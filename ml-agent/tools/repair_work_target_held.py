"""Repair W1 ended-crop held-yield fields without replaying unchanged actions.
Original Parquet shards and a before/after hash ledger stay on D:.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from kagml.paths import data_root
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

ROOT=data_root()/"runs/work-targets-2026-10-18"
ENDED=("harvested","dug","removed","replaced")


def main():
    archive=ROOT/"doses-before-held-fix";archive.mkdir(exist_ok=True)
    changed=[];checked=0
    for path in sorted((ROOT/"doses").glob("*.parquet")):
        t=pq.read_table(path,use_threads=False)
        ended=pc.is_in(t["reason"],value_set=pa.array(ENDED))
        mask=pc.and_(ended,pc.not_equal(t["marginal_held"],0))
        n=pc.sum(pc.cast(mask,pa.int64())).as_py() or 0
        if n:
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            saved=archive/path.name
            if not saved.exists():shutil.copy2(path,saved)
            t=t.set_column(t.schema.get_field_index("marginal_held"),"marginal_held",pc.if_else(ended,0,t["marginal_held"]))
            temp=path.with_suffix(".tmp");pq.write_table(t,temp,compression="zstd");temp.replace(path)
            changed.append(dict(run=path.stem,rows=n,before_sha256=before,after_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        assert not pc.any(pc.greater(pc.add(t["marginal_harvest"],t["marginal_held"]),3)).as_py(),path
        checked+=t.num_rows
    ledger=dict(reason="An ended crop spell has no held output; framework step copies retained the pre-turn tile.",checked_rows=checked,corrected_rows=sum(x["rows"] for x in changed),shards=changed)
    # Preserve the first correction ledger on repeat invocations.
    target=ROOT/"held-correction.json"
    if changed or not target.exists():target.write_text(json.dumps(ledger,indent=2))
    print(json.dumps({k:v for k,v in ledger.items() if k!="shards"}))


if __name__=="__main__":main()
