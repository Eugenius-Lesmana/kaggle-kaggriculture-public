# The top agents were trained networks, not hand-written plans

Date: 2026-10-15
Status: **correction.** Supersedes our reading in
[`MICROTAPE_STUDY_2026-09-28`](MICROTAPE_STUDY_2026-09-28.md), [`ROUTE_BACKBONES_2026-09-29`](ROUTE_BACKBONES_2026-09-29.md)
and the repository README that the top agents' seasons were "optimised as one piece, offline", like a tape.
The measurements in those notes stand. The explanation does not.

Sources: write-ups the teams published after the competition (linked below by final rank). We have not run
their code; the published repositories we checked contain no trained weights.

## What the top teams ran

| Final rank | Approach | Source |
|---|---|---|
| 1st | A 10M-parameter Transformer. Behaviour cloning on public replays and on games of their own heuristic planner, alternated with self-play reinforcement learning (PPO); about 8.3 million self-play games in the final model's lineage. A rule-based patch at play time. | [write-up](https://www.kaggle.com/competitions/kaggriculture/discussion/745073) |
| 5th | An 8.2M-parameter Transformer, behaviour cloning on recent top-team replays, told at play time to imitate the strongest team's newest version. Two rules. | [write-up](https://www.kaggle.com/competitions/kaggriculture/discussion/745367) |
| 7th | A 21.5M-parameter Transformer, pure behaviour cloning, no reinforcement learning, trained on the trades the engine actually executed. | [write-up](https://www.kaggle.com/competitions/kaggriculture/discussion/745119) |
| 31st | A cloned network that sets each day's plan, a hand-written C++ planner that carries it out, and a learned forecast of the opponent's sales. | [write-up](https://www.kaggle.com/competitions/kaggriculture/discussion/745783) |
| 347th | Hand-written rules tuned against daily targets measured from 22 top submissions. | [write-up](https://www.kaggle.com/competitions/kaggriculture/discussion/749466) |
| 512th | Hand-written routes chosen by which shops opened. | [write-up](https://www.kaggle.com/competitions/kaggriculture/writeups/kaggriculture-rank-512-bronze-how-my-agent-worke) |

"Behaviour cloning" means training a network to predict the action a strong player took in each recorded game
state. Six write-ups are not the whole top 50; the pattern above is what they show, not a census.

## What this changes in our notes

- **Repeated routes.** We saw the same worker follow the same route on the same day in different games, and
  read that as a fixed plan. A trained network that sees similar states also makes the same choices, so the
  observation fits either. The write-ups settle it: it was a network.
- **"A cell-state rule reproduces only ~68% of core actions."** The 7th-place team measured that independent
  top teams agree with each other on only 66–68% of decisions. There was no compact rule set to recover.
- **Copying single moves failed.** The 5th-place team found the same: copying one macro move from another team
  "hurt on its own", and a single rule could gain $1.6k on one model and lose $2.8k on the next. Our transplant
  and template experiments match this.

## What still holds

- The census: about 80% of the mid-ladder ran forks of the Metav4 tape family. Metav4 *is* a fixed action
  table; this correction is about the top agents only.
- The production and yield measurements (units, fertilizer timing, land timing) describe what the top agents
  did, whatever produced it.

## Methods that match ours

The write-ups used the same evaluation ideas we did: paired seeds, both seats, our money and the opponent's
money reported separately (the 31st-place team found one network won mostly because the opponent earned
$4.6k less), and continuing a recorded game from a chosen day. Three of them added a rule that sells what would
otherwise be destroyed when the shed overflows at midnight, worth about $300–750 a game to them.
