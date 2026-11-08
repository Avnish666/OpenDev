import type { AgChartOptions, AgChartTheme } from 'ag-charts-community';
import { colorSchemeDarkBlue, themeQuartz } from 'ag-grid-community';
import type { Theme } from '../context/theme';

// Canvas and SDK themes need resolved colors; keep their palette together here.
const palette = ['#0066f5', '#60cdff', '#7b8fac', '#003087'];
export function chartTheme(theme: Theme): AgChartTheme {
  return { baseTheme: theme === 'dark' ? 'ag-default-dark' : 'ag-default', palette: { fills: palette, strokes: palette }, overrides: { common: { background: { fill: theme === 'dark' ? '#111d2d' : '#ffffff' } } } };
}
export function themedCharts(charts: AgChartOptions[], theme: Theme): AgChartOptions[] {
  return charts.map(chart => ({ ...chart, theme: chartTheme(theme) }));
}
export function gridTheme(theme: Theme) {
  return (theme === 'dark' ? themeQuartz.withPart(colorSchemeDarkBlue) : themeQuartz).withParams({ accentColor: palette[0], fontFamily: 'Inter, system-ui, sans-serif', borderRadius: 12 });
}
