import type { AgChartOptions, AgChartTheme } from 'ag-charts-community';
import { colorSchemeDarkBlue, themeQuartz } from 'ag-grid-community';
import type { Theme } from '../context/theme';

// Canvas and SDK themes need resolved colors; keep their palette together here.
const lightPalette = ['#1469e8', '#607f78', '#a69b86', '#535f6a'];
const darkPalette = ['#92bbf7', '#95b8a7', '#c6b99c', '#adb4bb'];
export function chartTheme(theme: Theme): AgChartTheme {
  const palette = theme === 'dark' ? darkPalette : lightPalette;
  return { baseTheme: theme === 'dark' ? 'ag-default-dark' : 'ag-default', palette: { fills: palette, strokes: palette }, params: { fontFamily: 'DM Sans' }, overrides: { common: { background: { fill: theme === 'dark' ? '#24282b' : '#ffffff' } } } };
}
export function themedCharts(charts: AgChartOptions[], theme: Theme): AgChartOptions[] {
  return charts.map(chart => ({ ...chart, theme: chartTheme(theme) }));
}
export function gridTheme(theme: Theme) {
  return (theme === 'dark' ? themeQuartz.withPart(colorSchemeDarkBlue) : themeQuartz).withParams({ accentColor: theme === 'dark' ? darkPalette[0] : lightPalette[0], backgroundColor: theme === 'dark' ? '#24282b' : '#ffffff', foregroundColor: theme === 'dark' ? '#eeeede' : '#20252b', headerBackgroundColor: theme === 'dark' ? '#2b2f31' : '#eeede8', borderColor: theme === 'dark' ? '#414647' : '#dedfd9', fontFamily: 'DM Sans, system-ui, sans-serif', fontSize: 12, borderRadius: 2, rowHeight: 46, headerHeight: 44 });
}
