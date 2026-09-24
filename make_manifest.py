# -*- coding: utf-8 -*-
"""Write MANIFEST.md: SHA-256 and size of every tracked file, plus the recorded checksums of inputs not included."""
import hashlib, json, os, subprocess, datetime
B = os.path.dirname(os.path.abspath(__file__))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
try: files = subprocess.check_output(["git", "ls-files"], cwd=B, text=True).split()
except Exception: files = [os.path.relpath(os.path.join(r, f), B) for r, _, fs in os.walk(B) for f in fs if ".git" not in r]
files = sorted(f for f in files if f != "MANIFEST.md")
L = json.load(open(os.path.join(B, "output_v2", "build_log.json")))
lines = ["# Manifest", "", f"Generated {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} by `make_manifest.py`.", "",
         "## Files in this repository", "", "| file | bytes | sha256 |", "|---|---|---|"]
lines += [f"| `{f}` | {os.path.getsize(os.path.join(B, f)):,} | `{sha(os.path.join(B, f))}` |" for f in files]
lines += ["", "## Inputs used by v1.4 that are not included (checksums recorded by build_v2.py)", "", "| file | sha256 |", "|---|---|"]
lines += [f"| `{k}` | `{v}` |" for k, v in L["inputs_sha256"].items()]
lines += ["", f"Reproduction check (rulebook GMP return vs floating-weight reconstruction): max abs diff {L['reproduction_max_abs_diff']:.1e}."]
open(os.path.join(B, "MANIFEST.md"), "w").write("\n".join(lines) + "\n"); print(len(files), "files")
