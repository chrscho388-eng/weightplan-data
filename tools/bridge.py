"""Abgleich zwischen der claude.ai-Version (Artifact-Datenbank) und weightplan.json.

Aufruf: python3 tools/bridge.py <export_dir>
<export_dir> enthält den ArtifactData-Export (out_dir) von data/users/me:
  data/users/me/profile.json, data/users/me/profile/days/*.json, data/users/me/profile/plans/*.json
Pro Dokument gewinnt das neueste updatedAt. Das Skript aktualisiert weightplan.json und legt
alle Dokumente, die in der Artifact-Datenbank neu geschrieben werden müssen, unter
<export_dir>/to_artifact/<collection>/<doc_id>.json ab. Am Ende druckt es eine JSON-Zusammenfassung.
"""
import glob, json, os, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE = os.path.join(HERE, "weightplan.json")


def canon(d):
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def load_artifact(root):
    me = os.path.join(root, "data", "users", "me")
    docs = {}
    if os.path.exists(os.path.join(me, "profile.json")):
        docs["profile"] = json.load(open(os.path.join(me, "profile.json")))
    for sub in ("days", "plans"):
        for f in glob.glob(os.path.join(me, "profile", sub, "*.json")):
            docs[f"profile/{sub}/{os.path.basename(f)[:-5]}"] = json.load(open(f))
    return docs


def main(root):
    remote = json.load(open(FILE)) if os.path.exists(FILE) else {"app": "weightplan", "docs": {}}
    file_docs, art_docs = remote.get("docs", {}), load_artifact(root)
    merged, to_art, file_changed = {}, [], False
    for k in sorted(set(file_docs) | set(art_docs)):
        a, f = art_docs.get(k), file_docs.get(k)
        pick = f if a is None else a if f is None else (a if (a.get("updatedAt") or "") > (f.get("updatedAt") or "") else f)
        merged[k] = pick
        if f is None or canon(f) != canon(pick):
            file_changed = True
        if a is None or canon(a) != canon(pick):
            to_art.append(k)
    out = os.path.join(root, "to_artifact")
    writes = []
    for k in to_art:
        coll, doc_id = ("data/users/me", "profile") if k == "profile" else ("data/users/me/" + k.rsplit("/", 1)[0], k.rsplit("/", 1)[1])
        path = os.path.join(out, coll, doc_id + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(merged[k], open(path, "w"), ensure_ascii=False)
        writes.append({"collection": coll, "doc_id": doc_id, "file_path": path, "exists_in_artifact": k in art_docs})
    if file_changed:
        remote = {"app": "weightplan", "updatedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"), "docs": merged}
        json.dump(remote, open(FILE, "w"), ensure_ascii=False, indent=1)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import settings_md
    if settings_md.write(): file_changed = True
    print(json.dumps({"file_changed": file_changed, "artifact_writes": writes}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
