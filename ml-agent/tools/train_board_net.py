"""Train the whole-board network on the turn dataset (Codex's package N), on the GPU.

python tools/train_board_net.py <run name> [--epochs 8] [--sources l1,l3r1,l3r2,l1edge,l3edge] [--batch 64]
Split by game: training 10301-10314, analysis 10315-10319 (reported every epoch), test 10320-10324 (never read
here). Saves <data>/models/<run name>/model.pt (best analysis command accuracy) and report.json.
The adapter `load_shard` maps the dataset's arrays to the model's inputs; adjust it if the format differs.
"""
import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from kagml.board_net import BoardNet, NetConfig, load, loss_fn, market_loss, qty_class, save  # noqa: E402
import torch.nn.functional as F  # noqa: E402

# Base price per market token (engine 1.32.7: product base, seed, animal cost; land and hire as 1000).
TOKEN_PRICE = torch.tensor([25, 35, 60, 120, 250, 50, 160, 200, 100, 10, 20, 50, 100, 80, 300, 400, 500,
                            25, 35, 60, 120, 250, 50, 160, 200, 100, 1000, 1000], dtype=torch.float32)


def value_market_loss(logits, units, mask, nonzero_weight=4.0):
    """market_loss with each non-zero label also weighted by its value, clamp(units * price / 200, 1, 8)."""
    if not mask.any():
        return logits.new_zeros(())
    lg, u = logits[mask].float(), units[mask]
    y = qty_class(u).clamp(0, lg.shape[-1] - 1)
    ce = F.cross_entropy(lg.reshape(-1, lg.shape[-1]), y.reshape(-1), reduction="none")
    value = (u.float() * TOKEN_PRICE.to(u.device) / 200).clamp(1, 8)
    w = torch.where(y > 0, nonzero_weight * value, torch.ones_like(value)).reshape(-1)
    return (ce * w).sum() / w.sum()


def disagree_cmd_loss(cmd, base_cmd, cmd_y, legal, unit_mask, cmd_mask, k):
    """Command cross-entropy (as in loss_fn) with weight k where the frozen base model's choice differs from the label."""
    cm = cmd_mask.bool() & unit_mask.bool()
    logits = cmd.float().masked_fill(~legal.bool(), -1e9)[cm]
    y = cmd_y[cm].clamp(min=0)
    miss = base_cmd.float().masked_fill(~legal.bool(), -1e9)[cm].argmax(-1) != y
    w = torch.where(miss, float(k), 1.0)
    return (F.cross_entropy(logits, y, reduction="none") * w).sum() / w.sum(), float(miss.float().mean())
from kagml.paths import data_root, models  # noqa: E402

TRAIN = set(range(10301, 10315))
ANALYSIS = set(range(10315, 10320))
KEYS = ("tiles", "units", "unit_xy", "unit_mask", "glob", "command", "target", "amount", "legal", "cmd_mask", "amt_mask",
        "mkt_units", "mkt_mask")
MARKETS = {}       # worker file -> market sidecar file (manifests/turn-markets.csv, package P)


def load_shard(path):
    """One segment of Codex's turn dataset (reports/BOARD_FEATURES.md), mapped to the model's inputs and labels."""
    z = np.load(path)
    n = len(z["step"])
    mkt_units, mkt_mask = np.zeros((n, 28), np.int64), np.zeros(n, bool)
    side = MARKETS.get(Path(path).as_posix())
    if side is not None:                      # align the teacher's market orders by physical step
        m = np.load(side)
        where = {int(t): i for i, t in enumerate(m["step"])}
        for i, t in enumerate(z["step"]):
            j = where.get(int(t))
            if j is not None:
                mkt_units[i], mkt_mask[i] = m["units_issued"][j], True
    return {"mkt_units": mkt_units, "mkt_mask": mkt_mask, "tiles": z["tiles"], "units": z["units"], "unit_xy": z["position"].astype(np.int64), "unit_mask": z["unit_mask"],
            "glob": z["glob"], "command": z["command"].astype(np.int64), "target": z["target"].astype(np.int64),
            "amount": z["amount_class"].astype(np.int64), "legal": z["legal"], "cmd_mask": z["command_loss_mask"],
            "amt_mask": z["amount_loss_mask"]}


def stack(shards):
    """Concatenate segments (float32: some raw features, e.g. cash, exceed the 16-bit range)."""
    out = {}
    for k in KEYS:
        arr = np.concatenate([s[k] for s in shards])
        out[k] = torch.from_numpy(arr.astype(np.float32) if arr.dtype.kind == "f" else arr)
    return out


class Chunks:
    """A split's shard files, loaded a few hundred at a time (all of them do not fit in memory)."""

    def __init__(self, files, shuffle=False, size=300):
        self.files, self.shuffle, self.size, self.workers = list(files), shuffle, size, 0

    def turns(self):
        return sum(len(np.load(f)["step"]) for f in self.files)

    def __iter__(self):
        order = list(np.random.permutation(len(self.files))) if self.shuffle else range(len(self.files))
        files = [self.files[i] for i in order]
        self.workers = 0
        for i in range(0, len(files), self.size):
            chunk = stack([load_shard(f) for f in files[i:i + self.size]])
            self.workers += int(chunk["unit_mask"].sum())
            yield chunk


def batches(data, size, shuffle, device):
    n = len(data["tiles"])
    order = torch.randperm(n) if shuffle else torch.arange(n)
    for i in range(0, n, size):
        idx = order[i:i + size]
        b = {k: v[idx].to(device, non_blocking=True) for k, v in data.items()}
        yield (b["tiles"].float(), b["units"].float(), b["unit_xy"].long(), b["unit_mask"].bool(), b["glob"].float(),
               b["legal"].bool(), b["command"].long(), b["target"].long(), b["amount"].long(), b["cmd_mask"].bool(),
               b["amt_mask"].bool(), b["mkt_units"].long(), b["mkt_mask"].bool())


def evaluate(model, data, device, names):
    model.eval()
    hit, tot, hit_t, by = 0, 0, 0, defaultdict(lambda: [0, 0])
    mk = {"n": 0, **{k: torch.zeros(28, dtype=torch.long) for k in ("ordered_true", "ordered_pred", "ordered_both", "class_hit")}}
    with torch.no_grad():
        for tiles, units, xy, mask, glob, legal, cmd_y, tgt_y, amt_y, cm, am, mu, mm in (
                b for chunk in data for b in batches(chunk, 256, False, device)):
            prev = cmd_y.clamp(min=0).masked_fill(~mask, model.cfg.n_commands)
            with torch.autocast("cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
                outs = model(tiles, units, xy, mask, glob, prev, tgt_y.clamp(0, 100))
                cmd, tgt = outs[0], outs[1]
            if model.cfg.market and mm.any():
                pred_q, true_q = outs[3].float().argmax(-1)[mm], qty_class(mu[mm])
                mk["n"] += int(mm.sum())
                mk["ordered_true"] += (true_q > 0).sum(0).cpu()
                mk["ordered_pred"] += (pred_q > 0).sum(0).cpu()
                mk["ordered_both"] += ((pred_q > 0) & (true_q > 0)).sum(0).cpu()
                mk["class_hit"] += ((pred_q == true_q) & (true_q > 0)).sum(0).cpu()
            pred = cmd.float().masked_fill(~legal, -1e9).argmax(-1)
            m = cm & mask
            ok = (pred == cmd_y) & m
            hit += int(ok.sum()); tot += int(m.sum()); hit_t += int(((tgt.argmax(-1) == tgt_y) & mask).sum())
            for c in cmd_y[m].unique().tolist():
                sel = m & (cmd_y == c)
                by[c][0] += int((ok & sel).sum()); by[c][1] += int(sel.sum())
    model.train()
    per = {names[c] if c < len(names) else str(c): round(h / n, 3) for c, (h, n) in sorted(by.items()) if n >= 200}
    market = {}
    if mk["n"]:
        from kagml.board_features import COMMANDS  # noqa: F401  (vocabulary below is package P's)
        vocab = [l.strip().split(",") for l in open(REPO / "reports" / "PLAN_MARKET_VOCAB.csv")][1:]
        both, tr, pr = mk["ordered_both"].float(), mk["ordered_true"].float(), mk["ordered_pred"].float()
        market = {f"{op}:{item}": {"teacher_orders": int(tr[i]), "recall": round(float(both[i] / tr[i]), 3) if tr[i] else None,
                                   "precision": round(float(both[i] / pr[i]), 3) if pr[i] else None,
                                   "size_class_hit": round(float(mk["class_hit"][i] / tr[i]), 3) if tr[i] else None}
                  for i, (t, op, item, sup) in enumerate(vocab) if tr[i] >= 20}
        market["_overall"] = {"recall": round(float(both.sum() / tr.sum()), 3), "precision": round(float(both.sum() / max(1, pr.sum())), 3)}
    return {"market": market, "command_acc": hit / max(1, tot), "target_acc": hit_t / max(1, data.workers),
            "decisions": tot, "by_command": per}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--sources", default="")
    ap.add_argument("--d", type=int, default=128)
    ap.add_argument("--layers", type=int, default=4)
    ap.add_argument("--init", default="", help="start from this model's weights (fine-tune)")
    ap.add_argument("--market", action="store_true", help="add and train the market head (package P labels)")
    ap.add_argument("--w-market", type=float, default=0.5)
    ap.add_argument("--day-min", type=int, default=None)
    ap.add_argument("--day-max", type=int, default=None)
    ap.add_argument("--validation-split", choices=("analysis", "analysis2", "endval"), default="analysis")
    ap.add_argument("--require-cuda", action="store_true")
    ap.add_argument("--w-animal-land", type=float, default=1.0, help="market loss weight of BUY_ANIMAL and BUY_LAND tokens")
    ap.add_argument("--w-disagree", type=float, default=1.0, help="command loss weight where the --init model disagrees with the label")
    ap.add_argument("--value-market", action="store_true", help="weight market labels by units x price")
    a = ap.parse_args()
    if a.day_min is not None and not 0 <= a.day_min <= 29:
        ap.error("--day-min must be0..29")
    if a.day_max is not None and not 0 <= a.day_max <= 29:
        ap.error("--day-max must be0..29")
    if a.day_min is not None and a.day_max is not None and a.day_min > a.day_max:
        ap.error("--day-min exceeds --day-max")
    if a.require_cuda and not torch.cuda.is_available():
        ap.error("CUDA required; refusing CPU fallback")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(0)
    root = data_root()
    rows = list(csv.DictReader(open(REPO / "manifests" / "turns.csv")))
    if a.market:
        for r in csv.DictReader(open(REPO / "manifests" / "turn-markets.csv")):
            MARKETS[(root / r["worker_file"]).as_posix()] = root / r["file"]
    if a.sources:
        rows = [r for r in rows if r["source"] in a.sources.split(",")]
    if a.day_min is not None:
        rows = [r for r in rows if int(r["day"]) >= a.day_min]
    if a.day_max is not None:
        rows = [r for r in rows if int(r["day"]) <= a.day_max]
    files = {sp: [root / r["file"] for r in rows if r["split"] == sp] for sp in ("train", "analysis", "analysis2", "endval")}  # test never read
    if not files["train"]:
        ap.error("empty training selection")
    if not files[a.validation_split]:
        ap.error("empty validation selection")
    tr = Chunks(files["train"], shuffle=True)        # streamed from disk in chunks (memory)
    va, va2 = Chunks(files[a.validation_split]), Chunks(files["analysis2"] if a.validation_split != "analysis2" else [])
    from kagml.board_features import COMMANDS
    names = [":".join(c) for c in COMMANDS]
    first = load_shard(files["train"][0])
    cfg = NetConfig(tile_feats=first["tiles"].shape[-1], unit_feats=first["units"].shape[-1], glob_feats=first["glob"].shape[-1],
                    n_commands=len(names), d=a.d, layers=a.layers)
    if a.init:                               # fine-tune: keep the scaling the model was trained with
        model = load(models() / a.init / "model.pt", "cpu", market=a.market or None).train()
        cfg = model.cfg
    else:
        cfg.market = a.market
        model = BoardNet(cfg)
    with torch.no_grad():                    # scaling from the training data only (present workers for units)
        for part, key in (() if a.init else (("tiles", "tile"), ("units", "unit"), ("glob", "glob"))):
            sample = stack([load_shard(f) for f in files["train"][::20]])
            x = sample[part].float()
            if part == "units":
                x = x[sample["unit_mask"]]
            x = x.reshape(-1, x.shape[-1])
            getattr(model, f"{key}_mean").copy_(x.mean(0))
            getattr(model, f"{key}_std").copy_(x.std(0).clamp(min=1e-3))
    model = model.to(device)
    base = None
    if a.w_disagree != 1.0:
        if not a.init:
            ap.error("--w-disagree needs --init")
        base = load(models() / a.init / "model.pt", device).eval()
        for p in base.parameters():
            p.requires_grad_(False)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    tok_w = None                                      # tokens 14-16 BUY_ANIMAL, 26 BUY_LAND (reports/PLAN_MARKET_VOCAB.csv)
    if a.w_animal_land != 1.0:
        tok_w = torch.ones(28)
        tok_w[[14, 15, 16, 26]] = a.w_animal_land
    steps = a.epochs * (tr.turns() // a.batch + 1)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=steps, pct_start=0.05)
    out = models() / a.name
    out.mkdir(parents=True, exist_ok=True)
    print(f"train turns {tr.turns()}, analysis turns {va.turns()}, analysis2 turns {va2.turns()}, weights {sum(p.numel() for p in model.parameters())}", flush=True)
    best, log = -1.0, []
    for ep in range(a.epochs):
        t, run = time.perf_counter(), []
        for tiles, units, xy, mask, glob, legal, cmd_y, tgt_y, amt_y, cm, am, mu, mm in (
                b for chunk in tr for b in batches(chunk, a.batch, True, device)):
            prev = cmd_y.clamp(min=0).masked_fill(~mask, model.cfg.n_commands)     # earlier workers' true commands
            with torch.autocast("cuda", dtype=torch.bfloat16, enabled=device == "cuda"):
                pred = model(tiles, units, xy, mask, glob, prev, tgt_y.clamp(0, 100))
                loss, parts = loss_fn(pred, cmd_y, tgt_y, amt_y, legal, mask, cm, am)
                if base is not None:
                    with torch.no_grad():
                        base_cmd = base(tiles, units, xy, mask, glob, prev, tgt_y.clamp(0, 100))[0]
                    l_w, parts["disagree"] = disagree_cmd_loss(pred[0], base_cmd, cmd_y, legal, mask, cm, a.w_disagree)
                    l_plain, _ = disagree_cmd_loss(pred[0], base_cmd, cmd_y, legal, mask, cm, 1.0)
                    loss = loss - l_plain + l_w      # swap loss_fn's plain command term for the weighted one
                if cfg.market:
                    lm = (value_market_loss(pred[3], mu, mm) if a.value_market
                          else market_loss(pred[3], mu, mm, token_weight=tok_w))
                    loss = loss + a.w_market * lm
                    parts["market"] = float(lm.detach())
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            if sched.last_epoch + 1 < steps:  # chunked epochs can run a few batches more than estimated
                sched.step()
            run.append(parts)
        ev = evaluate(model, va, device, names)
        ev2 = evaluate(model, va2, device, names) if va2.files else {}
        rec = {"epoch": ep + 1, "seconds": round(time.perf_counter() - t),
               "train_cmd_loss": round(float(np.mean([p["cmd"] for p in run])), 4),
               "train_market_loss": round(float(np.mean([p.get("market", 0) for p in run])), 4), **ev,
               "analysis2": {k: ev2[k] for k in ("command_acc", "target_acc", "market") if k in ev2}}
        log.append(rec)
        print(json.dumps({"epoch": rec["epoch"], "seconds": rec["seconds"], "cmd_acc": round(rec["command_acc"], 4),
                          "cmd_acc_analysis2": round(rec["analysis2"].get("command_acc", 0), 4),
                          "market": rec["market"].get("_overall"), "market_analysis2": rec["analysis2"].get("market", {}).get("_overall")}), flush=True)
        if ev["command_acc"] > best:
            best = ev["command_acc"]
            save(model, out / "model.pt")
    (out / "report.json").write_text(json.dumps({"config": vars(a), "log": log, "best_command_acc": best}, indent=1))


if __name__ == "__main__":
    main()
