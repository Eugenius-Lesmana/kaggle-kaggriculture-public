# Whole-board encoder and turn tensor contract (package N)

`src/kagml/board_features.py` is shared between dataset construction and play. Fixed engine:
kaggle-environments 1.32.7, 10x10 board, 24 turns/day, 30 days, shed capacity 100.
No normalization: numerical feature tensors are float32; categorical ids are numeric columns.
Do not treat categorical ids as ordered quantities. Model code owns embeddings/scaling.
All unavailable/inapplicable tile fields are 0 except next_production=-1 and rot_in=999.
Worker padding is all zero and must be removed with unit_mask.

## Runtime API and history

```python
from kagml.board_features import History, encode, legal, COMMANDS
history = History()  # optionally History(warmed_work_features_history)
# Each consecutive pre-action observation, including any unlabelled L3 prefix:
history.observe(obs, seat, previous_action)
features = encode(obs, seat, history)
mask = legal(obs, seat, unit, earlier_commands)
```

Observe once before encode, in physical day/hour order. previous_action is the action actually issued on the
previous turn. At dawn reset last-job and direction memory; prices remain warm. The dataset uses the unchanged
build_ownfarm_dataset.warm_history on parent el3 before the segment, then observes the complete segment prefix.
Input features contain only own private state and public observations/history; opponent private state and
future labels never enter inputs. History simulates previous own worker commands to detect effective jobs;
market/hiring/overnight results are read from the next actual observation. Preserve engine dictionary insertion
order: reconstruct the entire segment from morning rather than reinitialize from JSON each turn, because sorted
bag keys can alter overflow. Encoder timing excludes observe and legality; handoff reports that scope explicitly.

14 slots (farmer + 13 hands) are user-approved: real data exceeds the design's original 13. More than 14 raises.
Arrays use row-major tile index y*10+x, x=column and y=row. Target 100 means no effective job remains that day.
A current effective job is its own target; target/helper labels and diagnostic future values are training-only.

## Sequential legal masks

legal requires exactly unit earlier commands, applies them to a private deep copy with native unit rules, then
returns 44 booleans. Use actual amounts for earlier PICKUP/PLACE commands. For decoding in engine order, the
faster equivalent is after_earlier once or maintain a copied farm/private and use mask_for_state/apply per slot.
Units move/act before market orders; newly hired hands first act next turn. Earlier commands can consume seeds,
fill/drain shed, clear/plant/water a tile, or place an animal. LOCKED tiles are walkable and shed operations at
center positions resolve before the locked-land guard. Animal placement takes one regardless of amount.
For PICKUP and shed PLACE, a legal token assumes a positive amount (the model head supplies 1..5); zero/negative
amounts must never be decoded. DROP can legally discard overflow or remove zero bag keys.
PASS is the single explicit exception to effect-based legality: valid intentional stay, with took_effect=False.
All other legal tokens change native state. Illegal issued teacher commands remain recorded, mask=False and
command_loss_mask=False. Do not assert all issued commands legal without applying that loss mask.

## Feature columns

### tiles: 31 columns

| Index | Column | Meaning |
|---:|---|---|
| 0 | `x` | Column 0..9. |
| 1 | `y` | Row 0..9. |
| 2 | `kind` | TILE_KINDS categorical id (mapping below). |
| 3 | `animal` | 0 absent; GOOSE=1, COW=2, SHEEP=3. |
| 4 | `owned` | 1 unless LOCKED; the shed is not a tile. |
| 5 | `age` | Current day minus planted_day / placed_day; otherwise 0. |
| 6 | `next_production` | Same t_next_prod definition as work_features: pre-first yield remaining days; mature one-time crop 0; ongoing crop age phase modulo interval; animal 0 when scheduled tonight, otherwise days to scheduled night; absent -1. |
| 7 | `held` | yield_units waiting on this tile. |
| 8 | `max_held` | Crop max_yield or animal max_held. |
| 9 | `held_fraction` | held / max_held; absent 0. |
| 10 | `watered` | Plant watered_today. |
| 11 | `dry_days` | Plant consecutive_unwatered. |
| 12 | `fertilizer_days` | Plant max(0, fertilized_until_day-day+1), inclusive active days. |
| 13 | `fed` | Animal fed_today. |
| 14 | `cared` | Animal cared_today. |
| 15 | `unfed_days` | Animal consecutive_unfed. |
| 16 | `care_bonus` | Animal pending_care_bonus. |
| 17 | `fertilizer_available` | Animal fertilizer_available. |
| 18 | `rot_in` | Plant max_lifespan_step minus current absolute step, or 999 absent/unset. |
| 19 | `ongoing` | Crop ongoing flag. |
| 20 | `first_yield_day` | Crop/animal first_yield_day from engine constants. |
| 21 | `production_interval` | Crop/animal interval from engine constants. |
| 22 | `n_dies_tonight` | Plant is unwatered and already has >=1 consecutive_unwatered. |
| 23 | `n_prod_tonight` | Potential scheduled production under work_features formula; independent of death/escape/feed flags. |
| 24 | `n_double_tonight` | Ongoing scheduled crop production and fertilized_until_day >= day; potential double conditional on watering. |
| 25 | `n_escapes_tonight` | Animal unfed and consecutive_unfed >=1. |
| 26 | `n_full` | Animal held >= max_held. |
| 27 | `n_loss_if_dry` | Same work_features dollar estimate: dying crop held*price + seed + (max_yield-held)*price; otherwise dry scheduled ongoing production price*(2 if fertilized else 1). |
| 28 | `n_loss_if_unfed` | Same work_features dollar estimate: escaping animal cost+held*price; otherwise unfed scheduled production price*(1+care_bonus). |
| 29 | `seed_cost` | Crop seed cost. |
| 30 | `animal_cost` | Animal purchase cost. |

### units: 19 columns

| Index | Column | Meaning |
|---:|---|---|
| 0 | `x` | Current worker column. |
| 1 | `y` | Current worker row. |
| 2 | `is_farmer` | 1 for slot 0, else 0. |
| 3 | `bag_wheat` | Own bag count of WHEAT. |
| 4 | `bag_carrot` | Own bag count of CARROT. |
| 5 | `bag_tomato` | Own bag count of TOMATO. |
| 6 | `bag_strawberry` | Own bag count of STRAWBERRY. |
| 7 | `bag_melon` | Own bag count of MELON. |
| 8 | `bag_egg` | Own bag count of EGG. |
| 9 | `bag_milk` | Own bag count of MILK. |
| 10 | `bag_wool` | Own bag count of WOOL. |
| 11 | `bag_fertilizer` | Own bag count of FERTILIZER. |
| 12 | `bag_goose` | Own bag count of GOOSE. |
| 13 | `bag_cow` | Own bag count of COW. |
| 14 | `bag_sheep` | Own bag count of SHEEP. |
| 15 | `last_move_dx` | Last effective cardinal move x delta today, else 0. |
| 16 | `last_move_dy` | Last effective cardinal move y delta today, else 0. |
| 17 | `since_last_job` | Turns since last effective non-move/non-PASS job today; 999 if none. |
| 18 | `last_job_command` | Command vocabulary id of that job; -1 if none. |

### glob: 121 columns

| Index | Column | Meaning |
|---:|---|---|
| 0 | `day` | Zero-based day. |
| 1 | `hour` | Zero-based hour. |
| 2 | `turns_left_game` | 719 - absolute physical step; terminal frame has no action. |
| 3 | `turns_left_day` | 24-hour; includes current action, except final game truncation. |
| 4 | `days_left` | 29-day. |
| 5 | `cash` | Own bank. |
| 6 | `opp_cash` | Public opponent bank. |
| 7 | `cash_gap` | Own minus opponent bank. |
| 8 | `hires_today` | Own hires_today counter. |
| 9 | `land_count` | Number of owned quadrants. |
| 10 | `hands` | Number of currently active hands. |
| 11 | `shed_total` | Sum of all own shed counts. |
| 12 | `land_nw` | Owned quadrant flag: NW. |
| 13 | `land_ne` | Owned quadrant flag: NE. |
| 14 | `land_sw` | Owned quadrant flag: SW. |
| 15 | `land_se` | Owned quadrant flag: SE. |
| 16 | `shed_wheat` | Own shed item count: WHEAT. |
| 17 | `shed_carrot` | Own shed item count: CARROT. |
| 18 | `shed_tomato` | Own shed item count: TOMATO. |
| 19 | `shed_strawberry` | Own shed item count: STRAWBERRY. |
| 20 | `shed_melon` | Own shed item count: MELON. |
| 21 | `shed_egg` | Own shed item count: EGG. |
| 22 | `shed_milk` | Own shed item count: MILK. |
| 23 | `shed_wool` | Own shed item count: WOOL. |
| 24 | `shed_fertilizer` | Own shed item count: FERTILIZER. |
| 25 | `shed_goose` | Own shed item count: GOOSE. |
| 26 | `shed_cow` | Own shed item count: COW. |
| 27 | `shed_sheep` | Own shed item count: SHEEP. |
| 28 | `seeds_wheat` | Own seed count: WHEAT. |
| 29 | `seeds_carrot` | Own seed count: CARROT. |
| 30 | `seeds_tomato` | Own seed count: TOMATO. |
| 31 | `seeds_strawberry` | Own seed count: STRAWBERRY. |
| 32 | `seeds_melon` | Own seed count: MELON. |
| 33 | `wheat_price` | WHEAT: Current integer sale quote. |
| 34 | `wheat_market_stock` | WHEAT: Current shared market inventory. |
| 35 | `wheat_price_dawn` | WHEAT: First pre-action quote of this day. |
| 36 | `wheat_price_high_today` | WHEAT: Maximum observed quote this day through current turn. |
| 37 | `wheat_price_low_today` | WHEAT: Minimum observed quote this day through current turn. |
| 38 | `wheat_price_change_4h` | WHEAT: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 39 | `wheat_relative_price` | WHEAT: Current quote / engine MARKET_PARAMS base. |
| 40 | `wheat_daily_demand` | WHEAT: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 41 | `carrot_price` | CARROT: Current integer sale quote. |
| 42 | `carrot_market_stock` | CARROT: Current shared market inventory. |
| 43 | `carrot_price_dawn` | CARROT: First pre-action quote of this day. |
| 44 | `carrot_price_high_today` | CARROT: Maximum observed quote this day through current turn. |
| 45 | `carrot_price_low_today` | CARROT: Minimum observed quote this day through current turn. |
| 46 | `carrot_price_change_4h` | CARROT: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 47 | `carrot_relative_price` | CARROT: Current quote / engine MARKET_PARAMS base. |
| 48 | `carrot_daily_demand` | CARROT: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 49 | `tomato_price` | TOMATO: Current integer sale quote. |
| 50 | `tomato_market_stock` | TOMATO: Current shared market inventory. |
| 51 | `tomato_price_dawn` | TOMATO: First pre-action quote of this day. |
| 52 | `tomato_price_high_today` | TOMATO: Maximum observed quote this day through current turn. |
| 53 | `tomato_price_low_today` | TOMATO: Minimum observed quote this day through current turn. |
| 54 | `tomato_price_change_4h` | TOMATO: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 55 | `tomato_relative_price` | TOMATO: Current quote / engine MARKET_PARAMS base. |
| 56 | `tomato_daily_demand` | TOMATO: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 57 | `strawberry_price` | STRAWBERRY: Current integer sale quote. |
| 58 | `strawberry_market_stock` | STRAWBERRY: Current shared market inventory. |
| 59 | `strawberry_price_dawn` | STRAWBERRY: First pre-action quote of this day. |
| 60 | `strawberry_price_high_today` | STRAWBERRY: Maximum observed quote this day through current turn. |
| 61 | `strawberry_price_low_today` | STRAWBERRY: Minimum observed quote this day through current turn. |
| 62 | `strawberry_price_change_4h` | STRAWBERRY: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 63 | `strawberry_relative_price` | STRAWBERRY: Current quote / engine MARKET_PARAMS base. |
| 64 | `strawberry_daily_demand` | STRAWBERRY: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 65 | `melon_price` | MELON: Current integer sale quote. |
| 66 | `melon_market_stock` | MELON: Current shared market inventory. |
| 67 | `melon_price_dawn` | MELON: First pre-action quote of this day. |
| 68 | `melon_price_high_today` | MELON: Maximum observed quote this day through current turn. |
| 69 | `melon_price_low_today` | MELON: Minimum observed quote this day through current turn. |
| 70 | `melon_price_change_4h` | MELON: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 71 | `melon_relative_price` | MELON: Current quote / engine MARKET_PARAMS base. |
| 72 | `melon_daily_demand` | MELON: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 73 | `egg_price` | EGG: Current integer sale quote. |
| 74 | `egg_market_stock` | EGG: Current shared market inventory. |
| 75 | `egg_price_dawn` | EGG: First pre-action quote of this day. |
| 76 | `egg_price_high_today` | EGG: Maximum observed quote this day through current turn. |
| 77 | `egg_price_low_today` | EGG: Minimum observed quote this day through current turn. |
| 78 | `egg_price_change_4h` | EGG: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 79 | `egg_relative_price` | EGG: Current quote / engine MARKET_PARAMS base. |
| 80 | `egg_daily_demand` | EGG: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 81 | `milk_price` | MILK: Current integer sale quote. |
| 82 | `milk_market_stock` | MILK: Current shared market inventory. |
| 83 | `milk_price_dawn` | MILK: First pre-action quote of this day. |
| 84 | `milk_price_high_today` | MILK: Maximum observed quote this day through current turn. |
| 85 | `milk_price_low_today` | MILK: Minimum observed quote this day through current turn. |
| 86 | `milk_price_change_4h` | MILK: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 87 | `milk_relative_price` | MILK: Current quote / engine MARKET_PARAMS base. |
| 88 | `milk_daily_demand` | MILK: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 89 | `wool_price` | WOOL: Current integer sale quote. |
| 90 | `wool_market_stock` | WOOL: Current shared market inventory. |
| 91 | `wool_price_dawn` | WOOL: First pre-action quote of this day. |
| 92 | `wool_price_high_today` | WOOL: Maximum observed quote this day through current turn. |
| 93 | `wool_price_low_today` | WOOL: Minimum observed quote this day through current turn. |
| 94 | `wool_price_change_4h` | WOOL: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 95 | `wool_relative_price` | WOOL: Current quote / engine MARKET_PARAMS base. |
| 96 | `wool_daily_demand` | WOOL: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 97 | `fertilizer_price` | FERTILIZER: Current integer sale quote. |
| 98 | `fertilizer_market_stock` | FERTILIZER: Current shared market inventory. |
| 99 | `fertilizer_price_dawn` | FERTILIZER: First pre-action quote of this day. |
| 100 | `fertilizer_price_high_today` | FERTILIZER: Maximum observed quote this day through current turn. |
| 101 | `fertilizer_price_low_today` | FERTILIZER: Minimum observed quote this day through current turn. |
| 102 | `fertilizer_price_change_4h` | FERTILIZER: Current quote minus quote four observations earlier; 0 if fewer than five observations. |
| 103 | `fertilizer_relative_price` | FERTILIZER: Current quote / engine MARKET_PARAMS base. |
| 104 | `fertilizer_daily_demand` | FERTILIZER: Expected daily town consumption from current unlocked shops (work_features.daily_demand). |
| 105 | `opp_crop_wheat` | Public opponent count of crop tiles: WHEAT. |
| 106 | `opp_crop_carrot` | Public opponent count of crop tiles: CARROT. |
| 107 | `opp_crop_tomato` | Public opponent count of crop tiles: TOMATO. |
| 108 | `opp_crop_strawberry` | Public opponent count of crop tiles: STRAWBERRY. |
| 109 | `opp_crop_melon` | Public opponent count of crop tiles: MELON. |
| 110 | `opp_animal_goose` | Public opponent count of animals: GOOSE. |
| 111 | `opp_animal_cow` | Public opponent count of animals: COW. |
| 112 | `opp_animal_sheep` | Public opponent count of animals: SHEEP. |
| 113 | `shop_bakery` | Current unlocked instance count (duplicates count): BAKERY. |
| 114 | `shop_pizza_shop` | Current unlocked instance count (duplicates count): PIZZA_SHOP. |
| 115 | `shop_brunch_spot` | Current unlocked instance count (duplicates count): BRUNCH_SPOT. |
| 116 | `shop_yarn_store` | Current unlocked instance count (duplicates count): YARN_STORE. |
| 117 | `shop_ice_cream_shop` | Current unlocked instance count (duplicates count): ICE_CREAM_SHOP. |
| 118 | `shop_pet_cafe` | Current unlocked instance count (duplicates count): PET_CAFE. |
| 119 | `shop_smoothie_shop` | Current unlocked instance count (duplicates count): SMOOTHIE_SHOP. |
| 120 | `shop_farmers_market` | Current unlocked instance count (duplicates count): FARMERS_MARKET. |

TILE_KINDS: 0=EMPTY, 1=LOCKED, 2=WEED, 3=WHEAT, 4=CARROT, 5=TOMATO, 6=STRAWBERRY, 7=MELON, 8=COOP, 9=PASTURE.

## Fixed command ids

| Id | Command |
|---:|---|
| 0 | `['PASS']` |
| 1 | `['NORTH']` |
| 2 | `['SOUTH']` |
| 3 | `['EAST']` |
| 4 | `['WEST']` |
| 5 | `['WATER']` |
| 6 | `['HARVEST']` |
| 7 | `['FERTILIZE']` |
| 8 | `['DIG']` |
| 9 | `['BUILD_COOP']` |
| 10 | `['BUILD_PASTURE']` |
| 11 | `['FEED']` |
| 12 | `['CARE']` |
| 13 | `['COLLECT_FERTILIZER']` |
| 14 | `['PLANT', 'WHEAT']` |
| 15 | `['PLANT', 'CARROT']` |
| 16 | `['PLANT', 'TOMATO']` |
| 17 | `['PLANT', 'STRAWBERRY']` |
| 18 | `['PLANT', 'MELON']` |
| 19 | `['PICKUP', 'WHEAT']` |
| 20 | `['PICKUP', 'CARROT']` |
| 21 | `['PICKUP', 'TOMATO']` |
| 22 | `['PICKUP', 'STRAWBERRY']` |
| 23 | `['PICKUP', 'MELON']` |
| 24 | `['PICKUP', 'EGG']` |
| 25 | `['PICKUP', 'MILK']` |
| 26 | `['PICKUP', 'WOOL']` |
| 27 | `['PICKUP', 'FERTILIZER']` |
| 28 | `['PICKUP', 'GOOSE']` |
| 29 | `['PICKUP', 'COW']` |
| 30 | `['PICKUP', 'SHEEP']` |
| 31 | `['DROP']` |
| 32 | `['PLACE', 'WHEAT']` |
| 33 | `['PLACE', 'CARROT']` |
| 34 | `['PLACE', 'TOMATO']` |
| 35 | `['PLACE', 'STRAWBERRY']` |
| 36 | `['PLACE', 'MELON']` |
| 37 | `['PLACE', 'EGG']` |
| 38 | `['PLACE', 'MILK']` |
| 39 | `['PLACE', 'WOOL']` |
| 40 | `['PLACE', 'FERTILIZER']` |
| 41 | `['PLACE', 'GOOSE']` |
| 42 | `['PLACE', 'COW']` |
| 43 | `['PLACE', 'SHEEP']` |

## Segment NPZ arrays

No pickle/object arrays; np.load(path, allow_pickle=False). N=teacher turns, U=14, C=44.
`reports/BOARD_SCHEMA.json` is a machine-readable copy of the fixed feature/vocabulary order.

| Array | dtype / shape | Meaning |
|---|---|---|
| tiles | float32 N,100,31 | Own pre-action tiles. |
| units | float32 N,14,19 | Own pre-action workers. |
| glob | float32 N,H | Global feature columns above. |
| unit_mask | bool N,14 | Present before action, including implicit PASS workers. |
| step | int16 N | Absolute physical pre-action step. |
| command | int16 N,14 | Issued vocabulary id, -1 padded. |
| command_argc | int8 N,14 | Original command length; preserves omitted amount vs explicit one. |
| command_issued | bool N,14 | Explicit command in action; otherwise a present worker implicitly passes. |
| took_effect | bool N,14 | Native position/tile/bag/shed/seeds state changed. |
| command_loss_mask | bool N,14 | Present and (native effect or PASS). Apply unit_mask too. |
| legal | bool N,14,44 | Conditional on earlier true commands, including their exact amounts. |
| amount | int32 N,14 | Exact issued PICKUP/PLACE quantity; default one; other ops placeholder one. |
| amount_applicable | bool N,14 | PICKUP or shed placement; animal placement amount is ignored by engine. |
| amount_class | int8 N,14 | amount-1 when applicable and 1..5; otherwise -1. |
| amount_loss_mask | bool N,14 | Applicable, effective and amount in 1..5. Out-of-range values are not clipped. |
| transferred | int32 N,14 | Actual bag item quantity change for amount-applicable commands; else zero. |
| position | int16 N,14,2 | Pre-command x,y; diagnostic label metadata (also in units). |
| target | int16 N,14 | Next effective non-move job at or after this turn, within this day; tile or 100. |
| target_step | int16 N,14 | That job's absolute step; -1 absent. |
| target_command | int16 N,14 | That job's command id; -1 absent. |
| target_distance | int16 N,14 | Manhattan distance from present position; zero absent. |
| target_value | float32 N,14 | Rough work_features immediate-dollar heuristic at that job's pre-turn observation; can be negative. |

Apply unit_mask to every label, including stay targets; padded target=100 is never a target-loss example.
Future targets/step/command/value/distance, effects, legal masks and all labels are excluded from encoder inputs.
Manifest source/game/day/H/split/episode provenance is also excluded from inputs. L3 contains only step>=takeover_step,
although native replay and history include the whole morning prefix. Game 10320-10324 split=test is encoded but excluded
from counting tables. NPZ SHA256 and source replay SHA256 are in manifests/turns.csv; encoder hash pins the contract.
All large arrays and per-segment audit receipts stay on D:. Builder verifies all six native tables for every segment.
Verification reconstructs stored commands, replays both seats through the engine, and compares all arrays bit-for-bit.

Rebuild: set PYTHONHASHSEED=0 and KAGML_DATA, then `python tools/build_turn_dataset.py --workers 2`.
Sample live parity/re-execution: `python tools/build_turn_dataset.py --verify --smoke --workers 2`.
Hash-seed comparison: run that verification in fresh processes with PYTHONHASHSEED=0 and 173.
Native rule regressions: `python tools/test_board_features.py`.

## Plan and market labels (package P)

Worker NPZ files and the encoder are unchanged. Market labels live in the **separate sibling directory**
`<data>/datasets/turn-markets/<source>/<worker-stem>.npz`, indexed by `manifests/turn-markets.csv`.
Do not glob these into worker inputs. Join by `worker_file`, verify `worker_sha256`, and align by physical `step`.
These arrays are training labels, never observation features. Existing test games 10320-10324 are not opened;
those original worker manifest rows are retained, without new market sidecars.

Fixed vocabulary (28 tokens, zero-based): SELL for PRODUCTS (9); BUY_SEED for CROP_NAMES (5); BUY_ANIMAL
for ANIMAL_NAMES (3); BUY_PRODUCT for PRODUCTS (9); BUY_LAND; HIRE. PRODUCT order is WHEAT, CARROT,
TOMATO, STRAWBERRY, MELON, EGG, MILK, WOOL, FERTILIZER. Crop order is WHEAT, CARROT, TOMATO,
STRAWBERRY, MELON; animal order GOOSE, COW, SHEEP. BUY_PRODUCT tokens exist for every product for a
stable mapping, but the engine supports only WHEAT and FERTILIZER (`order_valid=False` for others).

For N teacher turns, V=28 and M=max(1, maximum issued orders in this segment):

| Array | Shape / dtype | Meaning |
|---|---|---|
| `step`, `seat` | N; int16, int8 | Absolute physical step and teacher's physical seat. |
| `units_issued` | N,V; int64 | Sum of native-parseable requested quantities by token; HIRE/BUY_LAND each count one per issued order. |
| `units_executed` | N,V; int64 | Actual successful units from native market_orders; repeated orders are summed. |
| `order_count` | N; int16 | Number issued, including rejected and over-cap orders. |
| `order_token` | N,M; int16 | Issued order vocabulary id; -1 for padding or unknown token (distinguish with mask). |
| `order_quantity`, `order_executed` | N,M; int64 | Parsed requested quantity and native successful quantity. |
| `order_mask` | N,M; bool | True for each issued order, in its original order; no truncation at ten. |
| `order_valid` | N,M; bool | Native parse succeeds and token/product is supported; does not assert affordable or processed. |
| `order_attempted` | N,M; bool | Native processing reached this order; capped extras remain issued but unattempted. |
| `order_took_effect` | N,M; bool | Native successful units >0; partial fills retained. |
| `order_cash_delta` | N,M; float64 | Actual net cash change for this order. |
| `order_json` | N,M; Unicode | Exact issued order as JSON, including malformed or unknown orders; empty string padding. No pickle/object arrays. |
| `buy_land_requested`, `buy_land_executed` | N; bool | Binary land-head labels; units arrays and ordered rows still retain multiple land orders. |
| `sale_step`, `sale_order_index`, `sale_product` | S; int16, int16, int8 | Own-seat native sale fills, indexed by physical step, issued order and PRODUCTS id. |
| `sale_units`, `sale_unit_price`, `sale_revenue` | S; int64 | Native fill quantity, price and revenue; preserves price changes within a single SELL order. |

For unavailable/rejected fills all executed quantities/cash are zero. Requested and executed quantities are distinct:
SELL 20 with only 3 in the shed labels request 20 and execution 3. Orders are processed after worker operations;
newly harvested/dropped items and inventory capacity are resolved by native execution, not reconstructed from dawn.

New sources: **l1bal**, teacher on 60 balanced template-game farms at each morning 0-29; **tfull**, teacher's own
full games against Metav4 in both seats, sharded into days 0-29. Day 29 has 23 actions; a full game has 719.
Worker schemas and day-bounded future target labels are unchanged. `manifests/turns.csv` retains its original columns. Physical teacher seat is explicit in the market and teacher-full
manifests; tfull paths contain `seat0`/`seat1` to avoid collisions. `plan_dataset.teacher_seat` validates the filename against the episode id; old sources are seat 0. Public `game` remains the seed.
Encoding uses the unchanged board_features.encode and native reconciliation, including physical seat 1; history
comes from the corresponding parent template/full replay before the day, then observes actual segment turns.

`manifests/plan-seeds.csv` fixes 60 seed identities before generation: 20 per B, with 15 train and 5 analysis2 per B.
The **analysis2** split is never training, for either source or either physical seat. Consumers must honor the
manifest split and seed reservation; do not classify all seed ids >=10401 as train. Existing training scripts have
not been changed. All initial worker manifest rows and NPZ hashes are retained. Board input features, including
legacy n_loss_* estimates described above, are unchanged by this label-only addition.


The legacy turn checker enumerates a fixed source list; validate the new sources with
`python tools/check_plan_data.py --audit`. Unique shard identity includes physical teacher seat:
use worker_file or (source, game, day, H, teacher_seat), since tfull has both seats at each seed/day.
