"""Offene Anfragen aus der App (Schätzung, neue Rezepte und Rezeptänderungen: bei "change" das Rezept "current" nach dem Wunsch anpassen), die Claude beim Abgleich beantwortet.

python3 tools/requests.py list <ordner>
    Druckt alle offenen Anfragen als JSON und legt Fotos als <ordner>/<ref>.jpg ab.
python3 tools/requests.py apply <antworten.json>
    Schreibt die Antworten in weightplan.json (mit updatedAt). Format:
    {"estimates": {"<tag>|<meal-id>": {"label","kcal","protein","seen","parts":[{name,grams,kcal,protein}]}},
     "recipes": {"<plan-montag>|d<tag>:<i> oder s:<i>": {"servings","minutes","ingredients":[{amount,item}],"steps":[],"tip"}},
     "plans": {"<plan-montag>": {"note","days":[...],"swaps":[...]}}}  (Planänderung nach "wish"; Rezepte gleichnamiger Gerichte bleiben erhalten;
     bei "menu_file" das Kantinen-Menü im Bild für die Bürotage auswerten, Kantinen-Gewohnheiten in profile.canteenHabits)
Danach tools/bridge.py laufen lassen, damit die claude.ai-Version die Antworten auch bekommt.
"""
import base64, json, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(HERE, "weightplan.json")
now = lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def list_requests(out):
    docs = json.load(open(FILE))["docs"]
    os.makedirs(out, exist_ok=True)
    res = {"estimates": [], "recipes": [], "plans": []}
    for k, d in docs.items():
        if k.startswith("profile/days/"):
            for m in d.get("meals", []):
                if m.get("pending"):
                    ref = k.rsplit("/", 1)[1] + "|" + m["id"]
                    item = {"ref": ref, "text": m.get("request") or m.get("label", "")}
                    if m.get("photo", "").startswith("data:image"):
                        p = os.path.join(out, ref.replace("|", "_") + ".jpg")
                        open(p, "wb").write(base64.b64decode(m["photo"].split(",", 1)[1]))
                        item["photo_file"] = p
                    res["estimates"].append(item)
        if k.startswith("profile/plans/"):
            mon = k.rsplit("/", 1)[1]
            if d.get("planChange"):
                cur = {kk: d.get(kk) for kk in ("note", "days", "swaps") if d.get(kk) is not None}
                item = {"ref": mon, "wish": d["planChange"], "current": cur}
                if d.get("canteenMenu", "").startswith("data:image"):  # Kantinen-Menü der Woche als Bild
                    p = os.path.join(out, mon + "_kantine.jpg")
                    open(p, "wb").write(base64.b64decode(d["canteenMenu"].split(",", 1)[1]))
                    item["menu_file"] = p
                res["plans"].append(item)
            for di, day in enumerate(d.get("days", [])):
                for mi, m in enumerate(day.get("meals", [])):
                    if (m.get("recipeRequested") and not m.get("recipe")) or m.get("recipeChange"):
                        res["recipes"].append({"ref": f"{mon}|d{di}:{mi}", "name": m.get("name"), "detail": m.get("detail"), "kcal": m.get("kcal"), "protein": m.get("protein"), "change": m.get("recipeChange"), "current": m.get("recipe") if m.get("recipeChange") else None})
            for si, m in enumerate(d.get("swaps", [])):
                if (m.get("recipeRequested") and not m.get("recipe")) or m.get("recipeChange"):
                    res["recipes"].append({"ref": f"{mon}|s:{si}", "name": m.get("name"), "detail": m.get("detail"), "kcal": m.get("kcal"), "protein": m.get("protein"), "change": m.get("recipeChange"), "current": m.get("recipe") if m.get("recipeChange") else None})
    print(json.dumps(res, ensure_ascii=False, indent=1))


def apply(path):
    ans = json.load(open(path))
    f = json.load(open(FILE)); docs = f["docs"]; t = now()
    for ref, e in ans.get("estimates", {}).items():
        day, mid = ref.split("|")
        d = docs.get("profile/days/" + day)
        for m in (d or {}).get("meals", []):
            if m.get("id") == mid and m.get("pending"):
                m.update(label=e["label"], kcal=round(e["kcal"]), protein=round(e["protein"]))
                if e.get("seen"): m["seen"] = e["seen"]
                if e.get("parts"): m["parts"] = e["parts"]
                m.pop("pending", None); m.pop("request", None)
                d["updatedAt"] = t
    for ref, r in ans.get("recipes", {}).items():
        mon, pos = ref.split("|")
        p = docs.get("profile/plans/" + mon)
        if not p: continue
        if pos.startswith("s:"):
            m = p["swaps"][int(pos[2:])]
        else:
            di, mi = pos[1:].split(":"); m = p["days"][int(di)]["meals"][int(mi)]
        m["recipe"] = r; m.pop("recipeRequested", None); m.pop("recipeChange", None); p["updatedAt"] = t
    for mon, np in ans.get("plans", {}).items():
        p = docs.get("profile/plans/" + mon) or {}
        known = {m.get("name"): m["recipe"] for m in [x for d in p.get("days", []) for x in d.get("meals", [])] + p.get("swaps", []) if m.get("recipe")}
        for m in [x for d in np.get("days", []) for x in d.get("meals", [])] + np.get("swaps", []):
            if not m.get("recipe") and m.get("name") in known: m["recipe"] = known[m["name"]]
        wish = p.get("planChange")
        p = {**{k: v for k, v in p.items() if k not in ("days", "swaps", "note", "planChange")}, **np, "updatedAt": t}
        if wish: p["lastWish"] = wish[:300]
        docs["profile/plans/" + mon] = p
    f["updatedAt"] = t
    json.dump(f, open(FILE, "w"), ensure_ascii=False, indent=1)
    print("ok")


if __name__ == "__main__":
    (list_requests if sys.argv[1] == "list" else apply)(sys.argv[2])
