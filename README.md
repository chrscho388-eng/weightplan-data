# Weightplan-Daten (privat)

`weightplan.json` ist der Sync-Speicher der Weightplan-App. Schlüssel in `docs` sind relativ zum Nutzerbereich, z. B. `profile`, `profile/days/2026-10-27`, `profile/plans/2026-10-26`. Pro Dokument gewinnt der neueste `updatedAt`. Wer die Datei von Hand ändert, setzt `updatedAt` auf die aktuelle Zeit.

## Abgleich mit der claude.ai-Version

Die claude.ai-Version (Artifact) kann GitHub nicht selbst erreichen. Claude gleicht deshalb regelmäßig ab: ArtifactData-Export von `data/users/me` in einen Ordner, dann `python3 tools/bridge.py <ordner>`. Das Skript aktualisiert `weightplan.json` und legt unter `<ordner>/to_artifact/` die Dokumente ab, die in der Artifact-Datenbank neu geschrieben werden müssen.
