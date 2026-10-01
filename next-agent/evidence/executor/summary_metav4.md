paired games: 100  opponents: ['agents/ours/h1-substrate-metav4/main.py']
| metric | skel | route | tape | Team A (replays) |
|---|---|---|---|---|
| ratio vs opponent | 0.601 ± 0.010 | 0.589 ± 0.012 | 0.538 ± 0.011 | - |
| paired ratio change vs skel | +0.000 ± 0.000 | -0.012 ± 0.014 | -0.063 ± 0.016 | - |
| d6_11 productive | 468.6 | 507.3 | 401.5 | 599.8 |
| d6_11 productive_excl_unneeded_water | 468.6 | 393.3 | 384.6 | 570.3 |
| d6_11 WATER | 186.3 | 234.4 | 134.2 | 210.5 |
| d6_11 HARVEST | 26.6 | 28.8 | 27.3 | 36.8 |
| d6_11 PLANT | 57.2 | 55.0 | 39.9 | 70.8 |
| d6_11 FEED | 61.0 | 49.0 | 55.5 | 75.9 |
| d6_11 CARE | 63.6 | 47.2 | 58.7 | 78.4 |
| d6_11 COLLECT_FERTILIZER | 54.8 | 51.2 | 54.0 | 80.7 |
| d6_11 FERTILIZE | 0.0 | 13.6 | 10.7 | 13.5 |
| d6_11 DIG | 0.2 | 2.8 | 0.0 | 0.1 |
| d6_11 BUILD | 9.3 | 11.8 | 12.2 | 16.5 |
| d6_11 PLACE_ANIMAL | 9.6 | 13.4 | 9.1 | 16.5 |
| d6_11 failed | 0.0 | 0.0 | 231.6 | 1.9 |
| d6_11 idle_share | 0.288 | 0.063 | 0.059 | 0.027 |
| d6_11 move_share | 0.35 | 0.523 | 0.441 | 0.473 |
| _d0_5 productive | 210.0 | 254.0 | 173.8 | 209.3 |
| _d0_5 productive_excl_unneeded_water | 210.0 | 191.1 | 173.8 | 209.3 |
| _d0_5 WATER | 76.9 | 113.9 | 54.8 | 71.8 |
| _d0_5 HARVEST | 10.0 | 13.0 | 7.0 | 10.0 |
| _d0_5 PLANT | 30.0 | 33.0 | 25.9 | 30.0 |
| _d0_5 FEED | 29.0 | 28.0 | 26.0 | 28.1 |
| _d0_5 CARE | 29.0 | 26.0 | 28.0 | 34.4 |
| _d0_5 COLLECT_FERTILIZER | 25.0 | 25.0 | 22.0 | 25.0 |
| _d0_5 FERTILIZE | 0.0 | 5.0 | 0.0 | 0.0 |
| _d0_5 DIG | 0.1 | 0.1 | 0.0 | 0.0 |
| _d0_5 BUILD | 5.0 | 5.0 | 5.0 | 5.0 |
| _d0_5 PLACE_ANIMAL | 5.0 | 5.0 | 5.0 | 5.0 |
| _d0_5 failed | 0.0 | 0.0 | 20.2 | 2.0 |
| _d0_5 idle_share | 0.47 | 0.21 | 0.312 | 0.293 |
| _d0_5 move_share | 0.257 | 0.447 | 0.379 | 0.408 |
| day 12 crops | 61.2 | 52.7 | 33.4 | 67.6 |
| day 12 animals | 14.7 | 15.8 | 12.1 | 20.8 |
| day 12 empty | 22.5 | 27.9 | 19.8 | 11.5 |
| day 12 weeds | 0.2 | 2.6 | 5.6 | 0.0 |
| day 12 empty_structures | 1.3 | 1.0 | 4.0 | 0.0 |
| day 12 quadrants | 4.0 | 4.0 | 3.0 | 4.0 |
| day 12 money | 4312.9 | 2009.7 | 1619.1 | 6354.7 |
| day 12 shed_value | 3913.7 | 2429.7 | 3687.8 | 4019.0 |
| day 12 animal COW | 7.4 | 8.0 | 2.2 | 7.8 |
| day 12 animal GOOSE | 4.3 | 4.8 | 2.0 | 8.5 |
| day 12 animal SHEEP | 3.0 | 3.0 | 7.9 | 4.5 |
| day 12 crop MELON | 2.0 | 2.0 | 0.1 | 0 |
| day 12 crop STRAWBERRY | 24.3 | 22.6 | 18.9 | 27.3 |
| day 12 crop TOMATO | 2.2 | 3.9 | 3.1 | 5.4 |
| day 12 crop WHEAT | 32.7 | 24.2 | 11.2 | 31.2 |
coverage d6-11 Team A (replays) {"games": 11, "animal_days": 97.0, "dying_unwatered": 9.2, "fertilizer_uncollected": 0.5, "overdue_unharvested": 0.1, "plant_days": 288.6, "uncared": 20.1, "unfed": 21.5}

route d6-11: {"per_game": {"visits_total": 388.0, "visits_served": 241.3, "visits_skipped_nothing": 69.8, "visits_arrived_nothing": 18.3, "visits_locked": 45.2, "visits_abandoned": 0.0, "visits_unreached": 13.5, "route_op": 471.3, "route_wait": 28.1, "route_move": 446.2, "fallback_op": 131.0, "fallback_move": 315.3, "fallback_idle": 63.7}, "nothing_to_do_share": 0.267, "arrived_for_nothing_share": 0.055, "locked_share": 0.116, "unreached_share": 0.035, "fallback_share_of_ops": 0.217, "nothing_to_do_by_kind": {}}
