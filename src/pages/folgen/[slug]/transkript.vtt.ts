import type { APIRoute } from 'astro';
import { folgen, transkript, type Folge } from '../../../lib/daten';

// Transkript als WebVTT mit Sprechern (<v Name>), für Player, Barrierefreiheit und das Podcasting-2.0-Tag podcast:transcript.
export function getStaticPaths() {
  return folgen.filter((f) => transkript(f).length).map((f) => ({ params: { slug: f.slug }, props: { folge: f } }));
}
const vtt = (s: number) => {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), x = Math.floor(s % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}.000`;
};
export const GET: APIRoute = ({ props }) => {
  const zeilen = transkript((props as { folge: Folge }).folge);
  const text = ['WEBVTT', '', ...zeilen.map((z, i) => `${i + 1}\n${vtt(z.a)} --> ${vtt(Math.max(z.e, z.a + 1))}\n<v ${z.name}>${z.t}\n`)].join('\n');
  return new Response(text, { headers: { 'content-type': 'text/vtt; charset=utf-8' } });
};
