#!/usr/bin/env python3
"""Ordnet die AssemblyAI-Sprecher (A, B, C) je Folge einem Namen zu und schreibt daten/sprecher.json.

Regeln aus kit.config.json, Abschnitt "sprecher", in dieser Reihenfolge:
1. einspieler: Wer nur Werbung oder Hinweise spricht (Wörter aus der Liste), heißt "Einspieler".
2. eroeffnung: Wer die Folge mit diesem Satz eröffnet, bekommt den Namen dazu.
3. Bei zwei Hosts bekommt der andere Hauptsprecher den zweiten Namen.
4. anrede: Klappt 2 nicht, gilt: Wer einen Host mit Namen anspricht, ist nicht dieser Host.
Alles Übrige heißt "Weitere Stimme". Bestehende Einträge in daten/sprecher.json bleiben, von Hand korrigieren geht dort.

    python3 scripts/sprecher.py              # Vorschlag anzeigen
    python3 scripts/sprecher.py --schreiben  # neue Folgen eintragen
    python3 scripts/sprecher.py --zeigen 617 # erste Sätze je Sprecher zum Prüfen
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
DATEN = WURZEL / "daten"


def zuordnen(t: dict, regeln: dict) -> dict[str, str]:
    namen: list[str] = regeln.get("namen", [])
    text: dict[str, str] = {}
    for z in t["absaetze"]:
        text[z["s"]] = text.get(z["s"], "") + " " + z["t"]
    worte = {s: len(x.split()) for s, x in text.items()}
    out: dict[str, str] = {}

    muster = regeln.get("einspieler", [])
    for s, x in text.items():
        if muster and worte[s] < 600 and any(m.lower() in x.lower() for m in muster):
            out[s] = "Einspieler"

    for name, satz in regeln.get("eroeffnung", {}).items():
        erster = next((z for z in t["absaetze"][:5] if satz.lower() in z["t"].lower()), None)
        if erster and erster["s"] not in out:
            out[erster["s"]] = name

    haupt = [s for s in sorted(worte, key=worte.get, reverse=True) if s not in out]
    offen = [n for n in namen if n not in out.values()]
    if len(namen) == 2 and len(offen) == 1 and haupt:
        out[haupt[0]] = offen[0]

    anrede: dict[str, list[str]] = regeln.get("anrede", {})
    for name in [n for n in namen if n not in out.values()]:
        rufen = {s: sum(len(re.findall(rf"\b{re.escape(w)}\b", text[s])) for w in anrede.get(name, [])) for s in haupt if s not in out}
        if len(rufen) >= 2:
            leise = min(rufen, key=rufen.get)
            if max(rufen.values()) >= 2 and rufen[leise] < max(rufen.values()):
                out[leise] = name

    for s in text:
        out.setdefault(s, "Weitere Stimme")
    return dict(sorted(out.items()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schreiben", action="store_true")
    ap.add_argument("--zeigen", type=int)
    args = ap.parse_args()
    regeln = json.loads((WURZEL / "kit.config.json").read_text(encoding="utf-8"))["sprecher"]
    ziel = DATEN / "sprecher.json"
    bestehend = json.loads(ziel.read_text(encoding="utf-8")) if ziel.exists() else {}
    neu = dict(bestehend)

    for pfad in sorted((DATEN / "transkripte").glob("*.json")):
        t = json.loads(pfad.read_text(encoding="utf-8"))
        nr = str(t["nummer"])
        vorschlag = zuordnen(t, regeln)
        worte: dict[str, int] = {}
        for z in t["absaetze"]:
            worte[z["s"]] = worte.get(z["s"], 0) + len(z["t"].split())
        print(f"#{nr}: " + ", ".join(f"{s}={n} ({worte[s]} Wörter)" for s, n in vorschlag.items()) + ("  [steht schon]" if nr in bestehend else ""))
        if args.zeigen == int(nr):
            for s in vorschlag:
                saetze = [z["t"][:160] for z in t["absaetze"] if z["s"] == s][:2]
                print(f"   {s}: " + " | ".join(saetze))
        neu.setdefault(nr, vorschlag)

    if args.schreiben:
        ziel.write_text(json.dumps(dict(sorted(neu.items(), key=lambda x: -int(x[0]))), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"geschrieben: {ziel.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
