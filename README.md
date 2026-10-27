# Weightplan-Daten (privat)

`weightplan.json` ist der Sync-Speicher der Weightplan-App. Schlüssel in `docs` sind relativ zum Nutzerbereich, z. B. `profile`, `profile/days/2026-10-27`, `profile/plans/2026-10-26`. Pro Dokument gewinnt der neueste `updatedAt`. Wer die Datei von Hand ändert, setzt `updatedAt` auf die aktuelle Zeit.
