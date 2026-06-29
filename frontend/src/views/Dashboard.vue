<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";

import { getOverview } from "../api";

const router = useRouter();
const indices = ref([]);
const breadth = ref({});
const loading = ref(true);
const error = ref("");
const heatmapEl = ref(null);
let heatmap = null;

const UP = "#ef4d56";
const DOWN = "#1bbf83";

function colorFor(pct) {
  return pct >= 0 ? UP : DOWN;
}

async function load() {
  try {
    const data = await getOverview();
    indices.value = data.indices;
    breadth.value = data.breadth;
    renderHeatmap(data.sectors);
  } catch (e) {
    error.value = "大盘数据加载失败，请确认后端已启动";
  } finally {
    loading.value = false;
  }
}

function renderHeatmap(sectors) {
  const data = sectors.map((s) => ({
    name: s.name,
    value: Math.abs(s.change_pct) + 0.5, // size by magnitude
    itemStyle: { color: colorFor(s.change_pct) },
    label: { formatter: `${s.name}\n${s.change_pct}%` },
  }));
  heatmap.setOption({
    backgroundColor: "transparent",
    tooltip: {
      formatter: (p) => `${p.name}<br/>涨跌幅 ${p.data.raw}%`,
    },
    series: [
      {
        type: "treemap",
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: { fontSize: 12, color: "#fff" },
        data: data.map((d, i) => ({ ...d, raw: sectors[i].change_pct })),
      },
    ],
  });
}

onMounted(() => {
  heatmap = echarts.init(heatmapEl.value);
  load();
});

onUnmounted(() => heatmap?.dispose());
</script>

<template>
  <div>
    <h2>大盘看板</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>

    <div class="indices">
      <div v-for="idx in indices" :key="idx.symbol" class="idx-card">
        <div class="idx-name">{{ idx.name }}</div>
        <div class="idx-close" :style="{ color: colorFor(idx.change_pct) }">
          {{ idx.close }}
        </div>
        <div class="idx-chg" :style="{ color: colorFor(idx.change_pct) }">
          {{ idx.change_pct >= 0 ? "+" : "" }}{{ idx.change_pct }}%
        </div>
      </div>
    </div>

    <div class="breadth" v-if="breadth['上涨'] !== undefined">
      <span class="up">上涨 {{ breadth["上涨"] }}</span>
      <span class="down">下跌 {{ breadth["下跌"] }}</span>
      <span class="limit-up">涨停 {{ breadth["涨停"] }}</span>
      <span class="limit-down">跌停 {{ breadth["跌停"] }}</span>
    </div>

    <h3>行业板块热力图</h3>
    <div ref="heatmapEl" class="heatmap"></div>
  </div>
</template>

<style scoped>
h2 {
  margin-bottom: 16px;
}
h3 {
  margin: 28px 0 12px;
  color: #9aa4b5;
  font-size: 15px;
}
.error {
  color: #ef4d56;
}
.hint {
  color: #7d8799;
}
.indices {
  display: flex;
  gap: 16px;
}
.idx-card {
  background: #11151f;
  border: 1px solid #1f2633;
  border-radius: 10px;
  padding: 16px 28px;
  min-width: 150px;
}
.idx-name {
  color: #9aa4b5;
  font-size: 13px;
}
.idx-close {
  font-size: 24px;
  font-weight: 600;
  margin: 6px 0;
}
.idx-chg {
  font-size: 14px;
}
.breadth {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  font-size: 14px;
}
.up,
.limit-up {
  color: #ef4d56;
}
.down,
.limit-down {
  color: #1bbf83;
}
.heatmap {
  width: 100%;
  height: 460px;
}
</style>
