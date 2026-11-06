"""Verlust-Prüfung vor jedem Push: kein Eintrag darf aus weightplan.json verschwinden.

Aufruf: python3 tools/check_loss.py   (vergleicht die Arbeitsdatei mit origin/main)
Meldet Mahlzeiten (Tage), die im letzten gepushten Stand standen, jetzt fehlen und nicht in "removed" des Tages stehen,
sowie Tage, deren updatedAt älter geworden ist. Rückgabe 1 bei Fund: dann NICHT pushen, Chris melden.
"""
import json, subprocess, sys

old = json.loads(subprocess.run(["git", "show", "origin/main:weightplan.json"], capture_output=True, text=True, check=True).stdout)["docs"]
new = json.load(open("weightplan.json", encoding="utf8"))["docs"]
bad = []
for k, o in old.items():
    if not k.startswith("profile/days/"):
        continue
    n = new.get(k)
    if n is None:
        bad.append(f"{k}: Tag fehlt ganz")
        continue
    if (n.get("updatedAt") or "") < (o.get("updatedAt") or ""):
        bad.append(f"{k}: Stand wurde älter ({o.get('updatedAt')} -> {n.get('updatedAt')})")
    ids = {m.get("id") for m in n.get("meals", [])}
    gone = set(n.get("removed", [])) | set(o.get("removed", []))
    for m in o.get("meals", []):
        if m.get("id") not in ids and m.get("id") not in gone:
            bad.append(f"{k}: Eintrag verschwunden: {m.get('label')} ({m.get('kcal')} kcal)")
print("\n".join(bad) if bad else "OK: nichts verloren")
sys.exit(1 if bad else 0)
