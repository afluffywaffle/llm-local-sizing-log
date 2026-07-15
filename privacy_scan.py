#!/usr/bin/env python3
"""Flag likely PII / secrets before you push a log or this repo.

Usage:
    python privacy_scan.py your_log.jsonl        # scan a log file
    python privacy_scan.py --repo .              # scan every text file in a dir

Heuristic, not a guarantee. It errs toward noise; read each hit. Exit code 1 if
anything flagged, 0 if clean — usable in a pre-commit / CI gate.
"""
import sys
import os
import re

PATTERNS = [
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("home path", re.compile(r"/(Users|home)/[A-Za-z0-9._-]+/")),
    ("api key-ish", re.compile(r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12,}|ghp_[A-Za-z0-9]{20,})")),
    ("bearer/secret", re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*\S+")),
    ("ip address", re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")),
    ("aws-ish", re.compile(r"(?i)aws_(access|secret)")),
]

# Words that read as personal-project specifics worth a human glance (extend per project).
SOFT = re.compile(r"(?i)\b(novelization|manuscript|invoice|salary|\$\d{3,})\b")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
TEXT_EXT = {".jsonl", ".json", ".md", ".py", ".txt", ".sh", ".yml", ".yaml", ".toml", ""}


def scan_file(path):
    hits = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for n, line in enumerate(f, 1):
                # Don't flag this scanner's own pattern-definition lines.
                if "re.compile(" in line or "SOFT = " in line:
                    continue
                for label, pat in PATTERNS:
                    for m in pat.findall(line):
                        frag = m if isinstance(m, str) else next((x for x in m if x), "")
                        hits.append((n, label, frag[:60]))
                for m in SOFT.findall(line):
                    hits.append((n, "soft/project-specific", str(m)[:60]))
    except (OSError, UnicodeError):
        pass
    return hits


def iter_files(root):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in TEXT_EXT:
                yield os.path.join(dp, fn)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    targets = []
    if sys.argv[1] == "--repo":
        root = sys.argv[2] if len(sys.argv) > 2 else "."
        targets = list(iter_files(root))
    else:
        targets = [sys.argv[1]]

    total = 0
    for path in targets:
        hits = scan_file(path)
        # Ignore matches that are clearly inside this scanner's own pattern list.
        hits = [h for h in hits if "privacy_scan.py" not in path or h[1] == "soft/project-specific"]
        if hits:
            print(f"\n{path}")
            for n, label, frag in hits:
                print(f"  L{n:<4} [{label}] {frag}")
            total += len(hits)
    print(f"\n{'FLAGGED ' + str(total) + ' item(s) — review before pushing.' if total else 'clean.'}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
