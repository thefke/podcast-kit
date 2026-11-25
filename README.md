# podcast-kit

Eine statische Podcast-Website, auf der jedes gesprochene Wort durchsuchbar ist. Jeder Treffer führt zur Minute in der Folge, ein Klick spielt ab genau da.

Gebaut aus dem, was beim [HOTEL-PODCAST](https://www.hotel-podcast.com/de/suche/?q=Fachkr%C3%A4ftemangel) seit Oktober 2026 läuft. Hier als Demo mit den zehn neuesten Folgen des Doppelgänger Podcasts (#608 bis #617).

## Was drin ist

| Seite | Was sie kann |
|---|---|
| `/suche/` | Volltextsuche über alle Transkripte, Treffer mit Minute und Sprecher, Klick spielt ab der Stelle |
| `/folgen/<nr>-<titel>/` | Transkript mit Sprechern und Zeitmarken, Kapitel aus den Shownotes, Mitlesen beim Hören |
| `/zahlen/` | Archiv in Zahlen: Stunden, Wörter, Redeanteil je Host, je Folge |
| Player | bleibt beim Seitenwechsel stehen und spielt weiter, merkt sich die Position, Sperrbildschirm-Steuerung |
| `/folgen/<…>/transkript.vtt` | Transkript als WebVTT mit Sprechern, passt zum Feed-Tag `podcast:transcript` |
| `/folgen/<…>/kapitel.json` | Kapitel im Format Podcasting 2.0, passt zum Feed-Tag `podcast:chapters` |

Dazu `PodcastEpisode` als JSON-LD auf jeder Folgenseite, mit Link aufs Transkript.

Kein Server, keine Datenbank, kein Konto bei einem Dienst außer AssemblyAI für die Transkripte. Das Audio kommt direkt aus dem öffentlichen Feed.

## So läuft es

```bash
npm install
python3 scripts/feed.py                    # Feed lesen -> daten/folgen.json (mit --neueste 10 nur die neuesten)
export ASSEMBLYAI_API_KEY=...              # eigener Schlüssel von assemblyai.com
python3 scripts/transkribiere.py starten   # AssemblyAI holt das Audio selbst über die Feed-URL
python3 scripts/transkribiere.py abholen --warten
python3 scripts/sprecher.py --schreiben    # A, B, C -> Namen, Regeln in kit.config.json
npm run build                              # Seite nach dist/, danach baut Pagefind den Suchindex
npx astro preview                          # ansehen unter http://localhost:4321
```

Neue Folge: dieselben vier Schritte. `transkribiere.py` startet nur, was noch fehlt.

## Kosten

AssemblyAI rechnet nach Audiozeit: rund 0,21 $ je Stunde plus 0,02 $ für die Sprechertrennung, Stand November 2026, Preise bei AssemblyAI prüfen.

| Umfang | Stunden | Kosten |
|---|---|---|
| Diese Demo, 10 Folgen | 12,4 | rund 2,85 $ |
| Das ganze Archiv laut Feed, 619 Folgen | 862 | rund 198 $ einmalig |
| Eine neue Folge | etwa 1,1 | rund 0,25 $ |

Hosting ist statisch, also überall möglich: Netlify, Cloudflare Pages, GitHub Pages oder neben die bestehende Astro-Seite.

## Anpassen

- `kit.config.json`: Name, Feed, Fachbegriffe für die Transkription (`begriffe`), Hosts und wie sie erkannt werden.
- `src/styles/kit.css`: Farben und Schriften stehen oben als Variablen, der Rest leitet sich davon ab.
- `daten/sprecher.json`: Wer A, B, C je Folge ist. Von Hand korrigierbar, das Skript überschreibt bestehende Einträge nicht.
- `daten/korrekturen.json`: Hörfehler, die immer wieder vorkommen, etwa ein Name. Gilt beim Build für alle Folgen.
- `indexieren` in `kit.config.json`: `false` setzt `noindex` auf alle Seiten. Für eine echte Seite auf `true` stellen.

## In eine bestehende Astro-Seite einbauen

Siehe `CLAUDE.md`. Die Datei ist so geschrieben, dass ein Coding-Agent den Einbau allein machen kann.

## Grenzen

- Die Transkripte sind automatisch. Namen und Fachbegriffe gehen manchmal daneben, `begriffe` und `korrekturen.json` helfen.
- Die Sprechertrennung ist automatisch. Einzelne Absätze können beim falschen Sprecher landen, das schlägt auf den Redeanteil durch.
- Die Demo-Daten stammen aus dem öffentlichen Feed des Doppelgänger Podcasts und sind nur zur Vorschau da. Auf Zuruf nehmen wir sie raus.

## Lizenz

MIT, siehe `LICENSE`. Von Thomas Hefke.
