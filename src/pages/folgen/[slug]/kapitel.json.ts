import type { APIRoute } from 'astro';
import { folgen, type Folge } from '../../../lib/daten';

// Kapitel im Format Podcasting 2.0 (JSON Chapters 1.2.0), für das Tag podcast:chapters im Feed.
export function getStaticPaths() {
  return folgen.filter((f) => f.kapitel.length).map((f) => ({ params: { slug: f.slug }, props: { folge: f } }));
}
export const GET: APIRoute = ({ props }) => {
  const f = (props as { folge: Folge }).folge;
  const daten = { version: '1.2.0', chapters: f.kapitel.map((k) => ({ startTime: k.t, title: k.titel })) };
  return new Response(JSON.stringify(daten, null, 1), { headers: { 'content-type': 'application/json+chapters; charset=utf-8' } });
};
