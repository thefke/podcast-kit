#!/usr/bin/env python3
"""Transkribiert Folgen aus daten/folgen.json mit AssemblyAI, mit Sprechern und Wortzeiten.

AssemblyAI holt das Audio selbst über die URL aus dem Feed, hier wird nichts heruntergeladen.
Kosten laut AssemblyAI-Preisliste: rund 0,21 $ je Stunde plus 0,02 $ für die Sprechertrennung.

    export ASSEMBLYAI_API_KEY=...        # eigener Schlüssel
    python3 scripts/transkribiere.py starten          # Aufträge für alle Folgen ohne Transkript
    python3 scripts/transkribiere.py abholen          # fertige Transkripte nach daten/transkripte/
    python3 scripts/transkribiere.py starten --nur 617 616

Ergebnis je Folge: daten/transkripte/<nummer>.json mit Absätzen (Sprecher, Start, Ende, Text).
Offene Aufträge merkt sich daten/auftraege.json, ein zweiter Lauf startet nichts doppelt.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
DATEN = WURZEL / "daten"
ZIEL = DATEN / "transkripte"
AUFTRAEGE = DATEN / "auftraege.json"


def konfig() -> dict:
    return json.loads((WURZEL / "kit.config.json").read_text(encoding="utf-8"))


def anfrage(methode: str, url: str, daten: dict | None = None) -> dict:
    schluessel = os.environ.get("ASSEMBLYAI_API_KEY")
    if not schluessel:
        sys.exit("ASSEMBLYAI_API_KEY fehlt.")
    koerper = json.dumps(daten).encode() if daten is not None else None
    req = urllib.request.Request(url, data=koerper, method=methode,
                                 headers={"authorization": schluessel, "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as antwort:
            return json.loads(antwort.read())
    except urllib.error.HTTPError as fehler:
        sys.exit(f"AssemblyAI {fehler.code}: {fehler.read()[:300]!r}")


def lade(pfad: Path, leer):
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else leer


def starten(nur: list[int]) -> None:
    k = konfig()
    folgen = lade(DATEN / "folgen.json", [])
    auftraege = lade(AUFTRAEGE, {})
    ZIEL.mkdir(parents=True, exist_ok=True)
    neu = 0
    for f in folgen:
        nr = str(f["nummer"])
        if nur and f["nummer"] not in nur:
            continue
        if (ZIEL / f"{nr}.json").exists() or nr in auftraege:
            continue
        auftrag = {
            "audio_url": f["audio"],
            "speech_models": [k.get("assemblyai_modell", "universal-3-5-pro")],
            "language_code": k.get("sprache", "de"),
            "speaker_labels": True,
            "keyterms_prompt": k.get("begriffe", [])[:100],
        }
        antwort = anfrage("POST", f"{k['assemblyai_api']}/transcript", auftrag)
        auftraege[nr] = antwort["id"]
        neu += 1
        print(f"#{nr} gestartet: {antwort['id']}")
    AUFTRAEGE.write_text(json.dumps(auftraege, indent=1), encoding="utf-8")
    print(f"{neu} neue Aufträge, {len(auftraege)} offen")


def absaetze(t: dict) -> list[dict]:
    """Ein Absatz je Sprecherwechsel, lange Strecken alle rund 45 Sekunden an einem Satzende geteilt."""
    ergebnis = []
    for u in t.get("utterances") or []:
        woerter = u.get("words") or []
        stueck, start = [], None
        for w in woerter:
            if start is None:
                start = w["start"]
            stueck.append(w["text"])
            satzende = w["text"].endswith((".", "?", "!"))
            if satzende and w["end"] - start > 45000:
                ergebnis.append({"s": u["speaker"], "a": start // 1000, "e": w["end"] // 1000, "t": " ".join(stueck)})
                stueck, start = [], None
        if stueck:
            ergebnis.append({"s": u["speaker"], "a": start // 1000, "e": woerter[-1]["end"] // 1000, "t": " ".join(stueck)})
    return ergebnis


def abholen(warten: bool) -> None:
    k = konfig()
    auftraege = lade(AUFTRAEGE, {})
    while auftraege:
        for nr, tid in list(auftraege.items()):
            t = anfrage("GET", f"{k['assemblyai_api']}/transcript/{tid}")
            if t["status"] == "completed":
                daten = {"nummer": int(nr), "id": tid, "dauer": int(t.get("audio_duration") or 0),
                         "sprecher": sorted({u["speaker"] for u in t.get("utterances") or []}),
                         "absaetze": absaetze(t)}
                (ZIEL / f"{nr}.json").write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
                del auftraege[nr]
                print(f"#{nr} fertig, {len(daten['absaetze'])} Absätze")
            elif t["status"] == "error":
                print(f"#{nr} Fehler: {t.get('error')}")
                del auftraege[nr]
        AUFTRAEGE.write_text(json.dumps(auftraege, indent=1), encoding="utf-8")
        if not warten or not auftraege:
            break
        print(f"{len(auftraege)} laufen noch, nächster Blick in 30 s")
        time.sleep(30)
    print("offen:", len(auftraege))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("schritt", choices=["starten", "abholen"])
    ap.add_argument("--nur", type=int, nargs="*", default=[], help="nur diese Folgennummern")
    ap.add_argument("--warten", action="store_true", help="beim Abholen warten, bis alles fertig ist")
    args = ap.parse_args()
    if args.schritt == "starten":
        starten(args.nur)
    else:
        abholen(args.warten)


if __name__ == "__main__":
    main()
