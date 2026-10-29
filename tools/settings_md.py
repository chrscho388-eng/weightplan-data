"""Schreibt EINSTELLUNGEN.md: lesbare Übersicht der aktuellen Einstellungen aus weightplan.json.
Wird von tools/bridge.py bei jedem Abgleich aufgerufen. Gibt True zurück, wenn sich die Datei geändert hat."""
import json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE, OUT = os.path.join(HERE, "weightplan.json"), os.path.join(HERE, "EINSTELLUNGEN.md")
num = lambda n, d=0: f"{n:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render(p, plans):
    L = ["# Weightplan: aktuelle Einstellungen", "", "Wird bei jedem Abgleich automatisch aus `weightplan.json` erzeugt. Ändern in der App (Plan-Tab und Profil) oder per Nachricht an Claude.", ""]
    L += ["## Ziele", f"- Start: {num(p.get('startWeight', 0), 1)} kg am {p.get('startWeightDate', '?')}",
          f"- Ziel: {num(p.get('goalWeight', 0), 1)} kg spätestens {p.get('goalDate', '?')}",
          f"- Pro Tag: {num(p.get('kcalTarget', 0))} kcal und {p.get('proteinTarget', '?')} g Eiweiß; Event-Tage frei (Rahmen {num(p.get('eventKcal', 0))} kcal)"]
    for m in p.get("milestones") or []:
        L.append(f"  - {m['date']}: {num(m['kg'], 1)} kg")
    L += ["", "## Dauerhafte Wünsche für alle Pläne"]
    rules = [r.strip() for r in (p.get("planRules") or "").splitlines() if r.strip()]
    L += [f"- {r}" for r in rules] or ["- (keine)"]
    L += ["", "## Hinweise für Schätzung und Plan (Profil)"]
    L += [f"- {r.strip()}" for r in (p.get("estimateHints") or "").splitlines() if r.strip()] or ["- (keine)"]
    if p.get("canteenHabits"):
        L += ["", "## Kantine (Bürotage)", f"- {p['canteenHabits']}"]
    menus = [k for k, v in sorted(plans.items()) if v.get("canteenMenu")]
    if menus:
        L.append("- Menü hochgeladen für: " + ", ".join(f"Woche ab {k}" for k in menus))
    c = p.get("coffee")
    if c:
        per = ", ".join(f"{k} {v}" for k, v in (c.get("perType") or {}).items())
        L += ["", "## Kaffee", f"- Cappuccino {c.get('kcal')} kcal / {c.get('protein')} g Eiweiß, automatisch eingetragen ab {c.get('since')} ({per})"]
        for typ, b in (c.get("byType") or {}).items():
            L.append(f"- {typ}: {b.get('label', 'Cappuccino')} mit {num(b.get('kcal', 0), 1)} kcal / {num(b.get('protein', 0), 1)} g Eiweiß pro Tasse")
    if p.get("stepGoals"):
        L += ["", "## Schrittziele"]
        for g in p["stepGoals"]:
            L.append(f"- ab {g['from']}: {num(g['steps'])} Schritte" + (f" (an lockeren Tagen mind. {num(g['min'])})" if g.get("min") else ""))
    if p.get("favorites"):
        L += ["", "## Favoriten"] + [f"- {f['label']}: {num(f['kcal'])} kcal, {f['protein']} g Eiweiß" for f in p["favorites"]]
    notes = p.get("planNotes") or {}
    if notes:
        L += ["", "## Hinweise pro Woche"] + [f"- Woche ab {k}: {v}" for k, v in sorted(notes.items())]
    open_req = [f"- Woche ab {k}: {v['planChange']}" for k, v in sorted(plans.items()) if v.get("planChange")]
    if open_req:
        L += ["", "## Offene Planänderungen"] + open_req
    return "\n".join(L) + "\n"


def write():
    docs = json.load(open(FILE)).get("docs", {})
    plans = {k.rsplit("/", 1)[1]: v for k, v in docs.items() if k.startswith("profile/plans/")}
    txt = render(docs.get("profile") or {}, plans)
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if txt != old:
        open(OUT, "w", encoding="utf-8").write(txt)
        return True
    return False


if __name__ == "__main__":
    print(write())
