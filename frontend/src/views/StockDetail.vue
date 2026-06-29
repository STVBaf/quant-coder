<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import * as echarts from "echarts";

import { getKline } from "../api";

const route = useRoute();
const chartEl = ref(null);
const stock = ref(null);
const loading = ref(false);
const error = ref("");
let chart = null;

async function load(code) {
  loading.value = true;
  error.value = "";
  try {
    const data = await getKline(code);
    stock.value = data.stock;
    render(data.bars);
  } catch (e) {
    error.value = "加载失败，请确认代码是否正确";
  } finally {
    loading.value = false;
  }
}

function render(bars) {
  const dates = bars.map((b) => b.date);
  const candles = bars.map((b) => [b.open, b.close, b.low, b.high]);
  chart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
    grid: { left: 60, right: 20, top: 30, bottom: 60 },
    xAxis: { type: "category", data: dates, axisLine: { lineStyle: { color: "#2a3344" } } },
    yAxis: { scale: true, splitLine: { lineStyle: { color: "#1a212e" } } },
    dataZoom: [
      { type: "inside", start: 60, end: 100 },
      { type: "slider", start: 60, end: 100, height: 18, bottom: 20 },
    ],
    series: [
      {
        type: "candlestick",
        data: candles,
        itemStyle: {
          color: "#ef4d56",
          color0: "#1bbf83",
          borderColor: "#ef4d56",
          borderColor0: "#1bbf83",
        },
      },
    ],
  });
}

onMounted(() => {
  chart = echarts.init(chartEl.value);
  load(route.params.code);
});

onUnmounted(() => chart?.dispose());

watch(() => route.params.code, (code) => code && load(code));
</script>

<template>
  <div>
    <h2 v-if="stock">{{ stock.code }} {{ stock.name }}</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>
    <div ref="chartEl" class="chart"></div>
  </div>
</template>

<style scoped>
h2 {
  margin-bottom: 16px;
}
.error {
  color: #ef4d56;
}
.hint {
  color: #7d8799;
}
.chart {
  width: 100%;
  height: 520px;
}
</style>
