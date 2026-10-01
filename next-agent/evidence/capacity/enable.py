"""Generate a temporary direct-load agent with the capacity flags enabled."""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = (root / "agents/ours/v0.11.0-candidate/main.py").read_text()
for name in ("CAPACITY_SE_PLOT", "CAPACITY_GEESE", "CAPACITY_TOMATO"):
    marker = f"{name} = False"
    assert source.count(marker) == 1, marker
    source = source.replace(marker, f"{name} = True")
target = root / ".cache/capacity_agent_on.py"
target.parent.mkdir(exist_ok=True)
target.write_text(source)
print(target)
