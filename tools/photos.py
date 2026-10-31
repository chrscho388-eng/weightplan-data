"""Fotos außerhalb der Dokumente: photos/<id>.jpg im Repo, im Dokument nur "photo:<id>".
id = FNV-1a 64 (hex, 16 Stellen) der data:-URL – dieselbe Rechnung wie in der App (kurs.html photoId)."""
import base64, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(HERE, "photos")
REF = "photo:"


def photo_id(s):
    h = 0xcbf29ce484222325
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return format(h, "016x")


def walk(v, f):
    if isinstance(v, list): return [walk(x, f) for x in v]
    if isinstance(v, dict): return {k: walk(x, f) for k, x in v.items()}
    if isinstance(v, str): return f(v)
    return v


def out(doc, seen=None):
    """Inline-Bilder als Dateien ablegen und durch Verweise ersetzen. seen sammelt id -> data-URL."""
    def f(x):
        if not x.startswith("data:image/"): return x
        pid = photo_id(x)
        if seen is not None: seen[pid] = x
        p = os.path.join(DIR, pid + ".jpg")
        if not os.path.exists(p):
            os.makedirs(DIR, exist_ok=True)
            open(p, "wb").write(base64.b64decode(x.split(",", 1)[1]))
        return REF + pid
    return walk(doc, f)


def back(doc, known):
    """Verweise, deren Bild bekannt ist (known: id -> data-URL), wieder inline einsetzen."""
    return walk(doc, lambda x: known.get(x[len(REF):], x) if x.startswith(REF) else x)


def file_for(x):
    """Pfad zur Bilddatei für einen Verweis, sonst None."""
    if isinstance(x, str) and x.startswith(REF):
        p = os.path.join(DIR, x[len(REF):] + ".jpg")
        return p if os.path.exists(p) else None
    return None


def merge_day(a, b):
    """Wie mergeDay in der App: Mahlzeiten einzeln, Löschungen über "removed"."""
    if not a or not b: return a or b
    nw, old = (b, a) if (b.get("updatedAt") or "") > (a.get("updatedAt") or "") else (a, b)
    removed = list(dict.fromkeys((old.get("removed") or []) + (nw.get("removed") or [])))[-100:]
    gone, have = set(removed), {m.get("id") for m in nw.get("meals") or []}
    olds = {m.get("id"): m for m in old.get("meals") or []}
    def keep_photo(m):  # eine Seite ohne Foto (z. B. gekürzt) löscht das Foto der anderen nicht
        o = olds.get(m.get("id"))
        if o and not m.get("photo") and not m.get("photos") and (o.get("photo") or o.get("photos")):
            m = {**m, **{k: o[k] for k in ("photo", "photos") if o.get(k)}}
        return m
    meals = [keep_photo(m) for m in nw.get("meals") or []] + [m for m in old.get("meals") or [] if m.get("id") not in have]
    meals = [m for m in meals if m.get("id") not in gone]
    res = {**nw, "meals": meals}
    if removed: res["removed"] = removed
    else: res.pop("removed", None)
    return res
