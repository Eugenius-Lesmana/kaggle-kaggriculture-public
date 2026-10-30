"""An agent whose workers are run by the whole-board network; the template keeps the plan and market orders.

Same contract as ModelPlayer (compare_day / run_full player names "net:<model dir>[:dA-B]"): every turn the
template is asked for its full action, then its worker commands are replaced by the network's, decided worker by
worker with the legal mask from `board_features.legal` given the earlier workers' choices. Outside the day window
(default 6-28) the template's own worker commands are kept.
"""
import copy
import json
from pathlib import Path
from collections import Counter

import torch

from kagml.board_net import load
from kagml.paths import models
from kagml.preview import TemplatePlayer


def step_toward(pos, target):
    """One step along x first, then y (the same walking as the job-ranker player)."""
    (x, y), (tx, ty) = pos, target
    if x != tx:
        return ["EAST"] if tx > x else ["WEST"]
    if y != ty:
        return ["SOUTH"] if ty > y else ["NORTH"]
    return ["PASS"]


class NetPlayer(TemplatePlayer):
    def __init__(self, spec="board-v1"):
        super().__init__()
        name, *opts = spec.split(":")
        window = next((o[1:] for o in opts if o.startswith("d") and "-" in o), "6-28")
        self.days = tuple(int(x) for x in window.split("-"))
        self.guard = "guard" in opts          # end-of-day guard: no animal escapes, no crop dies, if a worker can reach it
        self.feedguard = "feedguard" in opts  # structural guard (as the 4th-place agent): wheat on hand for animals at risk
        self.use_market = "market" in opts    # network's market orders replace the template's on network days
        self.shopsell = "shopsell" in opts    # strawberry, milk and wool sold only on the turn after the town shops buy
        self.herd_caps = json.loads((Path(__file__).resolve().parents[2] / 'reports/ANIMAL_MIX_TRAIN_CAPS.json').read_text())['caps'] if 'herdcap' in opts else None
        self.online_sell = 'onlinesell' in opts
        self.sell_state = None
        self.deferred = Counter()
        self.overflow = "overflow" in opts    # sell from the shed what would be discarded at night
        self.wheatcap = "wheatcap" in opts    # wheat feed bought only for unfed animals the stock cannot cover
        self.sortsell = "sortsell" in opts    # sells first in the order list, dearest first
        self.endwork = "endwork" in opts      # no planting, building or care that cannot pay off before the end
        tau = next((float(o[2:]) for o in opts if o.startswith("la")), 0.0)
        self.bias = self._logit_adjustment(tau) if tau else None
        self.endmask = "endmask" in opts  # no purchases that cannot pay back before the end (all days, day 29 too)
        self.end29 = "end29" in opts      # day 29: shop goods sold right after each town pull, stock split evenly
        self.guarding = {}                 # worker -> (job, cell) the guard sent it to
        torch.set_num_threads(1)
        self.net = load(models() / name / "model.pt", "cpu")
        # mcal: per-token bias on the market head's "no order" class, fitted on the analysis split so each token is
        # ordered as often as the teacher orders it (models/<name>/market-cal.json; Claude 2026-10-29)
        self.mcal = torch.tensor(json.loads((models() / name / "market-cal.json").read_text())["bias"]) if "mcal" in opts else None
        from kagml import board_features as bf          # Codex's encoder (package N)
        self.bf = bf
        self.history, self.prev_action = bf.History(), None
        self.market_policy = None
        market_options = [o.split('=', 1)[1] for o in opts if o.startswith('mkt=')]
        if market_options:
            if len(market_options) != 1 or self.mcal is not None:
                raise ValueError('use one mkt=<model>; do not combine it with board-head mcal')
            from kagml.market_net import MarketPolicy
            self.market_policy = MarketPolicy.load(market_options[0])
            self.use_market = True
        self.base_net, self.end_net, self.end_day = self.net, None, None
        switch = [o for o in opts if o.startswith('end') and '=' in o]
        if switch:
            if len(switch) != 1:
                raise ValueError('use one end<day>=<model> option')
            day, model = switch[0].split('=', 1)
            self.end_day = int(day[3:])
            if not 0 <= self.end_day <= 28 or not model or Path(model).name != model:
                raise ValueError('invalid endgame day/model')
            self.end_net = load(models() / model / 'model.pt', 'cpu')
            for key in ('tile_feats', 'unit_feats', 'glob_feats', 'n_commands'):
                if getattr(self.end_net.cfg, key) != getattr(self.base_net.cfg, key):
                    raise ValueError('incompatible endgame model features')
        # Only requested models are loaded/warmed. No option retains the original single-model path.
        for network in (self.base_net, self.end_net) if self.end_net is not None else (self.base_net,):
            c = network.cfg
            z = lambda *s: torch.zeros(1, *s)
            network.act(z(100, c.tile_feats), z(14, c.unit_feats), torch.zeros(1, 14, 2, dtype=torch.long),
                        torch.ones(1, 14, dtype=torch.bool), z(c.glob_feats),
                        lambda k, chosen, amts: torch.ones(c.n_commands, dtype=torch.bool))

    def _model_for_day(self, day):
        return self.end_net if self.end_net is not None and self.end_day <= day <= 28 else self.base_net

    @staticmethod
    def _logit_adjustment(tau, min_count=10):
        """Option la<tau>: subtract tau * log(teacher frequency) from each command's logit, so the argmax is less
        pulled toward frequent commands. Commands the teacher used fewer than `min_count` times get the smallest
        adjustment (no boost), and so do PASS (idling) and DIG (it also removes crops)."""
        from kagml.command_prior import COUNTS
        from kagml.board_features import COMMAND_ID
        c = torch.tensor(COUNTS, dtype=torch.float32)
        adj = -tau * torch.log(c.clamp(min=1) / c.sum())
        keep = c >= min_count
        keep[COMMAND_ID[("PASS",)]] = keep[COMMAND_ID[("DIG",)]] = False
        return torch.where(keep, adj, adj[keep].min())

    def memory(self):
        base = (super().memory(), copy.deepcopy(self.history))
        return base if self.market_policy is None else (*base, self.market_policy.memory(), copy.deepcopy(self.prev_action))

    def restore(self, memory):
        super().restore(memory[0] if isinstance(memory, tuple) else memory)
        self.history = copy.deepcopy(memory[1]) if isinstance(memory, tuple) else self.bf.History()
        self.prev_action, self.deferred = None, Counter()
        self.sell_state = None
        if self.market_policy is not None:
            if not isinstance(memory, tuple) or len(memory) != 4:
                raise ValueError('market model restore requires its causal history')
            self.market_policy.restore(memory[2])
            self.prev_action = copy.deepcopy(memory[3])

    def warm_step(self, observation, configuration=None, previous_action=None):
        self.module.agent(observation, configuration)
        self.history.observe(observation, observation["player"], None)
        if self.market_policy is not None:
            self.market_policy.history.observe(observation, observation['player'], previous_action)

    def _engine(self, c, amount):
        """Command id -> engine command; shed pickups and placements of goods get the network's amount."""
        return self.bf.decode(c, int(amount))

    # order tokens (reports/PLAN_MARKET_VOCAB.csv) in the order they are issued: sells, hires, seeds, products,
    # animals, land (a sale can finance a purchase; the engine processes at most 10 orders in list order)
    PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
    TOKENS = ([("SELL", p) for p in PRODUCTS] + [("BUY_SEED", c) for c in PRODUCTS[:5]]
              + [("BUY_ANIMAL", a) for a in ("GOOSE", "COW", "SHEEP")] + [("BUY_PRODUCT", p) for p in PRODUCTS]
              + [("BUY_LAND", None), ("HIRE", None)])
    ISSUE_ORDER = list(range(0, 9)) + [27] + list(range(9, 14)) + [17, 25] + list(range(14, 17)) + [26]

    def _herd_cap(self, obs, action):
        if self.herd_caps is None:
            return action
        farm, private = obs['farms'][obs['player']], obs['private']
        held = Counter(t.get('animal') for line in farm['tiles'] for t in line if isinstance(t, dict))
        for bag in [private['shed'], *private['inventories']]:
            held.update({a: bag.get(a, 0) for a in ('COW', 'SHEEP')})
        caps = self.herd_caps[str(obs['day'])]
        orders = []
        for order in action.get('market') or []:
            if len(order) >= 3 and order[0] == 'BUY_ANIMAL' and order[1] in ('COW', 'SHEEP'):
                animal = order[1]
                n = max(0, min(int(order[2]), int(caps[animal]) - held[animal]))
                held[animal] += n
                if n:
                    orders.append(['BUY_ANIMAL', animal, n])
            else:
                orders.append(order)
        action['market'] = orders
        return action

    ONLINE_FRACTION = 0.8
    ONLINE_ROOM = 70

    def _online_sell(self, obs, action):
        day, hour = int(obs['day']), int(obs['hour'])
        prices, shed = obs['market']['prices'], obs['private']['shed']
        if self.sell_state is None or self.sell_state['day'] != day:
            self.sell_state = dict(day=day, high={}, last={}, pending=Counter())
        state = self.sell_state
        orders = []
        requested = Counter()
        for order in action.get('market') or []:
            if len(order) >= 3 and order[0] == 'SELL' and order[1] in self.SHOP_GOODS:
                requested[order[1]] += max(0, int(order[2]))
            else:
                orders.append(order)
        sells = []
        for product in self.SHOP_GOODS:
            price = prices[product]
            high = max(price, state['high'].get(product, price))
            last = state['last'].get(product, price)
            # A rising price releases held goods immediately; no fixed wait synchronizing both sellers.
            hold = hour < 22 and sum(shed.values()) < self.ONLINE_ROOM and price < self.ONLINE_FRACTION * high and price <= last
            quantity = max(requested[product], state['pending'][product])
            if hold:
                state['pending'][product] = quantity
            else:
                n = min(quantity, max(0, int(shed.get(product, 0))))
                if n:
                    sells.append(['SELL', product, n])
                state['pending'][product] = max(0, quantity - n)
            state['high'][product], state['last'][product] = high, price
        action['market'] = sells + orders
        return action

    def _market_orders(self, n_units):
        """The network's orders for this turn, from the market head on the board just encoded. Hires are capped so
        workers stay within the encoder's farmer + 13 hands (the most the teacher ever had)."""
        from kagml.board_net import QTY_PLAY
        logits = (self.net.market_logits()[0].float() if self.market_policy is None
                  else self.market_policy.logits(self._market_global))
        if self.mcal is not None:
            logits[:, 0] += self.mcal
        q = logits.argmax(-1).tolist()
        orders = []
        for i in self.ISSUE_ORDER:
            n = QTY_PLAY[q[i]]
            if n <= 0:
                continue
            op, item = self.TOKENS[i]
            if op == "HIRE":
                orders += [["HIRE"]] * max(0, min(n, self.bf.MAX_UNITS - n_units))
            elif op == "BUY_LAND":
                orders.append(["BUY_LAND"])
            else:
                orders.append([op, item, int(n)])
        return orders[:10]

    SHOP_GOODS = ("STRAWBERRY", "MILK", "WOOL")
    SHOP_HOLD_CAP = 80                         # shed is 100 units; above this, sell now to leave room for produce

    def _shop_sell(self, obs, action):
        """The town shops buy every 4th step (engine `_town_consume`, after the market), so prices are highest on
        steps with step % 4 == 1. Sells of shop goods on other steps are held back and added to the next such step,
        unless the shed is nearly full."""
        shed = obs["private"]["shed"]
        market = list(action.get("market") or [])
        shop_turn = (obs["day"] * 24 + obs["hour"]) % 4 == 1
        if not shop_turn and sum(shed.values()) < self.SHOP_HOLD_CAP:
            for o in market:
                if o[0] == "SELL" and o[1] in self.SHOP_GOODS:
                    self.deferred[o[1]] += int(o[2])
            action["market"] = [o for o in market if not (o[0] == "SELL" and o[1] in self.SHOP_GOODS)]
            return action
        if shop_turn:
            for p in self.SHOP_GOODS:
                n = min(shed.get(p, 0), self.deferred.pop(p, 0))
                o = next((o for o in market if o[0] == "SELL" and o[1] == p), None)
                if o:
                    o[2] = max(int(o[2]), n)
                elif n > 0:
                    market.insert(0, ["SELL", p, n])
            action["market"] = market[:10]
        return action

    INPUTS = ("WHEAT", "FERTILIZER")           # sold for overflow only after the produce

    def _overflow_sell(self, obs, action, n_units):
        """At night the engine drops every bag into the shed (100 units) and discards what does not fit. On the
        last turn of the day, sell from the shed what would not fit (one extra unit per worker for this turn's
        harvests), dearest produce first; the market runs after the workers act, before the night."""
        if obs["hour"] != 23:
            return action
        private, prices = obs["private"], obs["market"]["prices"]
        shed = private["shed"]
        excess = sum(shed.values()) + sum(sum(b.values()) for b in private["inventories"]) + n_units - 100
        market = list(action.get("market") or [])
        selling = {o[1]: o for o in market if o[0] == "SELL"}
        order = sorted((p for p in shed if p not in self.INPUTS), key=lambda p: -prices.get(p, 0)) + list(self.INPUTS)
        for p in order:
            if excess <= 0:
                break
            o = selling.get(p)
            n = min(excess, shed.get(p, 0) - (int(o[2]) if o else 0))
            if n <= 0:
                continue
            if o:
                o[2] = int(o[2]) + n
            elif len(market) < 10:
                market.insert(0, ["SELL", p, n])
            else:
                continue
            excess -= n
        action["market"] = market
        return action

    def _wheat_cap(self, obs, action):
        """Buy wheat feed only for animals not yet fed today that the wheat in the shed and bags cannot cover
        (as the teacher does)."""
        farm, private = obs["farms"][obs["player"]], obs["private"]
        unfed = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("animal")
                    and not t.get("fed_today"))
        unfed += sum(int(o[2]) for o in action.get("market") or [] if o and o[0] == "BUY_ANIMAL")   # bought this turn
        room = max(0, unfed - private["shed"].get("WHEAT", 0) - sum(b.get("WHEAT", 0) for b in private["inventories"]))
        market = []
        for o in action.get("market") or []:
            if o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                n = min(int(o[2]), room)
                room -= n
                if n <= 0:
                    continue
                o = ["BUY_PRODUCT", "WHEAT", n]
            market.append(o)
        action["market"] = market
        return action

    def _sort_sells(self, obs, action):
        """The engine matches both players' orders by list position and moves the price per unit, so a good sold
        earlier in the list gets the price before the opponent's later orders lower it. Sells go first, dearest
        first; other orders keep their order."""
        prices, market = obs["market"]["prices"], list(action.get("market") or [])
        sells = sorted((o for o in market if o and o[0] == "SELL"), key=lambda o: -prices.get(o[1], 0))
        action["market"] = sells + [o for o in market if not (o and o[0] == "SELL")]
        return action

    ANIMAL_YIELD = {"GOOSE": (4, 1), "COW": (8, 2), "SHEEP": (6, 3)}   # engine ANIMALS: first_yield_day, interval

    def _legal(self, obs, seat, unit, earlier):
        """The encoder's legal mask; with `endwork`, also no work that cannot pay off before the end: planting a
        crop that cannot ripen by day 29, building a coop or pasture after day 19 (no animals are bought), and
        care when no production night is left (the care bonus is paid on the next production night after the
        care day, and the last night that counts is day 28's)."""
        bf = self.bf
        mask = bf.legal(obs, seat, unit, earlier)
        if not self.endwork:
            return mask
        day = int(obs["day"])
        for c, fy in self.FIRST_YIELD.items():
            if day + fy > self.LAST_DAY:
                mask[bf.COMMAND_ID[("PLANT", c)]] = False
        if day > self.LAST_ANIMAL_DAY:
            mask[bf.COMMAND_ID[("BUILD_COOP",)]] = mask[bf.COMMAND_ID[("BUILD_PASTURE",)]] = False
        care = bf.COMMAND_ID[("CARE",)]
        if mask[care] and day >= 20:
            farm, _ = bf.after_earlier(obs, seat, unit, earlier)
            x, y = bf.K._farmer_position(farm, unit)
            tile = farm["tiles"][y][x]
            fy, every = self.ANIMAL_YIELD[tile["animal"]]
            mask[care] = any((n + 1 - tile["placed_day"] - fy) >= 0 and (n + 1 - tile["placed_day"] - fy) % every == 0
                             for n in range(day + 1, self.LAST_DAY))
        return mask

    LAST_DAY = 29
    FIRST_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}   # engine CROPS
    LAST_ANIMAL_DAY = 19                       # the teacher buys no animals after day 18

    def _end_mask(self, obs, action):
        """Drop purchases that cannot pay back before the game ends: seeds whose crop cannot ripen by day 29,
        animals after day 19, and wheat feed on day 29 (fed animals produce the next day)."""
        day = obs["day"]

        def keep(o):
            if o[0] == "BUY_SEED":
                return day + self.FIRST_YIELD.get(o[1], 99) <= self.LAST_DAY
            if o[0] == "BUY_ANIMAL":
                return day <= self.LAST_ANIMAL_DAY
            if o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                return day < self.LAST_DAY
            return True
        action["market"] = [o for o in action.get("market") or [] if o and keep(o)]
        return action

    END29_SLOTS = (1, 5, 9, 13, 17, 21)       # day-29 hours right after a town pull (engine pulls after the market at step % 4 == 0)
    END29_LAST = 22                            # last hour whose market orders the engine processes
    END29_ROOM = 80                            # shed fuller than this: keep the template's sells so deliveries fit

    def _end29_sell(self, obs, action):
        """Day 29 (Claude, 2026-10-30, reports/2026-10-30-sell-split.md): the template sells whatever reaches the shed
        and dumps everything at step 700, the turn before a pull. For goods an open shop buys, sell only on the turn
        right after each pull, splitting the shed stock evenly over the pulls left, and the rest on the last turn.
        Goods no open shop buys keep the template's orders: their price only falls during the day."""
        hour, shed = int(obs["hour"]), obs["private"]["shed"]
        demand = self.module.SHOP_DEMAND
        pulled = {p for shop in obs["town"]["unlocked_shops"] for p in demand.get(shop, {})}
        market = list(action.get("market") or [])
        if sum(shed.values()) > self.END29_ROOM:
            return action
        keep = [o for o in market if not (o and o[0] == "SELL" and o[1] in pulled)]
        # workers act before the market, so the template also sells what they drop in the shed this turn
        stock = Counter({p: int(shed.get(p, 0)) for p in pulled})
        for o in market:
            if o and o[0] == "SELL" and o[1] in pulled:
                stock[o[1]] = max(stock[o[1]], int(o[2]))
        left = sum(1 for h in self.END29_SLOTS if h >= hour)
        sells = []
        if hour in self.END29_SLOTS or hour >= self.END29_LAST:
            for p in sorted(pulled, key=lambda p: -obs["market"]["prices"].get(p, 0)):
                n = stock[p] if hour >= self.END29_LAST else -(-stock[p] // max(1, left))
                if n > 0:
                    sells.append(["SELL", p, n])
        action["market"] = (sells + keep)[:10]
        return action

    FEED_GUARD_HOUR = 18

    def _feed_guard(self, obs, seat, action):
        """Market-side feed guard: an animal unfed since yesterday escapes tonight, and after hour 18 any unfed animal
        is at risk. If those animals outnumber the wheat in the shed and bags, buy the shortfall (added to the
        template's orders; the workers do the feeding)."""
        farm, private = obs["farms"][seat], obs["private"]
        late = obs["hour"] >= self.FEED_GUARD_HOUR
        at_risk = sum(1 for row in farm["tiles"] for t in row if isinstance(t, dict) and t.get("animal")
                      and not t.get("fed_today") and (late or t.get("consecutive_unfed", 0) >= 1))
        have = private["shed"].get("WHEAT", 0) + sum(b.get("WHEAT", 0) for b in private["inventories"])
        market = list(action.get("market") or [])
        bought = sum(int(o[2]) for o in market if o and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" and len(o) > 2)
        short = at_risk - have - bought
        if short > 0 and len(market) < 10:                  # the engine takes at most 10 market orders a turn
            market.append(["BUY_PRODUCT", "WHEAT", int(short)])
            action["market"] = market
        return action

    def _apply_guard(self, obs, seat, commands):
        """The Guard role (PLAN.md): an animal unfed for a second day escapes tonight and a crop dry for a second
        day dies tonight. If no worker serves such a tile this turn and the day is running out (turns left <= the
        nearest free worker's trip + 2), that worker is sent there (fetching wheat first for feeding)."""
        from kagml.work_features import SHED_TILES, dist
        farm, private = obs["farms"][seat], obs["private"]
        pos = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
        left = 24 - obs["hour"]
        at_risk = []
        for y, row in enumerate(farm["tiles"]):
            for x, t in enumerate(row):
                if not isinstance(t, dict):
                    continue
                if t.get("animal") and not t.get("fed_today") and t.get("consecutive_unfed", 0) >= 1:
                    at_risk.append(("FEED", (x, y)))
                elif t.get("kind") == "PLANT" and not t.get("watered_today") and t.get("consecutive_unwatered", 0) >= 1:
                    at_risk.append(("WATER", (x, y)))
        if obs["hour"] == 0:
            self.guarding = {}
        self.guarding = {u: job for u, job in self.guarding.items() if job in at_risk and u < len(pos)}
        served = {(c[0], pos[u]) for u, c in enumerate(commands) if c and u < len(pos)}
        bag = lambda u: private["inventories"][u] if u < len(private["inventories"]) else {}

        def trip(u, job):
            kind, cell = job
            if kind == "FEED" and bag(u).get("WHEAT", 0) == 0:
                return min(dist(pos[u], s) + dist(s, cell) for s in SHED_TILES) + 2
            return dist(pos[u], cell) + 1

        for job in at_risk:
            if job in served or job in self.guarding.values():
                continue
            free = [u for u in range(len(pos)) if u not in self.guarding]
            if not free:
                break
            u = min(free, key=lambda w: trip(w, job))
            if left <= trip(u, job) + 2:
                self.guarding[u] = job
        for u, (kind, cell) in self.guarding.items():
            if kind == "FEED" and bag(u).get("WHEAT", 0) == 0:
                shed = min(SHED_TILES, key=lambda s: dist(pos[u], s))
                commands[u] = step_toward(pos[u], shed) if pos[u] != shed else ["PICKUP", "WHEAT", max(1, min(3, private["shed"].get("WHEAT", 0)))]
            else:
                commands[u] = step_toward(pos[u], cell) if pos[u] != cell else [kind]
        return commands

    def __call__(self, observation, configuration=None):
        obs, seat = observation, observation["player"]
        self.net = self._model_for_day(int(obs["day"]))
        action = dict(self.module.agent(obs, configuration))
        self.history.observe(obs, seat, self.prev_action)
        if self.market_policy is not None:
            self.market_policy.history.observe(obs, seat, self.prev_action)
        if not self.days[0] <= obs["day"] <= self.days[1]:
            if self.herd_caps is not None:
                action = self._herd_cap(obs, action)
            if self.endmask:
                action = self._end_mask(obs, action)
            if self.end29 and obs["day"] == self.LAST_DAY:
                action = self._end29_sell(obs, action)
            self.prev_action = action
            return action
        x = self.bf.encode(obs, seat, self.history)
        if self.market_policy is not None:
            self._market_global = x['glob']
        t = lambda k, dt=torch.float32: torch.as_tensor(x[k]).unsqueeze(0).to(dt)
        xy = torch.as_tensor(x["units"][..., :2]).unsqueeze(0).long()      # worker x, y are the first unit columns
        cmds, _, amounts = self.net.act(t("tiles"), t("units"), xy, t("unit_mask", torch.bool),
                                        t("glob"), lambda k, chosen, amts: torch.as_tensor(self._legal(
                                            obs, seat, k, [self._engine(c, amts[j]) for j, c in enumerate(chosen)])),
                                        self.bias)
        commands = [self._engine(c, amounts[k]) for k, c in enumerate(cmds)]
        n = len(obs["farms"][seat]["hands"]) + 1
        commands += [["PASS"]] * (n - len(commands))
        if self.use_market and (self.net.cfg.market or self.market_policy is not None):
            action["market"] = self._market_orders(n)
        if self.shopsell:
            action = self._shop_sell(obs, action)
        if self.online_sell:
            action = self._online_sell(obs, action)
        if self.overflow:
            action = self._overflow_sell(obs, action, n)
        if self.guard:
            commands = self._apply_guard(obs, seat, commands)
        if self.feedguard:
            action = self._feed_guard(obs, seat, action)
        if self.wheatcap:
            action = self._wheat_cap(obs, action)
        if self.sortsell:
            action = self._sort_sells(obs, action)
        if self.herd_caps is not None:
            action = self._herd_cap(obs, action)
        if self.endmask:
            action = self._end_mask(obs, action)
        action["farmer"], action["hands"] = commands[0], commands[1:n]
        self.prev_action = action
        return action
