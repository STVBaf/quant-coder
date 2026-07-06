<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";

import { getOverview, getQuote } from "../api";
import { echarts, UP, DOWN, colorFor } from "../charts";
import CountUp from "../components/CountUp.vue";
import BreadthGauge from "../components/BreadthGauge.vue";

const indices = ref([]);
const breadth = ref({});
const sectors = ref([]);
const errors = ref([]);
const loading = ref(true);
const failed = ref(false);
const lastTick = ref("");
const heatmapEl = ref(null);
let heatmap = null;
let timer = null;
let sectorSig = ""; // signature of last-rendered sectors, to skip no-op redraws

const POLL_MS = 8000;
// Ticker tape: a few liquid names to show a live scrolling tape.
const TAPE = [
  { code: "600519", name: "贵州茅台" },
  { code: "000858", name: "五粮液" },
  { code: "300750", name: "宁德时代" },
  { code: "002594", name: "比亚迪" },
  { code: "600036", name: "招商银行" },
  { code: "601318", name: "中国平安" },
  { code: "000001", name: "平安银行" },
  { code: "600276", name: "恒瑞医药" },
];
const tape = ref(TAPE.map((t) => ({ ...t, price: 0, change_pct: 0 })));

const down = (k) => errors.value.includes(k);

async function loadOverview() {
  try {
    const data = await getOverview();
    indices.value = data.indices;
    breadth.value = data.breadth;
    sectors.value = data.sectors || [];
    errors.value = data.errors || [];
    if (sectors.value.length) renderHeatmap(sectors.value);
    lastTick.value = new Date().toLocaleTimeString("zh-CN", { hour12: false });
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

async function loadTape() {
  const results = await Promise.allSettled(TAPE.map((t) => getQuote(t.code)));
  results.forEach((r, i) => {
    if (r.status === "fulfilled" && r.value?.price != null) {
      tape.value[i] = { ...tape.value[i], ...r.value };
    }
  });
}

function poll() {
  loadOverview();
  loadTape();
}

function renderHeatmap(list) {
  // Only the 20 biggest movers (by |change|), so the treemap breathes instead
  // of cramming ~80 tiny industry tiles. Both leaders and laggards survive.
  const top = [...list]
    .sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct))
    .slice(0, 20);

  // Skip the redraw (and its animation) when polling returns identical data.
  const sig = top.map((s) => `${s.name}:${s.change_pct}`).join("|");
  if (sig === sectorSig) return;
  sectorSig = sig;

  heatmap.setOption({
    tooltip: {
      formatter: (p) =>
        `${p.name}<br/>涨跌幅 ${p.data.pct}%<br/>领涨 ${p.data.leader || "—"}`,
    },
    series: [
      {
        type: "treemap",
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        animationDurationUpdate: 600,
        label: { fontSize: 14, color: "#fff", formatter: "{b}" },
        itemStyle: { borderColor: "#0B0E11", borderWidth: 2, gapWidth: 2 },
        emphasis: { itemStyle: { borderColor: "#fff", borderWidth: 1 } },
        data: top.map((s) => ({
          name: s.name,
          value: s.turnover || Math.abs(s.change_pct) + 0.5,
          pct: s.change_pct,
          leader: s.leader,
          itemStyle: { color: colorFor(s.change_pct) },
        })),
      },
    ],
  });
}

onMounted(() => {
  heatmap = echarts.init(heatmapEl.value, "okx");
  window.addEventListener("resize", () => heatmap?.resize());
  poll();
  timer = setInterval(poll, POLL_MS);
});
onUnmounted(() => {
  clearInterval(timer);
  heatmap?.dispose();
});
</script>

<template>
  <div class="relative h-full overflow-y-auto">
    <!-- Backdrop FX -->
    <div class="pointer-events-none fixed inset-0 fx-grid"></div>
    <div class="pointer-events-none fixed inset-0 fx-glow"></div>

    <!-- Ticker tape -->
    <div class="relative overflow-hidden border-b border-[#2B3139] bg-[#0B0E11]/80 backdrop-blur">
      <div class="fx-marquee py-2">
        <template v-for="rep in 2" :key="rep">
          <span
            v-for="t in tape"
            :key="rep + t.code"
            class="mx-5 inline-flex items-baseline gap-2 text-sm"
          >
            <span class="text-[#848E9C]">{{ t.name }}</span>
            <span class="nums" :style="{ color: colorFor(t.change_pct) }">{{ t.price || "—" }}</span>
            <span class="nums text-xs" :style="{ color: colorFor(t.change_pct) }">
              {{ t.change_pct >= 0 ? "+" : "" }}{{ t.change_pct }}%
            </span>
          </span>
        </template>
      </div>
    </div>

    <div class="relative space-y-4 p-6">
      <div class="flex items-baseline justify-between">
        <h2 class="text-lg font-semibold tracking-wide text-[#FAFAFA]">大盘看板</h2>
        <span v-if="lastTick" class="flex items-center gap-2 text-xs text-[#848E9C]">
          <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-[#0ECB81]"></span>
          实时 · {{ lastTick }}
        </span>
      </div>

      <p v-if="failed" class="text-sm text-[#F6465D]">大盘数据加载失败，请确认后端已启动</p>

      <!-- Index cards -->
      <div v-if="down('indices')" class="card flex h-24 items-center justify-center text-sm text-[#848E9C]">
        指数数据源暂时离线
      </div>
      <div v-else class="grid grid-cols-3 gap-4">
        <div
          v-for="(idx, i) in indices"
          :key="idx.symbol"
          class="card card-glow fx-scanline fx-rise relative overflow-hidden p-5"
          :style="{ '--d': i * 90 + 'ms' }"
        >
          <div class="text-sm text-[#848E9C]">{{ idx.name }}</div>
          <CountUp
            :value="idx.close"
            class="mt-2 block text-3xl font-bold"
            :style="{ color: colorFor(idx.change_pct) }"
          />
          <div class="nums mt-1 text-sm" :style="{ color: colorFor(idx.change_pct) }">
            {{ idx.change_pct >= 0 ? "▲" : "▼" }}
            {{ idx.change_pct >= 0 ? "+" : "" }}{{ idx.change_pct }}%
          </div>
        </div>
      </div>

      <div class="grid grid-cols-[360px_1fr] gap-4">
        <!-- Breadth gauge -->
        <div class="card fx-rise p-5" style="--d: 280ms">
          <h3 class="mb-2 text-sm text-[#848E9C]">市场情绪 · 涨跌广度</h3>
          <template v-if="down('breadth')">
            <p class="text-sm text-[#848E9C]">涨跌分布数据源暂时离线</p>
          </template>
          <template v-else>
            <BreadthGauge :up="breadth['上涨'] || 0" :down="breadth['下跌'] || 0" />
            <div class="mt-3 flex justify-between text-sm">
              <span class="nums" :style="{ color: UP }">上涨 {{ breadth["上涨"] }}</span>
              <span class="nums" :style="{ color: DOWN }">下跌 {{ breadth["下跌"] }}</span>
            </div>
            <div class="mt-4 grid grid-cols-2 gap-3">
              <div class="rounded-lg bg-[#0B0E11] p-3">
                <div class="text-xs text-[#848E9C]">涨停</div>
                <div class="nums mt-1 text-xl font-semibold" :style="{ color: UP }">{{ breadth["涨停"] }}</div>
              </div>
              <div class="rounded-lg bg-[#0B0E11] p-3">
                <div class="text-xs text-[#848E9C]">跌停</div>
                <div class="nums mt-1 text-xl font-semibold" :style="{ color: DOWN }">{{ breadth["跌停"] }}</div>
              </div>
            </div>
          </template>
        </div>

        <!-- Treemap -->
        <div class="card fx-rise p-5" style="--d: 360ms">
          <h3 class="mb-3 text-sm text-[#848E9C]">行业板块热力图 · 涨跌幅前 20</h3>
          <p v-if="down('sectors')" class="flex h-[560px] items-center justify-center text-sm text-[#848E9C]">
            板块数据源暂时离线
          </p>
          <div v-show="!down('sectors')" ref="heatmapEl" class="h-[560px] w-full"></div>
        </div>
      </div>
    </div>
  </div>
</template>
