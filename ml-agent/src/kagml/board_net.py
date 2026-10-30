"""Whole-board network for our workers (WHOLE_BOARD_DESIGN.md).

Input per turn: tile tokens (100 x F), worker tokens (up to 13 x G, with a mask), one global token (H).
Every token type has its own encoder; all tokens go through one transformer whose attention is biased by the
Manhattan distance between tokens (tiles and workers have a position; the global token does not).
Output per worker, in engine order: a command (masked to the legal ones), a target tile (101 = 100 tiles + stay;
a training helper) and an amount (1-5) for shed pickups and placements. Each worker also sees the decisions of
the workers before it this turn through a small causal layer over "decision tokens" (worker + its command +
its target tile), so two workers do not chase the same job.
"""
from dataclasses import asdict, dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

BOARD = 10
STAY = 100           # target index meaning "no target / stay"
MAX_DIST = 18        # Manhattan distances 0..18 on a 10x10 board; one more bin for "no position"


@dataclass
class NetConfig:
    tile_feats: int
    unit_feats: int
    glob_feats: int
    n_commands: int
    d: int = 128
    heads: int = 4
    layers: int = 4
    ff: int = 256
    n_amounts: int = 5
    dropout: float = 0.0
    # categorical columns: (column, number of ids, offset added so ids start at 0); embedded, not scaled
    tile_cat: tuple = ((2, 10, 0), (3, 4, 0))
    unit_cat: tuple = ((18, 45, 1),)
    glob_cat: tuple = ()
    # market head (PLAN_HEADS_DESIGN.md): quantity class per order token, from the global token
    market: bool = False
    n_market_tokens: int = 28
    n_qty: int = 11


class Block(nn.Module):
    """Pre-norm transformer layer with an additive attention bias."""

    def __init__(self, d, heads, ff, dropout):
        super().__init__()
        self.heads, self.n1, self.n2 = heads, nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.out = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.ff = nn.Sequential(nn.Linear(d, ff), nn.GELU(), nn.Linear(ff, d))
        self.drop = dropout

    def forward(self, x, bias):
        b, s, d = x.shape
        q, k, v = self.qkv(self.n1(x)).view(b, s, 3, self.heads, d // self.heads).permute(2, 0, 3, 1, 4)
        a = F.scaled_dot_product_attention(q, k, v, attn_mask=bias, dropout_p=self.drop if self.training else 0.0)
        x = x + self.out(a.transpose(1, 2).reshape(b, s, d))
        return x + self.ff(self.n2(x))


class BoardNet(nn.Module):
    def __init__(self, cfg: NetConfig):
        super().__init__()
        self.cfg = cfg
        d = cfg.d
        self.tile_in = nn.Sequential(nn.Linear(cfg.tile_feats, d), nn.GELU(), nn.Linear(d, d))
        self.unit_in = nn.Sequential(nn.Linear(cfg.unit_feats, d), nn.GELU(), nn.Linear(d, d))
        self.glob_in = nn.Sequential(nn.Linear(cfg.glob_feats, d), nn.GELU(), nn.Linear(d, d))
        self.cat = nn.ModuleDict({f"{part}{col}": nn.Embedding(n, d) for part in ("tile", "unit", "glob")
                                  for col, n, _ in getattr(cfg, f"{part}_cat")})
        for part, n in (("tile", cfg.tile_feats), ("unit", cfg.unit_feats), ("glob", cfg.glob_feats)):
            self.register_buffer(f"{part}_mean", torch.zeros(n))       # set by the trainer from training data
            self.register_buffer(f"{part}_std", torch.ones(n))
        self.xy = nn.Embedding(BOARD * BOARD, d)                  # where a token is
        self.kind = nn.Embedding(3, d)                            # global / tile / worker
        self.dist_bias = nn.Embedding(MAX_DIST + 2, cfg.heads)    # attention bias by distance
        self.blocks = nn.ModuleList(Block(d, cfg.heads, cfg.ff, cfg.dropout) for _ in range(cfg.layers))
        self.norm = nn.LayerNorm(d)
        # decisions of earlier workers this turn
        self.cmd_emb = nn.Embedding(cfg.n_commands + 1, d)        # + "not decided yet"
        self.stay_tok = nn.Parameter(torch.zeros(d))
        self.dec = Block(d, cfg.heads, cfg.ff, cfg.dropout)
        # heads
        self.cmd_head = nn.Sequential(nn.Linear(2 * d, d), nn.GELU(), nn.Linear(d, cfg.n_commands))
        self.tgt_q, self.tgt_k = nn.Linear(2 * d, d), nn.Linear(d, d)
        self.amt_head = nn.Sequential(nn.Linear(2 * d, d), nn.GELU(), nn.Linear(d, cfg.n_amounts))
        if cfg.market:
            self.mkt_head = nn.Sequential(nn.Linear(d, 2 * d), nn.GELU(), nn.Linear(2 * d, cfg.n_market_tokens * cfg.n_qty))

    @staticmethod
    def _positions(unit_xy):
        """Cell index of every token: global = -1, tiles 0..99, workers from their (x, y)."""
        b, u = unit_xy.shape[:2]
        tiles = torch.arange(100, device=unit_xy.device).expand(b, 100)
        units = (unit_xy[..., 1].clamp(0, 9) * BOARD + unit_xy[..., 0].clamp(0, 9)).long()
        glob = torch.full((b, 1), -1, device=unit_xy.device, dtype=torch.long)
        return torch.cat([glob, tiles, units], 1)

    def _embed(self, part, x, enc):
        """Scale numeric columns (training mean/std, clipped), embed categorical ones, sum."""
        cats = getattr(self.cfg, f"{part}_cat")
        z = ((x - getattr(self, f"{part}_mean")) / getattr(self, f"{part}_std")).clamp(-8, 8)
        if cats:
            z = z.clone()
            z[..., [c for c, _, _ in cats]] = 0
        h = enc(z)
        for col, n, off in cats:
            h = h + self.cat[f"{part}{col}"]((x[..., col] + off).long().clamp(0, n - 1))
        return h

    def encode(self, tiles, units, unit_xy, unit_mask, glob):
        """Board representation: (tile tokens B x 100 x d, worker tokens B x U x d)."""
        b, u = units.shape[:2]
        pos = self._positions(unit_xy)
        x = torch.cat([self._embed("glob", glob, self.glob_in).unsqueeze(1), self._embed("tile", tiles, self.tile_in),
                       self._embed("unit", units, self.unit_in)], 1)
        kinds = torch.cat([torch.zeros(b, 1), torch.ones(b, 100), torch.full((b, u), 2)], 1).long().to(x.device)
        x = x + self.kind(kinds) + self.xy(pos.clamp(min=0)) * (pos >= 0).unsqueeze(-1)
        px, py = pos % BOARD, pos // BOARD
        dist = (px.unsqueeze(2) - px.unsqueeze(1)).abs() + (py.unsqueeze(2) - py.unsqueeze(1)).abs()
        nopos = (pos < 0).unsqueeze(2) | (pos < 0).unsqueeze(1)
        dist = torch.where(nopos, torch.full_like(dist, MAX_DIST + 1), dist.clamp(max=MAX_DIST))
        bias = self.dist_bias(dist).permute(0, 3, 1, 2)            # B x heads x S x S
        pad = torch.cat([torch.ones(b, 101, dtype=torch.bool, device=x.device), unit_mask.bool()], 1)
        bias = bias.masked_fill(~pad[:, None, None, :], float("-inf")).to(x.dtype)
        for blk in self.blocks:
            x = blk(x, bias)
        x = self.norm(x)
        self._glob_h = x[:, 0]                     # kept for the market head
        return x[:, 1:101], x[:, 101:]

    def decide(self, tile_h, unit_h, unit_mask, prev_cmd, prev_tgt):
        """Heads for every worker, given the earlier workers' decisions (prev_cmd/prev_tgt: B x U, with the
        decisions of workers 0..k-1 at positions 0..k-1; position k onwards ignored by the causal mask)."""
        b, u, d = unit_h.shape
        tgt_h = torch.cat([tile_h, self.stay_tok.expand(b, 1, d)], 1)                 # B x 101 x d
        dec = unit_h + self.cmd_emb(prev_cmd) + tgt_h.gather(1, prev_tgt.clamp(0, STAY).unsqueeze(-1).expand(b, u, d))
        # worker k may only look at decision tokens 0..k-1 (and needs at least one key: a zero "start" token)
        start = torch.zeros(b, 1, d, device=unit_h.device, dtype=unit_h.dtype)
        seq = torch.cat([start, dec[:, :-1]], 1)
        causal = torch.ones(u, u, dtype=torch.bool, device=unit_h.device).tril()
        bias = torch.zeros(b, self.cfg.heads, u, u, device=unit_h.device, dtype=unit_h.dtype).masked_fill(~causal, float("-inf"))
        ctx = self.dec(seq, bias)
        h = torch.cat([unit_h, ctx], -1)
        cmd = self.cmd_head(h)
        tgt = torch.einsum("bud,btd->but", self.tgt_q(h), self.tgt_k(tgt_h)) / d ** 0.5
        return cmd, tgt, self.amt_head(h)

    def market_logits(self):
        """Order quantity logits (B x tokens x classes) from the last encoded board."""
        b = self._glob_h.shape[0]
        return self.mkt_head(self._glob_h).view(b, self.cfg.n_market_tokens, self.cfg.n_qty)

    def forward(self, tiles, units, unit_xy, unit_mask, glob, prev_cmd, prev_tgt):
        tile_h, unit_h = self.encode(tiles, units, unit_xy, unit_mask, glob)
        out = self.decide(tile_h, unit_h, unit_mask, prev_cmd, prev_tgt)
        return out + (self.market_logits(),) if self.cfg.market else out

    @torch.no_grad()
    def act(self, tiles, units, unit_xy, unit_mask, glob, legal_fn, bias=None):
        """Decode one turn worker by worker. `legal_fn(k, commands_so_far, amounts_so_far)` returns worker k's
        legal mask (bool, n_commands) given the choices for workers 0..k-1. `bias` (n_commands) is added to the
        command logits (play-time logit adjustment). Returns (commands, targets, amounts) per worker."""
        tile_h, unit_h = self.encode(tiles, units, unit_xy, unit_mask, glob)
        u = unit_h.shape[1]
        none = self.cfg.n_commands
        prev_cmd = torch.full((1, u), none, dtype=torch.long, device=unit_h.device)
        prev_tgt = torch.full((1, u), STAY, dtype=torch.long, device=unit_h.device)
        cmds, tgts, amts = [], [], []
        for k in range(int(unit_mask.sum())):
            cmd, tgt, amt = self.decide(tile_h, unit_h, unit_mask, prev_cmd, prev_tgt)
            legal = legal_fn(k, cmds, amts)
            logits = (cmd[0, k].float() if bias is None else cmd[0, k].float() + bias).masked_fill(~torch.as_tensor(legal, device=cmd.device), float("-inf"))
            c, t, a = int(logits.argmax()), int(tgt[0, k].argmax()), int(amt[0, k].argmax()) + 1
            cmds.append(c), tgts.append(t), amts.append(a)
            prev_cmd[0, k], prev_tgt[0, k] = c, t
        return cmds, tgts, amts


def loss_fn(out, cmd_y, tgt_y, amt_y, legal, unit_mask, cmd_mask=None, amt_mask=None, w_tgt=0.5, w_amt=0.2):
    """Cross-entropy on legal commands (where cmd_mask), target tile (every present worker) and amount class 0-4
    (where amt_mask). Without the masks: commands on present workers, amounts where amt_y > 0 (1-5)."""
    cmd, tgt, amt = out[:3]
    live = unit_mask.bool()
    cm = live if cmd_mask is None else cmd_mask.bool() & live
    logits = cmd.float().masked_fill(~legal.bool(), -1e9)
    l_cmd = F.cross_entropy(logits[cm], cmd_y[cm].clamp(min=0))
    l_tgt = F.cross_entropy(tgt.float()[live], tgt_y[live].clamp(0, STAY))
    if amt_mask is None:
        has, cls = live & (amt_y > 0), amt_y - 1
    else:
        has, cls = amt_mask.bool() & live, amt_y
    l_amt = F.cross_entropy(amt.float()[has], cls[has].clamp(0, 4)) if has.any() else cmd.new_zeros(())
    return l_cmd + w_tgt * l_tgt + w_amt * l_amt, {"cmd": float(l_cmd.detach()), "tgt": float(l_tgt.detach()), "amt": float(l_amt.detach())}


def save(model, path):
    torch.save({"cfg": asdict(model.cfg), "state": model.state_dict()}, path)


def load(path, device="cpu", market=None):
    """Load a model; market=True adds a fresh market head to a model trained without one (for fine-tuning)."""
    ck = torch.load(path, map_location=device, weights_only=False)
    cfg = dict(ck["cfg"])
    if market is not None:
        cfg["market"] = market
    m = BoardNet(NetConfig(**cfg))
    m.load_state_dict(ck["state"], strict=not (market and not ck["cfg"].get("market")))
    return m.to(device).eval()


QTY_EDGES = (0, 1, 2, 3, 4, 5, 6, 8, 11, 16, 26)          # lower edge of each quantity class
QTY_PLAY = (0, 1, 2, 3, 4, 5, 6, 9, 13, 20, 30)           # quantity played for each class


def qty_class(units):
    """Quantities (tensor or array of ints) -> class index 0..10."""
    edges = torch.as_tensor(QTY_EDGES, device=units.device if torch.is_tensor(units) else None)
    u = torch.as_tensor(units)
    return (u.unsqueeze(-1) >= edges).sum(-1) - 1


def market_loss(logits, units, mask, nonzero_weight=4.0, token_weight=None):
    """Cross-entropy per order token on turns with a market label; non-zero quantities counted more, and each token
    times `token_weight[token]` when given (e.g. animals and land up-weighted)."""
    if not mask.any():
        return logits.new_zeros(())
    lg, y = logits[mask].float(), qty_class(units[mask]).clamp(0, logits.shape[-1] - 1)
    ce = F.cross_entropy(lg.reshape(-1, lg.shape[-1]), y.reshape(-1), reduction="none")
    w = torch.where(y.reshape(-1) > 0, nonzero_weight, 1.0)
    if token_weight is not None:
        w = w * token_weight.to(w.device).repeat(lg.shape[0])
    return (ce * w).sum() / w.sum()
