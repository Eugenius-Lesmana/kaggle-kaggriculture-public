# Online selling — 2026-10-28

**Reject `onlinesell`: live paired margin −4,394 coins/game (seed SE1,186), share0.834,0/48wins.** Our bank changes−1,314/game (SE1,080); fifth-nflow’s changes+3,079 (SE553). Best remains `net:board-p4:market:overflow:endmask:endwork`.

All48 evaluation games use seeds20001–20024bothseats against live fifth-nflow, compared with `tools/paired_runs.py nflow-p4-ovf-end-ew nflow-p4-onlinesell`. The default ruled agent first reproduced the exact seed20001seat0 gameplay hash; final replay/identity/action/timing checks passed for48. Fourworkers, PYTHONHASHSEED=0. Acceptance required positive paired margin at about2SE, estimated over24seed means (bothseats averaged); this fails.

## Rule fixed before live evaluation

For milk,wool,strawberry on network days6–28, track today’s observed high and previous price. Defer requested sales only when price is below80%of observed high, is non-rising, shed holds fewer than70items and hour<22. Release on any price rise, roompressure or hour22deadline. Held quantities are not added twice to later model requests, and releases are clipped to current shed stock. Overflow still runs AFTER this rule at hour23. Day29 stays template. No future prices, future town draws, oracle actions or evaluation observations enter the rule/selection.

Unlike rejected fixed-turn `shopsell`, this version releases on a rising price rather than waiting a fixed number of turns. It still loses; the test does not establish that all learned selling policies fail.

## Training-only recorded-market tuning

Six fixed settings were evaluated on90 original P2 full games against fifth-nflow:45plan TRAIN seeds, bothseats. Those P2 farms/market histories differ from current P4. No evaluation seeds were used for tuning. The full native replay validates each source, then price-only re-auctions preserve recorded pre-turn market/worker arrivals and opponent issued sale orders. Future inventories, cash feasibility and workers are held recorded; deferred quantity/terminal stock may differ. This is a conditional training diagnostic, not a full counterfactual game or a fixed-volume oracle.

| Fraction of observed high | Shed hold limit | Recorded revenue change/game | Day-end unsold deferred units/game |
| --- | --- | --- | --- |
| .80 |70|−611|13.80|
| .80 |85|−742|16.23|
| .90 |70|−2,481|26.89|
| .90 |85|−2,920|31.76|
| .95 |70|−5,255|42.13|
| .95 |85|−5,996|49.18|

Every tested setting lost recorded revenue; the least harmful (.80/70) was preselected for the requested live test. No selection was changed after seeing live games. The earlier4,946/game hindsight oracle used16evaluation P4 recordings, fixed daily quantities, stock-aware hindsight and different histories. It is sizing evidence, not a training target or expected attainable gain; −611 on these training recordings is not a paired comparison with that number.

[Training scores](ONLINE_SELL_TRAINING.json), [live paired checks](ONLINE_SELL_CHECKS.json). Full source receipts/hashes are in `runs/next-20261028/selling-train` and `.cache/next/selling-inputs.json`; no test contents10320–10324, protected encoding/vendor changes, pushes or submissions. The opt-in code remains for reproducibility and is not included in the best agent.
