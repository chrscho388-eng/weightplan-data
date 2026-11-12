#!/usr/bin/env python3
"""Schneller Vorab-Check für den stündlichen Abgleich.

Pullt das Daten-Repo (main), prüft den Schalter autoSyncHourly und zählt
offene Anfragen. Ausgabe: "nichts neu" oder eine kurze Zusammenfassung.
Die Artifact-DB wird weiterhin im Ablauf geprüft (nur bei Bedarf).
"""
import json, os, subprocess, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*args):
    return subprocess.run(args, cwd=R, capture_output=True, text=True)


def find_flag(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for v in node.values():
            r = find_flag(v, key)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find_flag(v, key)
            if r is not None:
                return r
    return None


def main():
    fetch = run("git", "fetch", "-q", "origin", "main")
    if fetch.returncode != 0:
        print("FEHLER: git fetch", fetch.stderr.strip()[:200])
        return 1
    before = run("git", "rev-parse", "HEAD").stdout.strip()
    co = run("git", "checkout", "-q", "-B", "main", "origin/main")
    if co.returncode != 0:
        print("FEHLER: checkout", co.stderr.strip()[:200])
        return 1
    after = run("git", "rev-parse", "HEAD").stdout.strip()

    data = json.load(open(os.path.join(R, "weightplan.json"), encoding="utf-8"))
    auto = find_flag(data, "autoSyncHourly")

    req = run("python3", "tools/requests.py", "list", "/tmp/none")
    try:
        pending = json.loads(req.stdout)
        n_req = sum(len(pending.get(k, [])) for k in ("estimates", "recipes", "plans"))
    except (ValueError, AttributeError):
        print("FEHLER: requests.py lieferte keine Liste:", req.stderr.strip()[:200])
        return 1

    parts = []
    if auto is False:
        parts.append("Schalter autoSyncHourly AUS, Lauf beendet")
    if before != after:
        parts.append(f"Repo neu: {before[:7]} zu {after[:7]}")
    if n_req:
        parts.append(f"{n_req} offene Anfrage(n)")

    if not parts:
        print("nichts neu")
    else:
        print("ÄNDERUNG: " + "; ".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
