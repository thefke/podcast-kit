#!/usr/bin/env python3
"""Liest den RSS-Feed des Podcasts und schreibt daten/folgen.json.

Je Folge: Nummer, Titel, Datum, Dauer, Audio-URL, Beschreibung, Slug.
Nur Standardbibliothek, kein API-Schlüssel nötig.

    python3 scripts/feed.py              # alle Folgen
    python3 scripts/feed.py --neueste 10 # nur die zehn neuesten
"""
from __future__ import annotations

import argparse
import email.utils
import html
import json
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
      "content": "http://purl.org/rss/1.0/modules/content/"}


def konfig() -> dict:
    return json.loads((WURZEL / "kit.config.json").read_text(encoding="utf-8"))


def sekunden(wert: str | None) -> int:
    if not wert:
        return 0
    teile = [int(float(t)) for t in wert.strip().split(":")]
    s = 0
    for t in teile:
        s = s * 60 + t
    return s


def slug(text: str, laenge: int = 60) -> str:
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = text.replace("Ä", "ae").replace("Ö", "oe").replace("Ü", "ue")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:laenge].rstrip("-")


def nur_text(roh: str) -> str:
    roh = re.sub(r"<br\s*/?>|</p>", "\n", roh or "", flags=re.I)
    roh = re.sub(r"<[^>]+>", "", roh)
    roh = html.unescape(roh).replace("\u2060", "").replace("\u200b", "")
    return re.sub(r"\n{3,}", "\n\n", roh).strip()


KAPITEL = re.compile(r"^\(?(\d{1,2}:\d{2}(?::\d{2})?)\)?\s+(.+)$")


def kapitel(text: str) -> list[dict]:
    """Zeilen wie "(00:06:14) War Room" werden Kapitel mit Sekunden."""
    out = []
    for zeile in text.splitlines():
        m = KAPITEL.match(zeile.strip())
        if m:
            out.append({"t": sekunden(m.group(1)), "titel": m.group(2).strip()})
    return out if len(out) >= 2 else []


def kurz(text: str) -> str:
    """Erster Absatz der Beschreibung, ohne Werbung und Linklisten."""
    for absatz in text.split("\n\n"):
        absatz = absatz.strip()
        if len(absatz) > 60:
            return absatz
    return text[:400]


def nummer(titel: str, episode: str | None) -> int | None:
    if episode and episode.strip().isdigit():
        return int(episode)
    m = re.search(r"#\s?(\d{1,4})\b", titel)
    return int(m.group(1)) if m else None


def lies_feed(url: str) -> list[dict]:
    anfrage = urllib.request.Request(url, headers={"User-Agent": "podcast-kit/1.0"})
    with urllib.request.urlopen(anfrage, timeout=60) as antwort:
        wurzel = ET.fromstring(antwort.read())
    folgen = []
    for item in wurzel.iter("item"):
        titel = (item.findtext("title") or "").strip()
        enc = item.find("enclosure")
        if enc is None:
            continue
        nr = nummer(titel, item.findtext("itunes:episode", namespaces=NS))
        datum = item.findtext("pubDate")
        iso = email.utils.parsedate_to_datetime(datum).date().isoformat() if datum else ""
        beschreibung = item.findtext("content:encoded", namespaces=NS) or item.findtext("description") or ""
        titel_sauber = re.sub(r"\s*#\s?\d{1,4}\s*$", "", titel).strip()
        folgen.append({
            "nummer": nr,
            "titel": titel_sauber,
            "datum": iso,
            "dauer": sekunden(item.findtext("itunes:duration", namespaces=NS)),
            "audio": enc.get("url"),
            "guid": (item.findtext("guid") or "").strip(),
            "beschreibung": kurz(nur_text(beschreibung)),
            "kapitel": kapitel(nur_text(beschreibung)),
            "slug": f"{nr}-{slug(titel_sauber)}" if nr else slug(titel_sauber),
        })
    return folgen


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--neueste", type=int, default=0, help="nur die N neuesten Folgen")
    args = ap.parse_args()
    k = konfig()
    folgen = lies_feed(k["feed"])
    if args.neueste:
        folgen = folgen[: args.neueste]
    ziel = WURZEL / "daten" / "folgen.json"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(json.dumps(folgen, ensure_ascii=False, indent=1), encoding="utf-8")
    stunden = sum(f["dauer"] for f in folgen) / 3600
    print(f"{len(folgen)} Folgen, {stunden:.1f} Stunden Audio -> {ziel.relative_to(WURZEL)}")


if __name__ == "__main__":
    main()
