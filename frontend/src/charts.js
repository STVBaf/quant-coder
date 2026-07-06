import * as echarts from "echarts";

// 红涨绿跌 — keep in sync with --color-up / --color-down in main.css
export const UP = "#f6465d";
export const DOWN = "#0ecb81";
export const colorFor = (pct) => (pct >= 0 ? UP : DOWN);

// Register a dark theme that blends into the #0B0E11 background:
// transparent canvas, faint grid lines, dim axis labels.
echarts.registerTheme("okx", {
  backgroundColor: "transparent",
  textStyle: { color: "#848e9c" },
  title: { textStyle: { color: "#fafafa" } },
  legend: { textStyle: { color: "#848e9c" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#2b3139" } },
    axisLabel: { color: "#848e9c" },
    splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false },
    axisLabel: { color: "#848e9c" },
    splitLine: { lineStyle: { color: "rgba(255,255,255,0.05)" } },
  },
  tooltip: {
    backgroundColor: "#181a20",
    borderColor: "#2b3139",
    textStyle: { color: "#eaecef" },
  },
});

export { echarts };
