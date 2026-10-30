The complete per-operation data is on D:, not in git:

- `<data>/runs/overnight-s-complete/shed_events.csv.gz`: 12,742 item rows for 10,059 teacher commands.
- `<data>/runs/overnight-s-complete/tool_keep_decisions.csv.gz`: 21,694 tool-at-shed opportunities.
- `cases/*.json.gz` and `*.metrics.json`: per-case measurements and native/Parquet audit receipts. Source L1/L3 files remain unchanged.

`(event_id, item)` is the key in each export. One DROP can have several item rows. `source, game, day, H, episode, step, unit` join to the original manifest/Parquet tables. L1 H=0; L3 H=4/8/12/16. Step is the absolute pre-action turn; hour is 0-23. Only seat 0 teacher actions are exported, with L3 step >= takeover_step.

| Fields | Meaning |
|---|---|
| op, item, requested, amount | PICKUP actual bag increase; DROP/PLACE actual bag decrease. DROP request is blank because it empties the bag. Every non-animal-placement PLACE at a shed-access tile is included. |
| carried_before, bag_before | Current-item quantity and the full positive bag contents immediately before that worker's action. |
| shed_available, shed_received, discarded | Native shed state/change for this command; pickup shed_received is negative. Discarded is removed minus accepted for an issued deposit. |
| open_jobs | Wheat: animals not fed today. Fertilizer: plants whose fertilizer has expired (`fertilized_until_day < day`). Animals: currently empty matching structures. Other goods have no worker input jobs. |
| legal_jobs | Fertilizer counts all PLANT tiles: the native engine also allows refreshing active fertilizer. Otherwise equals open_jobs. This is eligibility, not a profitable-job count or the teacher's private plan. |
| other_workers_carrying, other_carried | Number of other active workers holding this item, and their total quantity. |
| uncovered_jobs | max(0, open_jobs - other_carried). Does not assign/reserve jobs or make distant supplies interchangeable. |
| pre_turn_* | Same counts and shed stock in the recorded observation before any worker acts. Use these observable inputs for training; unprefixed counts reflect actual sequential execution after earlier workers. |
| first_use_lag | PICKUP: turns until this worker first consumes this item type, while it stays carried. FEED, FERTILIZE and animal placement count as use. Continues through partial deposits that keep the item; stops if the item leaves the bag. |
| use_censor | Blank when use is observed; returned / overnight_return means the item leaves the bag before use; window means a genuinely unobserved endpoint. No unknown-window pickup follow-ups remain in these complete days. |
| next_drop_lag, next_drop_kind | First later DROP or shed PLACE of any item, or observed automatic night return. Kind is command / overnight. Night endpoints are at the next dawn boundary, never counted as teacher commands. |
| left_before_next_drop | Whole bag quantity of this item immediately before that deposit. Can include earlier stock, harvesting or another pickup. |
| removed_at_next_drop, kept_after_next_drop | Quantity removed from the bag, and quantity retained. Removal can include overnight overflow discard; it does not assert every unit was accepted into the shed. A PLACE of another item can keep all the tool. |
| clean_cohort | No same-item stock before the pickup and no replenishment before the first deposit. Only here can the leftover be assigned exactly to this pickup. Addition/use totals and a flow-balance assertion support it. |

For DROP/PLACE, future-use fields are blank: deposited units merge in the shed and cannot be identified across later pickups. Their actual returned quantity, previous bag and demand context are recorded. Unused at a deposit does not mean permanently wasted; it can be kept or used later from the shed.

Keep opportunities are resource-specific worker turns at a shed-access tile with wheat/fertilizer already carried. Decision is return, keep, use or pickup_more. Sale goods exclude wheat/fertilizer and animals. Partial deposits can return another tool or animal, not only sale goods. Return percentages in SHED_KEEP_RULES condition on return-or-keep, with use/replenish counts supplied separately.

Statistics are event weighted. L3 has four correlated recovery windows per morning and a different hour/state mix from L1. Source and H/hour strata are supplied; these are descriptions, not validated replacement-policy rules.
