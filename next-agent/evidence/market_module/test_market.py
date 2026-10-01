import copy
import unittest

import market


def observation(step=156, shed=None, shops=(), money=3000):
    farms = [{"tiles": [[None] * 10 for _ in range(10)], "money": money,
              "hands": [], "unlocked_quadrants": ["NW"]} for _ in range(2)]
    return {"player": 0, "step": step, "day": step // 24, "hour": step % 24,
            "farms": farms, "private": {"shed": shed or {}, "inventories": [{}]},
            "town": {"unlocked_shops": list(shops)},
            "market": {"inventory": dict.fromkeys(market.PRODUCTS, 10000),
                       "prices": {p: v["base"] for p, v in market.PARAMS.items()}}}


class MarketTests(unittest.TestCase):
    def setUp(self):
        market._STATE.clear()
        market.ENABLE_MODEL_LEAD = True
        market.ENABLE_EXPOSURE_ORDERING = True
        market.ENABLE_WHEAT_ROUND_TRIP = False
        market.ENABLE_PRICE_GATE_LEAD = True

    def test_prices_match_installed_engine(self):
        from kaggle_environments.envs.kaggriculture.kaggriculture import market_price
        for item in market.PRODUCTS:
            for inventory in (-100, 0, 9500, 9999, 10000, 10001, 10050, 10500, 20000):
                self.assertEqual(market.price(item, inventory), market_price(item, inventory))
        params = copy.deepcopy(market.PARAMS)
        params["MILK"].update(base=240, I0=9000, below_func="log10")
        self.assertEqual(market.price("MILK", 8980, params), market_price("MILK", 8980, params))

    def test_duplicate_shops_and_town_drain(self):
        shops = ["PIZZA_SHOP", "PIZZA_SHOP", "ICE_CREAM_SHOP", "YARN_STORE"]
        self.assertEqual(market.drain("MILK", 24, shops), 4)
        self.assertEqual(market.drain("WOOL", 4, shops), 2)
        self.assertEqual(market.drain("WOOL", 5, shops), 0)
        self.assertEqual(market.drain("FERTILIZER", 24, shops), 0)

    def test_model_lead_only_held_supported_goods(self):
        obs = observation(shed={"MILK": 12, "WHEAT": 10, "FERTILIZER": 10, "MELON": 10})
        self.assertEqual(market.market_orders(obs, []), [["SELL", "MILK", 10]])
        self.assertEqual(obs["private"]["shed"]["MILK"], 12)

    def test_model_windows_and_floor(self):
        for step in (143, 144, 167, 696, 718):
            self.assertEqual(market.market_orders(observation(step, {"MILK": 12}), []), [])
        obs = observation(shed={"MILK": 12})
        obs["market"]["prices"]["MILK"] = 1
        self.assertEqual(market.market_orders(obs, []), [])

    def test_final_f4_hour_window_and_hour1_tiers(self):
        self.assertEqual(market.market_orders(observation(146, {"MILK": 12}), []), [["SELL", "MILK", 10]])
        obs = observation(145, {"MILK": 2})
        obs["market"]["prices"]["MILK"] = 80
        obs["market"]["inventory"]["MILK"] = 10038
        self.assertEqual(market.market_orders(obs, []), [["SELL", "MILK", 2]])
        obs["market"]["prices"]["WOOL"] = 10
        self.assertEqual(market.market_orders(obs, []), [])
        obs["private"]["shed"]["MILK"] = 3
        self.assertEqual(market.market_orders(obs, []), [["SELL", "MILK", 3]])
        obs["market"]["prices"]["MILK"] = 49
        obs["market"]["inventory"]["MILK"] = 10053
        self.assertEqual(market.market_orders(obs, []), [])

    def test_real_demand_can_prevent_a_lead_sale(self):
        obs = observation(shed={"MILK": 12}, shops=["SMOOTHIE_SHOP"] * 8)
        self.assertEqual(market.market_orders(obs, []), [])

    def test_existing_sale_and_ten_slots_are_preserved(self):
        obs = observation(shed={"MILK": 12})
        orders = [["SELL", "MILK", 3]]
        self.assertEqual(market.market_orders(obs, orders), orders)
        full = [["HIRE"] for _ in range(10)]
        self.assertEqual(market.market_orders(obs, full), full)

    def test_own_supply_is_subtracted_from_flow(self):
        previous = observation(155, {"MILK": 4})
        market.market_orders(previous, [["SELL", "MILK", 4]])
        current = observation(156)
        current["market"]["inventory"]["MILK"] += 4
        market.market_orders(current, [])
        self.assertEqual(market._STATE[0]["history"]["MILK"], [0])

    def test_unknown_drop_fills_and_new_game_do_not_invent_rival_flow(self):
        market.market_orders(observation(155), [["SELL", "MILK", 8]])
        current = observation(156)
        current["market"]["inventory"]["MILK"] += 8
        market.market_orders(current, [])
        self.assertEqual(market._STATE[0]["history"]["MILK"], [])
        market.market_orders(observation(0), [])
        self.assertEqual(market._STATE[0]["history"]["MILK"], [])

    def test_floor_crossing_sales_do_not_get_supply_credit(self):
        obs = observation(155, {"MILK": 10})
        obs["market"]["inventory"]["MILK"] = 10072
        obs["market"]["prices"]["MILK"] = market.price("MILK", 10072)
        market.market_orders(obs, [["SELL", "MILK", 10]])
        self.assertIsNone(market._STATE[0]["own"]["MILK"])

    def test_price_gate_releases_melon_but_preserves_inputs(self):
        obs = observation(192, {"MELON": 10, "WHEAT": 20, "FERTILIZER": 20})
        obs["market"]["inventory"]["MELON"] = 9999
        obs["market"]["prices"].update(MELON=market.price("MELON", 9999), WHEAT=40, FERTILIZER=150)
        self.assertEqual(market.market_orders(obs, []), [["SELL", "MELON", 10]])
        obs["market"]["prices"]["MELON"] = 250
        self.assertEqual(market.market_orders(obs, []), [])
        obs["market"]["prices"]["MELON"] = 260
        obs["step"] = 696
        self.assertEqual(market.market_orders(obs, []), [])

    def test_price_gate_respects_current_orders_and_full_book(self):
        obs = observation(192, {"MELON": 10})
        obs["market"]["prices"]["MELON"] = 260
        self.assertEqual(market.market_orders(obs, [["SELL", "MELON", 2]]), [["SELL", "MELON", 2]])
        orders = [["HIRE"] for _ in range(10)]
        self.assertEqual(market.market_orders(obs, orders), orders)

    def test_ordering_preserves_barriers_quantities_and_inputs(self):
        obs = observation(100, {"WHEAT": 10, "MILK": 10, "MELON": 10})
        orders = [["SELL", "WHEAT", 10], ["SELL", "MILK", 10], ["HIRE"], ["SELL", "MELON", 10]]
        saved = copy.deepcopy((obs, orders))
        result = market.market_orders(obs, orders)
        self.assertEqual(result[:2], [["SELL", "MILK", 10], ["SELL", "WHEAT", 10]])
        self.assertEqual(result[2:], orders[2:])
        self.assertEqual((obs, orders), saved)
        wash = [["BUY_PRODUCT", "WHEAT", 5], ["SELL", "WHEAT", 3], ["SELL", "MILK", 10]]
        self.assertEqual(market.market_orders(obs, wash), wash)

    def test_duplicates_and_placeholders_keep_slots(self):
        obs = observation(100, {"MILK": 10})
        orders = [["SELL", "MILK", 2], ["SELL", "MILK", 3], [], ["SELL", "MILK", 0]]
        self.assertEqual(market.market_orders(obs, orders), orders)

    def test_opening_is_optional_and_funded(self):
        obs = observation(0)
        orders = [["BUY_PRODUCT", "WHEAT", 5], ["BUY_ANIMAL", "COW", 1]]
        self.assertEqual(market.market_orders(obs, orders), orders)
        market.ENABLE_WHEAT_ROUND_TRIP = True
        self.assertEqual(market.market_orders(obs, orders), [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 15], ["BUY_ANIMAL", "COW", 1]])
        poor = observation(0, money=700)
        self.assertEqual(market.market_orders(poor, orders), orders)
        later_buy = [["HIRE"], ["BUY_PRODUCT", "WHEAT", 5]]
        self.assertEqual(market.market_orders(obs, later_buy), later_buy)

    def test_validation_and_missing_market(self):
        for orders in ([['BAD']], [['SELL', 'MILK', -1]], [['SELL', 'MILK', True]], [['BUY_PRODUCT', 'MILK', 1]], [['HIRE', 2]], [['HIRE']] * 11):
            with self.assertRaises(ValueError):
                market.market_orders(observation(), orders)
        obs = observation()
        del obs["market"]
        self.assertEqual(market.market_orders(obs, [["HIRE"]]), [["HIRE"]])


if __name__ == "__main__":
    unittest.main()
