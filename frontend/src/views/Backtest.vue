<script setup>
import { ref, onMounted } from "vue";
import * as echarts from "echarts";

import { listStrategies, runBacktest } from "../api";

const code = ref("600519");
const strategies = ref([]);
const selected = ref(null);
const params = ref({});
const result = ref(null);
const loading = ref(false);
const error = ref("");
const chartEl = ref(null);
let chart = null;

function pick(s) {
  selected.value = s;
  params.value = { ...s.params };
}

async function run() {
  if (!selected.value) return;
  loading.value = true;
  error.value = "";
  try {
    result.value = await runBacktest({
      code: code.value.trim(),
      kind: selected.value.kind,
      params: params.value,
    });
    renderChart();
  } catch (e) {
    error.value = e.response?.data?.error || "回测失败";
  } finally {
    loading.value = false;
  }
}

function renderChart() {
  const r = result.value;
  const dates = r.equity_curve.map((p) => p[0]);
  const values = r.equity_curve.map((p) => p[1]);
  const marks = r.trades.map((t) => ({
    coord: [t.date, r.equity_curve.find((p) => p[0] === t.date)?.[1]],
    itemStyle: { color: t.action === "buy" ? "#ef4d56" : "#1bbf83" },
    value: t.action === "buy" ? "买" : "卖",
  }));
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 60, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: dates, axisLine: { lineStyle: { color: "#2a3344" } } },
    yAxis: { scale: true, splitLine: { lineStyle: { color: "#1a212e" } } },
    series: [
      {
        type: "line",
        data: values,
        showSymbol: false,
        lineStyle: { color: "#4ea1ff" },
        areaStyle: { color: "rgba(78,161,255,0.1)" },
        markPoint: { symbolSize: 36, data: marks, label: { color: "#fff", fontSize: 11 } },
      },
    ],
  });
}

onMounted(async () => {
  chart = echarts.init(chartEl.value);
  strategies.value = await listStrategies();
  pick(strategies.value[0]);
});
</script>

<template>
  <div>
    <h2>策略回测</h2>
    <div class="form">
      <input v-model="code" placeholder="股票代码" />
      <div class="kinds">
        <button
          v-for="s in strategies"
          :key="s.kind"
          :class="{ active: selected?.kind === s.kind }"
          @click="pick(s)"
        >
          {{ s.name }}
        </button>
      </div>
      <div class="params">
        <label v-for="(v, key) in params" :key="key">
          {{ key }}
          <input v-model.number="params[key]" type="number" step="any" />
        </label>
      </div>
      <button class="run" :disabled="loading" @click="run">
        {{ loading ? "回测中…" : "运行回测" }}
      </button>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="result" class="metrics">
      <div class="metric">
        <span>累计收益</span>
        <b :class="result.metrics.total_return >= 0 ? 'up' : 'down'">
          {{ (result.metrics.total_return * 100).toFixed(2) }}%
        </b>
      </div>
      <div class="metric">
        <span>最大回撤</span>
        <b class="down">{{ (result.metrics.max_drawdown * 100).toFixed(2) }}%</b>
      </div>
      <div class="metric">
        <span>夏普比率</span>
        <b>{{ result.metrics.sharpe }}</b>
      </div>
      <div class="metric">
        <span>胜率</span>
        <b>{{ (result.metrics.win_rate * 100).toFixed(1) }}%</b>
      </div>
    </div>

    <div ref="chartEl" class="chart" v-show="result"></div>
  </div>
</template>

<style scoped>
h2 {
  margin-bottom: 16px;
}
.form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
input {
  background: #0b0e14;
  border: 1px solid #2a3344;
  color: #d6dbe5;
  padding: 6px 10px;
  border-radius: 6px;
  width: 110px;
}
.kinds button {
  background: #11151f;
  border: 1px solid #2a3344;
  color: #9aa4b5;
  padding: 6px 14px;
  margin-right: 8px;
  border-radius: 6px;
  cursor: pointer;
}
.kinds button.active {
  border-color: #4ea1ff;
  color: #4ea1ff;
}
.params {
  display: flex;
  gap: 12px;
}
.params label {
  color: #7d8799;
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.params input {
  width: 80px;
}
.run {
  background: #4ea1ff;
  border: none;
  color: #06101f;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}
.error {
  color: #ef4d56;
}
.metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.metric {
  background: #11151f;
  border: 1px solid #1f2633;
  border-radius: 10px;
  padding: 14px 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.metric span {
  color: #7d8799;
  font-size: 13px;
}
.metric b {
  font-size: 20px;
}
.up {
  color: #ef4d56;
}
.down {
  color: #1bbf83;
}
.chart {
  width: 100%;
  height: 420px;
}
</style>
