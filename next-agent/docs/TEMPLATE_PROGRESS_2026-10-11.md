# Template agent: progress on 2026-10-11

> **Superseded** by [`TEMPLATE_PROGRESS_2026-10-16`](TEMPLATE_PROGRESS_2026-10-16.md): the current confirmed
> version reaches **0.913** of Metav4's final bank. The figures below are as of 11 October.

This is a progress note, not a result. The target has not been reached yet.

The template agent is our attempt to rebuild a strong farm from what can be seen in public replays of
one reference team, and then improve it by measurement. This note covers where it stands, what worked,
what did not, and what is still missing. The agent's code and the detailed study of the reference team
are held back until the competition's grading has ended.

Every figure below was measured. Where something is an estimate, the line says so.

## Where it stands

| | Bank per game | Share of Metav4's bank |
|---|---:|---:|
| First working copy | $82,346 | 0.790 |
| Current confirmed version | $89,751 | 0.892 |
| Current version, pooled over five test setups | | 0.893 |

The target is at least 0.9 of Metav4's bank. The agent is just short of it and wins 2 of the 24
standard games outright.

## Versions

Each row adds to the one above it. From 2026-10-06 on, figures are from the standard 24 games.

| Date | Version | Bank per game | Share of Metav4's bank |
|---|---|---:|---:|
| 2026-10-03 | First hand-built policy | $63,134 (6 games) | 0.52 |
| 2026-10-04 | Workers plan a whole day at a time | $69,889 (6 games) | not recorded |
| 2026-10-06 | First working copy, frozen as the baseline | $82,346 | 0.790 |
| 2026-10-08 | Job fixes, herd follows the shops, herd bug fixed | $87,196 | 0.859 |
| 2026-10-08 | No wheat bought into a full shed | not recorded | 0.868 |
| 2026-10-08 | Melon rush | $88,644 | 0.880 |
| 2026-10-10 | Deadline rule (current confirmed version) | $89,751 | 0.892 |
| 2026-10-10 | Crop layout rebuilt to follow the reference team | level with the row above | not adopted |

## How it is measured

- **Standard setup:** 24 fixed seeds, our agent in seat 0 against Metav4 in seat 1. Each change is
  compared with the version before it on the same seeds, as a per-game difference with its standard
  error.
- **Other setups:** seats swapped, against F1, against F4, and 24 fresh seeds. A change counts as
  confirmed only when it also holds there.
- **Split by scenario:** every comparison is reported by the shops that open early, not only as an
  average over all games.
- **Share:** the mean, over games, of our final bank divided by the opponent's.

## What worked

| Change | Worth per game |
|---|---:|
| Four fixes to how workers pick jobs, and a bug in herd sizing | about +$3,000 |
| Herd size follows which shops are open | about +$2,900 |
| No wheat bought at the last hour into a full shed | +$500 to +$700 |
| Ripe melons are urgent and carried straight to the shed | +$500 to +$1,000 |
| Deadline rule | +$1,384 (SE 381), pooled over five setups |

The deadline rule is the clearest single gain. Work that is lost if it is not done today (a plant
about to die, fruit on its last day, an animal that produces tonight but has not been fed) is given to
the nearest worker. Once that worker has only just enough time left to reach all of it, it stops doing
other jobs on the way.

## What did not work

Each line is a 24-game test unless marked.

| Attempt | Result per game |
|---|---|
| Carrying fertilizer to strawberries, three versions | -$1,100; -$1,300 to -$1,500; then level. Closed. |
| Evening couriers and extra fertilizer pickups | Lost money or level |
| Moving the strawberry block next to the shed | -$1,700 |
| That block plus a morning run to the shed plus a dawn crew | about -$3,000 (4 games only) |
| Planting new land sooner | -$989 (SE 497) |
| Two changes to animal care | Level; +$366 (SE 451), not confirmed |
| Crop layout rebuilt to follow the reference team's | Our bank -$175 (SE 693) over four setups |
| Herd size taken from the reference team's layout | Share 0.887, our bank -$680 (SE 947) |

## A result we do not claim

Rebuilding the crop layout to follow the reference team raised the share against Metav4 from 0.891 to
0.911 on the standard setup. We do not count it:

- Our own bank did not move (-$133, SE 917). Metav4's fell by $1,887.
- The cause was strawberries. We planted them earlier, sold earlier, and lowered the price in the days
  when Metav4 sells most of its crop.
- On fresh seeds neither bank moved (share 0.885 to 0.888).
- By scenario it was a gain of about $3,000 when no strawberry buyer opens early, and a loss when one
  or two do.

## What is still missing

- **A layout chosen by scenario.** Using the rebuilt layout only when no strawberry buyer opens early
  should be worth about $1,100 a game on the standard setup. This is arithmetic from the two measured
  versions. It has not been built or run.
- **Fertilizer in the second week.** From day 6 we collect and sell clearly less fertilizer than the
  reference team, about $1,400 behind by day 10. The cause has not been traced.
- **Animal care when the product is dear.** When milk or wool sells at $150 or more, we care for about
  70% of animal-days. The reference team manages about 90%.
- **Midnight overflow and late rot.** Some goods are lost when the shed is full at midnight, and some
  wheat and carrots are picked too late. Both are small.

## What we learned about the method

- Counting every lost unit into a named bucket first, and then changing behaviour only for the largest
  bucket, produced all of the confirmed gains.
- Copying one behaviour from a strong team onto a farm arranged differently failed every time. Its
  behaviours depend on each other and on its layout.
- An average over all games can hide two opposite effects. Splitting by scenario showed them.
- A share against one opponent can rise because the opponent earns less. Our own bank and a second
  opponent have to be checked before a change counts.
- Four games cannot resolve a difference under about $2,000. Decisions were made on 24.