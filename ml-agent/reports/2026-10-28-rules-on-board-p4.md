# Rules on top of board-p4 (2026-10-28)

**Plain answer:** three rules kept. `net:board-p4:market:overflow:endmask:endwork` reaches **share 0.871 against
fifth-nflow (board-p4 0.839), margin +3,896 a game (se 619), better on 23 of 24 seeds**; still 0 of 48 wins.
Shop-turn selling, the wheat cap, sell sorting and play-time logit adjustment were rejected.

All runs: 48 games against live fifth-nflow, seeds 20001-20024, both seats, paired by seed and seat
(`tools/paired_runs.py`). Options are in `src/kagml/net_player.py`.

| Rule | Run | Compared with | Margin a game (se) | Seeds better | Share | Verdict |
|---|---|---|---:|---:|---:|---|
| `shopsell`: sell strawberry, milk, wool only on steps with step % 4 == 1 (just after the town shops buy) | `runs/nflow-p4-shopsell` | board-p4 | -2,774 (1,226) | 8/24 | 0.817 | rejected |
| `overflow`: on hour 23, sell from the shed what the night drop-off would discard | `runs/nflow-p4-overflow` | board-p4 | +3,130 (572) | 21/24 | 0.864 | kept |
| `endmask` on top of `overflow`: no seeds that cannot ripen by day 29, no animals after day 19, no wheat feed on day 29 (template day 29 included) | `runs/nflow-p4-ovf-end` | overflow | +340 (77) | 21/24 | 0.867 | kept |
| overflow + endmask | `runs/nflow-p4-ovf-end` | board-p4 | +3,470 (572) | 22/24 | 0.867 | |
| `wheatcap` on top: wheat feed bought only for unfed animals the stock cannot cover | `runs/nflow-p4-ovf-end-wc` | overflow + endmask | -766 (1,318) | 13/24 | 0.862 | rejected (our bank +472, fifth-nflow's +1,237) |
| `sortsell` on top: sells first in the order list, dearest first | `runs/nflow-p4-ovf-end-ss` | overflow + endmask | -49 (286) | 13/24 | 0.867 | rejected (no effect) |
| `endwork` on top: no planting a crop that cannot ripen by day 29, no coop/pasture after day 19, no care with no production night left | `runs/nflow-p4-ovf-end-ew` | overflow + endmask | +426 (147) | 16/24 | 0.871 | kept |
| overflow + endmask + endwork | `runs/nflow-p4-ovf-end-ew` | board-p4 | +3,896 (619) | 23/24 | 0.871 | |
| `la0.3` on top: command logits minus 0.3 x log(teacher frequency) (`src/kagml/command_prior.py`; PASS, DIG and commands used < 10 times not boosted) | `runs/nflow-p4-best-la03` | overflow + endmask + endwork | -442 (1,015) | 13/24 | 0.867 | rejected |

Logit-adjustment pilot, seeds 20001-20004 both seats (8 games, `runs/nflow-p4-best-la{0.15,0.3,0.6}`): +998 (1,368),
+2,225 (2,695), +1,822 (2,116). The 48-game run of the best pilot value did not confirm it.

## Why these rules (from existing games, seeds 20001-20008)

- **Sale timing.** The teacher sells 61% / 71% / 51% of its strawberries / milk / wool on the turn after the shops
  buy; board-p4 34% / 53% / 40%. Copying only the timing failed: our bank -876, fifth-nflow's +1,740 a game. We then
  sell on the same turns as fifth-nflow and both push the price down; first-unit prices rose (milk about 99 to
  114) but larger batches lower the price per unit.
- **Night overflow.** The engine drops all bags into the shed (100 units) at night and discards what does not
  fit. board-p4 had a full shed on 8 mornings a game (the teacher 3) and discarded about 80 units a game (the
  teacher about 5), mostly on days 22-28. Codex's loss split (`dev/eugene-codex-loss-split`, 8246a3a) finds an
  unexplained stock loss of +965 / +1,429 / +977 for days 12-21 / 22-27 / 28-29, consistent with this. With the
  rule our bank rose only +417; fifth-nflow's fell 2,713 (our evening sales lower the price it sells at next).
- **Late purchases.** On day 29 the template bought about 23 wheat and half a goose a game; wheat seeds were bought
  on days 27-28. The teacher buys none of these.

Slowest turn with the three kept rules: 774 ms (limit 1 s).
