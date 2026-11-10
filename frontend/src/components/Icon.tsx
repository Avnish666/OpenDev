import type { CSSProperties } from 'react';
const paths = {
  arrow: 'M5 12h14m-6-6 6 6-6 6',
  sun: 'M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
  moon: 'M21 13a9 9 0 1 1-10-10 7 7 0 0 0 10 10Z',
  menu: 'M4 6h16M4 12h16M4 18h16', close: 'm6 6 12 12M6 18 18 6',
  code: 'm8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 16', check: 'm5 12 4 4L19 6',
  shield: 'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3Zm-4 9 3 3 5-6',
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z',
  search: 'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Zm-2 5 6 6',
  wallet: 'M4 7V5h14v3M4 8h16v12H4V8Zm11 4h5v4h-5v-4Z',
  timeline: 'M5 4v16M5 6h13M5 12h9M5 18h15M15 4v4M11 10v4M17 16v4',
  chart: 'M4 20V4m0 16h17M8 16v-5m5 5V7m5 9v-7',
  document: 'M6 3h9l4 4v14H6V3Zm9 0v5h4M9 12h7M9 16h5',
  github: 'M9 19c-4 1-4-2-6-2m12 5v-4c0-1-.2-1.5-.7-2 3.1-.4 6.4-1.5 6.4-7A5.5 5.5 0 0 0 19 5c.2-1 .2-2-.2-3 0 0-1.5-.5-4.1 1.5a14 14 0 0 0-7.4 0C4.7 1.5 3.2 2 3.2 2c-.4 1-.4 2-.2 3a5.5 5.5 0 0 0-1.7 4c0 5.5 3.3 6.6 6.4 7-.5.5-.7 1-.7 2v4',
} as const;
export default function Icon({ name, size = 20, style }: { name: keyof typeof paths; size?: number; style?: CSSProperties }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0, ...style }}><path d={paths[name]} /></svg>;
}
