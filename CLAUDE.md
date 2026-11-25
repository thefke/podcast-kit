# CLAUDE.md: podcast-kit

Anleitung für einen Coding-Agenten, der das Kit betreibt oder in eine bestehende Podcast-Website einbaut.

## Was das Kit ist

Statische Astro-Seite (Astro 5, Pagefind 1.5) mit drei Bausteinen, die zusammengehören:

1. **Daten**: `scripts/feed.py` liest den RSS-Feed, `scripts/transkribiere.py` holt Transkripte mit Sprechern von AssemblyAI, `scripts/sprecher.py` ordnet A, B, C den Hosts zu. Alles landet als JSON in `daten/`. Es gibt keine zweite Datenquelle.
2. **Seiten**: `src/lib/daten.ts` liest `daten/` beim Build. Folgenseite, Suche, Zahlen und die Endpunkte für VTT und Kapitel bauen nur darauf auf.
3. **Player und Suche im Browser**: `src/components/Player.astro` und das Skript in `src/pages/suche.astro`. Kein Framework, kein Server.

## Regeln, die halten müssen

- Jeder Transkript-Absatz ist ein `<li id="t-<Sekunden>">` innerhalb von `data-pagefind-body`. Die Suche liest die Sekunden aus der ID. Wer das Markup ändert, behält die ID.
- Zeitmarken im Transkript tragen `data-pagefind-ignore`, sonst stehen sie doppelt in den Suchtreffern.
- Abspielen geht nur über Elemente mit `data-play`, `data-play-src`, `data-play-titel`, `data-play-url` und optional `data-play-zeit` (Sekunden) und `data-play-kapitel` (JSON). Der Player fängt den Klick in der Capture-Phase ab.
- Der Player sitzt im Layout mit `transition:persist` und `<ClientRouter />`. Ohne den Router bricht das Weiterspielen beim Seitenwechsel ab.
- Seitenwechsel laufen ohne Neuladen. Neue Skripte deshalb delegiert an `document` hängen oder an `astro:page-load` und zusätzlich direkt aufrufen, mit Schutz gegen doppeltes Binden.
- Der Player meldet die Zeit als Ereignis `pk:zeit` (`{ id, t, laeuft }`). Die Folgenseite markiert damit Absatz und Kapitel.
- Pfade immer über `u()` aus `src/lib/daten.ts`, damit die Seite auch unter einem Unterpfad läuft (`BASE_PATH`).
- `npm run build` baut erst Astro, dann Pagefind. Im Dev-Server gibt es keinen Suchindex, die Suchseite sagt das.

## Einbau in eine bestehende Astro-Seite

1. `scripts/`, `daten/`, `kit.config.json` übernehmen, `pagefind` als Abhängigkeit, Build um `&& pagefind --site dist` ergänzen.
2. `src/lib/daten.ts` übernehmen. Gibt es schon eine Folgen-Collection, `transkript()` und `KONFIG` daraus nutzen und `folgen` durch die eigene Quelle ersetzen. Schlüssel ist die Folgennummer.
3. `Player.astro` ins Layout, `<ClientRouter />` in den Head.
4. Auf der bestehenden Folgenseite: `data-pagefind-body` um den Inhalt, das Transkript-Markup aus `src/pages/folgen/[slug]/index.astro` und das Mitlese-Skript darunter. Bestehende Kapitel-Links bekommen `data-play-zeit`.
5. `src/pages/suche.astro` übernehmen. Gibt es schon eine Suche über Titel und Beschreibungen, kann sie bleiben und bei leerem Ergebnis auf `/suche/?q=` verlinken.
6. Optional `zahlen.astro`, `transkript.vtt.ts`, `kapitel.json.ts`. Die URLs von VTT und Kapiteln können als `podcast:transcript` und `podcast:chapters` in den Feed.
7. Farben und Schriften aus `kit.css` durch die eigenen Variablen ersetzen.

## Laufender Betrieb

Neue Folge: `feed.py`, `transkribiere.py starten`, `transkribiere.py abholen --warten`, `sprecher.py --schreiben`, Build. Das lässt sich als GitHub Action nach jedem Feed-Update laufen lassen, den Schlüssel als Secret `ASSEMBLYAI_API_KEY`.

Prüfen nach jedem Umbau am Player oder Router: zweimal ohne Neuladen auf dieselbe Seite wechseln, Player und Suche müssen beim zweiten Besuch noch gehen. Ein Treffer in der Suche muss ab seiner Minute abspielen.

## Was nicht ins Repo gehört

Audiodateien, API-Schlüssel, `daten/auftraege.json` (offene AssemblyAI-Aufträge, steht in `.gitignore`).
