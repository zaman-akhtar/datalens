"""Build a smaller dev sample from a large CSV.
Usage:  python scripts/make_sample.py <input.csv> <n_rows>
Writes data/<input>_sample_<n>.csv next to the original.
"""
from __future__ import annotations
import sys
import random
from pathlib import Path

def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    n = int(sys.argv[2])
    out = Path("data") / f"{src.stem}_sample_{n}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with src.open() as f, out.open("w") as g:
        header = f.readline()
        g.write(header)
        rows = f.readlines()
    sample = random.sample(rows, min(n, len(rows)))
    with out.open("a") as g:
        g.writelines(sample)
    print(f"Wrote {len(sample)} rows to {out}")

if __name__ == "__main__":
    main()
