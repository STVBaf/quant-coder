<script setup>
import { ref, watch, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";

import { getKline } from "../api";
import { echarts, UP, DOWN } from "../charts";

const route = useRoute();
const router = useRouter();
const chartEl = ref(null);
const stock = ref(null);
const last = ref(null);
const loading = ref(false);
const error = ref("");
let chart = null;

async function load(code) {
  loading.value = true;
  error.value = "";
  try {
    const data = await getKline(code);
    stock.value = data.stock;
    last.value = data.bars[data.bars.length - 1] || null;
    render(data.bars);
  } catch {
    error.value = "加载失败，请确认代码是否正确";
  } finally {
    loading.value = false;
  }
}

function render(bars) {
  const dates = bars.map((b) => b.date);
  const candles = bars.map((b) => [b.open, b.close, b.low, b.high]);
  const vols = bars.map((b) => ({
    value: b.volume,
    itemStyle: { color: b.close >= b.open ? UP : DOWN },
  }));
  chart.setOption({
    animation: false,
    axisPointer: { link: [{ xAxisIndex: "all" }] },
    tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
    grid: [
      { left: 56, right: 20, top: 16, height: "62%" },
      { left: 56, right: 20, top: "76%", bottom: 40 },
    ],
    xAxis: [
      { type: "category", data: dates, gridIndex: 0, axisLabel: { show: false } },
      { type: "category", data: dates, gridIndex: 1 },
    ],
    yAxis: [
      { scale: true, gridIndex: 0 },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false } },
    ],
    dataZoom: [
      { type: "inside", xAxisIndex: [0, 1], start: 55, end: 100 },
      { type: "slider", xAxisIndex: [0, 1], start: 55, end: 100, height: 16, bottom: 12 },
    ],
    series: [
      {
        type: "candlestick",
        data: candles,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: { color: UP, color0: DOWN, borderColor: UP, borderColor0: DOWN },
      },
      { type: "bar", data: vols, xAxisIndex: 1, yAxisIndex: 1 },
    ],
  }, true);
}

onMounted(() => {
  chart = echarts.init(chartEl.value, "okx");
  window.addEventListener("resize", () => chart?.resize());
  load(route.params.code);
});
onUnmounted(() => chart?.dispose());
watch(() => route.params.code, (code) => code && load(code));
</script>

<template>
  <div class="h-full space-y-4 overflow-y-auto p-6">
    <div class="flex items-center justify-between">
      <div v-if="stock">
        <span class="text-lg font-semibold text-[#FAFAFA]">{{ stock.name }}</span>
        <span class="nums ml-2 text-sm text-[#848E9C]">{{ stock.code }}</span>
      </div>
      <button
        v-if="stock"
        class="rounded-lg bg-[#007AFF] px-4 py-1.5 text-sm font-medium text-white transition hover:brightness-110"
        @click="router.push('/workspace')"
      >
        去回测此股 →
      </button>
    </div>

    <p v-if="error" class="text-sm text-[#F6465D]">{{ error }}</p>
    <p v-if="loading" class="text-sm text-[#848E9C]">加载中…</p>

    <div class="card p-4">
      <div ref="chartEl" class="h-[560px] w-full"></div>
    </div>
  </div>
</template>
