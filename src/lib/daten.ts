// Eine Datenquelle für alle Seiten: daten/folgen.json aus dem Feed (scripts/feed.py),
// daten/transkripte/<nr>.json von AssemblyAI (scripts/transkribiere.py),
// daten/sprecher.json ordnet A, B, C je Folge einem Namen zu (scripts/sprecher.py).
import konfig from '../../kit.config.json';
import folgenRoh from '../../daten/folgen.json';

export type Kapitel = { t: number; titel: string };
export type Absatz = { s: string; a: number; e: number; t: string };
export type Folge = {
  nummer: number;
  titel: string;
  datum: string;
  dauer: number;
  audio: string;
  beschreibung: string;
  kapitel: Kapitel[];
  slug: string;
};
export type Zeile = Absatz & { name: string; host: number };

const transkripte = import.meta.glob<{ default: { nummer: number; absaetze: Absatz[] } }>('../../daten/transkripte/*.json', { eager: true });
const sprecherDatei = import.meta.glob<{ default: Record<string, Record<string, string>> }>('../../daten/sprecher.json', { eager: true });
const sprecher: Record<string, Record<string, string>> = Object.values(sprecherDatei)[0]?.default ?? {};
const korrekturDatei = import.meta.glob<{ default: { ersetzen: [string, string][] } }>('../../daten/korrekturen.json', { eager: true });
const ersetzen: [string, string][] = Object.values(korrekturDatei)[0]?.default?.ersetzen ?? [];
const korrigiere = (t: string) => ersetzen.reduce((x, [falsch, richtig]) => x.split(falsch).join(richtig), t);

export const KONFIG = konfig as { name: string; kurzname: string; feed: string; website: string; indexieren?: boolean; sprecher: { namen: string[] } };
export const folgen: Folge[] = (folgenRoh as Folge[]).filter((f) => f.nummer);

export const BASE = import.meta.env.BASE_URL.endsWith('/') ? import.meta.env.BASE_URL : `${import.meta.env.BASE_URL}/`;
export const u = (pfad: string) => `${BASE}${pfad.replace(/^\//, '')}`;
export const folgenUrl = (f: Folge) => u(`folgen/${f.slug}/`);

export function transkript(f: Folge): Zeile[] {
  const roh = Object.entries(transkripte).find(([pfad]) => pfad.endsWith(`/${f.nummer}.json`))?.[1]?.default;
  if (!roh) return [];
  const namen = sprecher[String(f.nummer)] ?? {};
  const reihenfolge = KONFIG.sprecher.namen;
  return roh.absaetze.map((z) => {
    const name = namen[z.s] ?? `Sprecher ${z.s}`;
    const i = reihenfolge.indexOf(name);
    return { ...z, t: korrigiere(z.t), name, host: i >= 0 ? i : reihenfolge.length };
  });
}

// 3725 -> "1:02:05", 65 -> "1:05"
export function uhr(s: number) {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = Math.floor(s % 60);
  return (h ? `${h}:${String(m).padStart(2, '0')}` : `${m}`) + `:${String(x).padStart(2, '0')}`;
}
// Anker im Transkript: t-<Sekunden>. Die Suche liest die Sekunden direkt aus der ID.
export const anker = (s: number) => `t-${s}`;

export const datumDe = (iso: string) =>
  iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('de-DE', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
export const minuten = (s: number) => `${Math.round(s / 60)} Min`;
export const zahl = (n: number) => new Intl.NumberFormat('de-DE').format(n);
export const woerter = (t: string) => t.split(/\s+/).filter(Boolean).length;
