"""Emit the column/array contract directly from the encoder's stable ordering."""
import json
from build_turn_dataset import B,REPO


def main():
    tile={
    'x':'Column 0..9.','y':'Row 0..9.','kind':'TILE_KINDS categorical id (mapping below).','animal':'0 absent; GOOSE=1, COW=2, SHEEP=3.','owned':'1 unless LOCKED; the shed is not a tile.',
    'age':'Current day minus planted_day / placed_day; otherwise 0.','next_production':'Same t_next_prod definition as work_features: pre-first yield remaining days; mature one-time crop 0; ongoing crop age phase modulo interval; animal 0 when scheduled tonight, otherwise days to scheduled night; absent -1.',
    'held':'yield_units waiting on this tile.','max_held':'Crop max_yield or animal max_held.','held_fraction':'held / max_held; absent 0.','watered':'Plant watered_today.','dry_days':'Plant consecutive_unwatered.','fertilizer_days':'Plant max(0, fertilized_until_day-day+1), inclusive active days.','fed':'Animal fed_today.','cared':'Animal cared_today.','unfed_days':'Animal consecutive_unfed.','care_bonus':'Animal pending_care_bonus.','fertilizer_available':'Animal fertilizer_available.','rot_in':'Plant max_lifespan_step minus current absolute step, or 999 absent/unset.','ongoing':'Crop ongoing flag.','first_yield_day':'Crop/animal first_yield_day from engine constants.','production_interval':'Crop/animal interval from engine constants.',
    'n_dies_tonight':'Plant is unwatered and already has >=1 consecutive_unwatered.','n_prod_tonight':'Potential scheduled production under work_features formula; independent of death/escape/feed flags.','n_double_tonight':'Ongoing scheduled crop production and fertilized_until_day >= day; potential double conditional on watering.','n_escapes_tonight':'Animal unfed and consecutive_unfed >=1.','n_full':'Animal held >= max_held.','n_loss_if_dry':'Same work_features dollar estimate: dying crop held*price + seed + (max_yield-held)*price; otherwise dry scheduled ongoing production price*(2 if fertilized else 1).','n_loss_if_unfed':'Same work_features dollar estimate: escaping animal cost+held*price; otherwise unfed scheduled production price*(1+care_bonus).','seed_cost':'Crop seed cost.','animal_cost':'Animal purchase cost.'}
    unit={'x':'Current worker column.','y':'Current worker row.','is_farmer':'1 for slot 0, else 0.','last_move_dx':'Last effective cardinal move x delta today, else 0.','last_move_dy':'Last effective cardinal move y delta today, else 0.','since_last_job':'Turns since last effective non-move/non-PASS job today; 999 if none.','last_job_command':'Command vocabulary id of that job; -1 if none.'}
    price={'price':'Current integer sale quote.','market_stock':'Current shared market inventory.','price_dawn':'First pre-action quote of this day.','price_high_today':'Maximum observed quote this day through current turn.','price_low_today':'Minimum observed quote this day through current turn.','price_change_4h':'Current quote minus quote four observations earlier; 0 if fewer than five observations.','relative_price':'Current quote / engine MARKET_PARAMS base.','daily_demand':'Expected daily town consumption from current unlocked shops (work_features.daily_demand).'}
    glob={'day':'Zero-based day.','hour':'Zero-based hour.','turns_left_game':'719 - absolute physical step; terminal frame has no action.','turns_left_day':'24-hour; includes current action, except final game truncation.','days_left':'29-day.','cash':'Own bank.','opp_cash':'Public opponent bank.','cash_gap':'Own minus opponent bank.','hires_today':'Own hires_today counter.','land_count':'Number of owned quadrants.','hands':'Number of currently active hands.','shed_total':'Sum of all own shed counts.'}
    def description(kind,key):
        if kind=='tiles':return tile[key]
        if kind=='units':return unit.get(key,'Own bag count of '+key.removeprefix('bag_').upper()+'.')
        if key in glob:return glob[key]
        for prefix,desc in [('land_','Owned quadrant flag: '),('shed_','Own shed item count: '),('seeds_','Own seed count: '),('opp_crop_','Public opponent count of crop tiles: '),('opp_animal_','Public opponent count of animals: '),('shop_','Current unlocked instance count (duplicates count): ')]:
            if key.startswith(prefix):return desc+key.removeprefix(prefix).upper()+'.'
        for item in B.PRODUCTS:
            if key.startswith(item.lower()+'_'):return item+': '+price[key[len(item)+1:]]
        raise KeyError(key)
    schema=dict(version=1,max_units=B.MAX_UNITS,stay_target=100,tiles=list(B.TILE_COLUMNS),units=list(B.UNIT_COLUMNS),glob=list(B.GLOBAL_COLUMNS),commands=[list(c) for c in B.COMMANDS],tile_kinds=list(B.TILE_KINDS),items=list(B.ITEMS),animal_names=list(B.ANIMAL_NAMES))
    (REPO/'reports/BOARD_SCHEMA.json').write_text(json.dumps(schema,indent=2)+'\n',encoding='utf-8')
    text="""# Whole-board encoder and turn tensor contract (package N)

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
"""
    for kind,cols in [('tiles',B.TILE_COLUMNS),('units',B.UNIT_COLUMNS),('glob',B.GLOBAL_COLUMNS)]:
        text+=f'\n### {kind}: {len(cols)} columns\n\n| Index | Column | Meaning |\n|---:|---|---|\n'
        for i,k in enumerate(cols):text+=f'| {i} | `{k}` | {description(kind,k)} |\n'
    text+='\nTILE_KINDS: '+', '.join(f'{i}={k}' for i,k in enumerate(B.TILE_KINDS))+'.\n'
    text+='\n## Fixed command ids\n\n| Id | Command |\n|---:|---|\n'+''.join(f'| {i} | `{list(c)}` |\n' for i,c in enumerate(B.COMMANDS))
    text+="""
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
"""
    (REPO/'reports/BOARD_FEATURES.md').write_text(text,encoding='utf-8')
    print(json.dumps({'tiles':len(B.TILE_COLUMNS),'units':len(B.UNIT_COLUMNS),'glob':len(B.GLOBAL_COLUMNS),'commands':len(B.COMMANDS)}))

if __name__=='__main__':main()
