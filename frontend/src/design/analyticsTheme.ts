import type { AgChartOptions, AgChartTheme } from 'ag-charts-community';
import { colorSchemeDarkBlue, themeQuartz } from 'ag-grid-community';
import type { Theme } from '../context/theme';

// Canvas and SDK themes need resolved colors; keep their palette together here.
const lightPalette = ['#0066f5', '#0789ac', '#8195b1', '#173c71'];
const darkPalette = ['#6aafff', '#65d8ee', '#a9bfdc', '#397ee8'];
export function chartTheme(theme: Theme): AgChartTheme {
  const palette = theme === 'dark' ? darkPalette : lightPalette;
  return { baseTheme: theme === 'dark' ? 'ag-default-dark' : 'ag-default', palette: { fills: palette, strokes: palette }, overrides: { common: { background: { fill: theme === 'dark' ? '#111d30' : '#ffffff' } } } };
}
export function themedCharts(charts: AgChartOptions[], theme: Theme): AgChartOptions[] {
  return charts.map(chart => ({ ...chart, theme: chartTheme(theme) }));
}
export function gridTheme(theme: Theme) {
  return (theme === 'dark' ? themeQuartz.withPart(colorSchemeDarkBlue) : themeQuartz).withParams({ accentColor: theme === 'dark' ? darkPalette[0] : lightPalette[0], backgroundColor: theme === 'dark' ? '#111d30' : '#ffffff', foregroundColor: theme === 'dark' ? '#f5f8ff' : '#101828', headerBackgroundColor: theme === 'dark' ? '#15243a' : '#f1f5fb', borderColor: theme === 'dark' ? '#29405c' : '#e1e8f0', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 12, borderRadius: 12, rowHeight: 46, headerHeight: 44 });
}
