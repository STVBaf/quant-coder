<script setup>
import { ref, onMounted, watch, nextTick } from "vue";

import { listStrategies, getKline, sendChat } from "../api";
import { useBacktest } from "../stores/backtest";
import { echarts, UP, DOWN } from "../charts";

const bt = useBacktest();

// ---- left: strategy params ----
const code = ref("600519");
const strategies = ref([]);
const selected = ref(null);
const params = ref({});
const start = ref("");
const end = ref("");

function pick(s) {
  selected.value = s;
  params.value = { ...s.params };
}

async function runFromForm() {
  if (!selected.value) return;
  await bt.run({
    code: code.value.trim(),
    kind: selected.value.kind,
    params: params.value,
    start: start.value || undefined,
    end: end.value || undefined,
  });
}

// ---- center: chart ----
const chartEl = ref(null);
let chart = null;

async function redraw(res, meta) {
  if (!chart) return;
  const code6 = meta?.code || res.stock?.code;
  let bars = [];
  try {
    const k = await getKline(code6, { start: meta?.start, end: meta?.end });
    bars = k.bars;
  } catch { /* chart still renders equity curve alone */ }
  renderChart(res, bars);
}

watch(() => bt.result, (res) => res && redraw(res, bt.params));

function renderChart(res, bars) {
  const dates = bars.length ? bars.map((b) => b.date) : res.equity_curve.map((p) => p[0]);
  const candles = bars.map((b) => [b.open, b.close, b.low, b.high]);
  const eqMap = Object.fromEntries(res.equity_curve);
  const equity = dates.map((d) => eqMap[d] ?? null);

  const marks = res.trades.map((t) => ({
    name: t.action,
    coord: [t.date, bars.length ? t.price : eqMap[t.date]],
    value: t.action === "buy" ? "B" : "S",
    itemStyle: { color: t.action === "buy" ? UP : DOWN },
  }));

  chart.setOption({
    animation: false,
    axisPointer: { link: [{ xAxisIndex: "all" }] },
    tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
    grid: [
      { left: 52, right: 24, top: 16, height: "55%" },
      { left: 52, right: 24, top: "72%", bottom: 28 },
    ],
    xAxis: [
      { type: "category", data: dates, gridIndex: 0, axisLabel: { show: false } },
      { type: "category", data: dates, gridIndex: 1 },
    ],
    yAxis: [
      { scale: true, gridIndex: 0 },
      { scale: true, gridIndex: 1, name: "净值", splitNumber: 3 },
    ],
    dataZoom: [
      { type: "inside", xAxisIndex: [0, 1], start: 40, end: 100 },
      { type: "slider", xAxisIndex: [0, 1], start: 40, end: 100, height: 14, bottom: 8 },
    ],
    series: [
      {
        type: "candlestick",
        data: candles,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: { color: UP, color0: DOWN, borderColor: UP, borderColor0: DOWN },
        markPoint: {
          symbolSize: 26,
          label: { color: "#fff", fontSize: 10 },
          data: bars.length ? marks : [],
        },
      },
      {
        type: "line",
        name: "资金曲线",
        data: equity,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        smooth: true,
        connectNulls: true,
        lineStyle: { color: "#007AFF", width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(0,122,255,0.35)" },
            { offset: 1, color: "rgba(0,122,255,0)" },
          ]),
        },
      },
    ],
  }, true);
}

// ---- right: agent chat ----
const messages = ref([]);
const input = ref("");
const chatLoading = ref(false);
const convoId = ref(null);
const boxEl = ref(null);

const samples = [
  "用双均线回测茅台近三年，5日20日均线",
  "比较平安银行的 RSI 和布林带策略",
  "有哪些可用的回测策略？",
];

async function send(text) {
  const content = (text ?? input.value).trim();
  if (!content || chatLoading.value) return;
  input.value = "";
  messages.value.push({ role: "user", text: content });
  chatLoading.value = true;
  await scroll();
  try {
    const data = await sendChat({ conversation_id: convoId.value, message: content });
    convoId.value = data.conversation_id;
    messages.value.push({ role: "assistant", text: data.reply, trace: data.trace });
    syncChartFromTrace(data.trace);
  } catch (e) {
    const msg = e.response?.data?.error || "请求失败";
    messages.value.push({ role: "assistant", text: msg, error: true });
  } finally {
    chatLoading.value = false;
    await scroll();
  }
}

// The highlight: if the Agent ran a backtest, redraw the center chart. The
// trace result is only a metrics summary (kept lean to save tokens), so we
// re-run it through /backtest/run/ — bars are cached, so this is cheap and
// returns the full equity curve + trades the chart needs.
function syncChartFromTrace(trace) {
  const call = [...(trace || [])].reverse().find((t) => t.tool === "run_backtest" && !t.result?.error);
  if (!call) return;
  const inp = call.input;
  const years = inp.years || 2;
  const today = new Date();
  const startDate = new Date(today);
  startDate.setFullYear(today.getFullYear() - years);
  const fmt = (d) => d.toISOString().slice(0, 10);
  // Reflect the Agent's run in the left panel too, then run.
  code.value = inp.code;
  const s = strategies.value.find((x) => x.kind === inp.kind);
  if (s) {
    selected.value = s;
    params.value = { ...s.params, ...(inp.params || {}) };
  }
  start.value = fmt(startDate);
  end.value = fmt(today);
  bt.run({
    code: inp.code,
    kind: inp.kind,
    params: inp.params || undefined,
    start: start.value,
    end: end.value,
  });
}

async function scroll() {
  await nextTick();
  if (boxEl.value) boxEl.value.scrollTop = boxEl.value.scrollHeight;
}

onMounted(async () => {
  chart = echarts.init(chartEl.value, "okx");
  window.addEventListener("resize", () => chart?.resize());
  strategies.value = await listStrategies();
  pick(strategies.value[0]);
  if (bt.result) redraw(bt.result, bt.params);
});
</script>

<template>
  <div class="flex h-full">
    <!-- LEFT: strategy config (full-bleed panel) -->
    <aside class="flex w-72 shrink-0 flex-col border-r border-[#2B3139] bg-[#181A20]">
      <div class="flex items-center gap-2 border-b border-[#2B3139] p-4">
        <svg class="h-4 w-4 text-[#007AFF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <h2 class="text-sm font-semibold text-[#FAFAFA]">策略参数设置</h2>
      </div>

      <div class="flex-1 space-y-5 overflow-y-auto p-4">
        <div class="space-y-1.5">
          <label class="text-xs text-[#848E9C]">股票代码 / Stock Code</label>
          <input
            v-model="code"
            class="nums w-full rounded border border-[#2B3139] bg-[#0B0E11] p-2 text-sm outline-none transition focus:border-[#007AFF]"
          />
        </div>

        <div class="space-y-1.5">
          <label class="text-xs text-[#848E9C]">策略类型 / Strategy</label>
          <select
            class="w-full appearance-none rounded border border-[#2B3139] bg-[#0B0E11] p-2 text-sm text-[#FAFAFA] outline-none transition focus:border-[#007AFF]"
            :value="selected?.kind"
            @change="pick(strategies.find((s) => s.kind === $event.target.value))"
          >
            <option v-for="s in strategies" :key="s.kind" :value="s.kind">{{ s.name }}</option>
          </select>
        </div>

        <div class="flex gap-2">
          <div class="flex-1 space-y-1.5">
            <label class="text-xs text-[#848E9C]">起始 Start</label>
            <input v-model="start" type="date" class="nums w-full rounded border border-[#2B3139] bg-[#0B0E11] p-2 text-xs outline-none focus:border-[#007AFF]" />
          </div>
          <div class="flex-1 space-y-1.5">
            <label class="text-xs text-[#848E9C]">结束 End</label>
            <input v-model="end" type="date" class="nums w-full rounded border border-[#2B3139] bg-[#0B0E11] p-2 text-xs outline-none focus:border-[#007AFF]" />
          </div>
        </div>

        <div v-if="Object.keys(params).length" class="space-y-4 border-t border-[#2B3139] pt-4">
          <label class="block text-xs text-[#848E9C]">自定义参数 / Params</label>
          <div v-for="(v, key) in params" :key="key" class="flex items-center justify-between">
            <span class="text-sm text-[#FAFAFA]">{{ key }}</span>
            <input
              v-model.number="params[key]"
              type="number"
              step="any"
              class="nums w-16 rounded border border-[#2B3139] bg-[#0B0E11] p-1 text-center text-sm outline-none focus:border-[#007AFF]"
            />
          </div>
        </div>
      </div>

      <div class="border-t border-[#2B3139] p-4">
        <button
          class="w-full rounded bg-[#007AFF] py-2.5 font-medium text-white shadow-[0_0_15px_rgba(0,122,255,0.3)] transition hover:brightness-110 disabled:opacity-50"
          :disabled="bt.loading"
          @click="runFromForm"
        >
          {{ bt.loading ? "回测中…" : "运行回测 (Run)" }}
        </button>
        <p v-if="bt.error" class="mt-2 text-xs text-[#F6465D]">{{ bt.error }}</p>
      </div>
    </aside>

    <!-- CENTER: metrics + chart -->
    <section class="relative flex flex-1 flex-col overflow-hidden bg-[#0B0E11]">
      <div class="grid h-24 shrink-0 grid-cols-4 divide-x divide-[#2B3139] border-b border-[#2B3139] bg-[#181A20]">
        <div
          v-for="m in [
            { k: '累计收益', en: 'Total Return', v: bt.result?.metrics.total_return, pct: true, color: true },
            { k: '最大回撤', en: 'Max Drawdown', v: bt.result?.metrics.max_drawdown, pct: true, neg: true },
            { k: '夏普比率', en: 'Sharpe Ratio', v: bt.result?.metrics.sharpe },
            { k: '胜率', en: 'Win Rate', v: bt.result?.metrics.win_rate, pct: true },
          ]"
          :key="m.k"
          class="flex flex-col justify-center p-4"
        >
          <span class="mb-1 text-xs text-[#848E9C]">{{ m.k }} · {{ m.en }}</span>
          <span
            class="nums text-xl font-bold"
            :class="bt.result == null ? 'text-[#848E9C]'
              : m.neg ? 'text-[#0ECB81]'
              : m.color ? (m.v >= 0 ? 'text-[#F6465D]' : 'text-[#0ECB81]')
              : 'text-[#FAFAFA]'"
          >
            <template v-if="bt.result == null">—</template>
            <template v-else-if="m.pct">{{ m.v >= 0 && m.color ? "+" : "" }}{{ (m.v * 100).toFixed(2) }}%</template>
            <template v-else>{{ m.v }}</template>
          </span>
        </div>
      </div>

      <div class="relative flex-1 p-2">
        <div ref="chartEl" class="h-full w-full"></div>
        <div class="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.03]">
          <span class="text-9xl font-bold tracking-widest">QUANTDESK</span>
        </div>
        <div
          v-if="!bt.result && !bt.loading"
          class="pointer-events-none absolute inset-0 flex items-center justify-center text-sm text-[#848E9C]"
        >
          运行回测，或在右侧让 Agent 帮你跑一个
        </div>
      </div>
    </section>

    <!-- RIGHT: agent chat -->
    <aside class="flex w-80 shrink-0 flex-col border-l border-[#2B3139] bg-[#181A20]">
      <div class="flex items-center justify-between border-b border-[#2B3139] p-4">
        <h2 class="flex items-center text-sm font-semibold text-[#FAFAFA]">
          <svg class="mr-2 h-4 w-4 text-[#8A2BE2]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Quant Agent
        </h2>
        <span class="rounded border border-[#8A2BE2]/50 px-1.5 py-0.5 text-[10px] text-[#8A2BE2]">
          Claude
        </span>
      </div>

      <div ref="boxEl" class="flex-1 space-y-6 overflow-y-auto p-4">
        <!-- welcome -->
        <div class="flex items-start">
          <div class="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded bg-[#8A2BE2]">
            <svg class="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2zM9 21h6" />
            </svg>
          </div>
          <p class="ml-3 text-sm leading-relaxed text-[#848E9C]">
            您好，我是您的专属量化研究助理。用自然语言让我运行回测、查询指标或分析策略，结果会同步到中间图表。
          </p>
        </div>

        <div v-if="!messages.length" class="space-y-2 pl-9">
          <button
            v-for="s in samples"
            :key="s"
            class="block w-full rounded border border-[#2B3139] px-3 py-2 text-left text-xs text-[#848E9C] transition hover:border-[#8A2BE2]"
            @click="send(s)"
          >
            {{ s }}
          </button>
        </div>

        <!-- messages -->
        <template v-for="(m, i) in messages" :key="i">
          <!-- user -->
          <div v-if="m.role === 'user'" class="flex items-start justify-end">
            <div class="mr-3 max-w-[85%] rounded-lg rounded-tr-none bg-[#2B3139] px-3 py-2">
              <p class="text-sm text-[#FAFAFA]">{{ m.text }}</p>
            </div>
            <div class="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded bg-[#007AFF] text-xs font-bold text-white">
              U
            </div>
          </div>
          <!-- assistant -->
          <div v-else class="flex items-start">
            <div class="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded bg-[#8A2BE2]">
              <svg class="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div class="ml-3 w-full">
              <div v-if="m.trace && m.trace.length" class="glass mt-1 rounded-md border border-[#2B3139] p-2">
                <details open>
                  <summary class="flex cursor-pointer items-center font-mono text-xs text-[#8A2BE2]">
                    <svg class="mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M4 17h16a2 2 0 002-2V5a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    Tools 调用 ({{ m.trace.length }})
                  </summary>
                  <div v-for="(t, j) in m.trace" :key="j" class="mt-2 border-t border-[#2B3139]/50 pt-2">
                    <code class="nums text-[10px] text-[#8A2BE2]">{{ t.tool }}</code>
                    <pre class="nums mt-1 overflow-x-auto text-[10px] text-[#848E9C]">{{ JSON.stringify(t.input, null, 2) }}</pre>
                    <div class="mt-1 flex items-center text-[10px]">
                      <svg class="mr-1 h-3 w-3" :class="t.result?.error ? 'text-[#F6465D]' : 'text-[#0ECB81]'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      <span :class="t.result?.error ? 'text-[#F6465D]' : 'text-[#0ECB81]'">{{ t.result?.error ? "返回错误" : "返回成功" }}</span>
                    </div>
                  </div>
                </details>
              </div>
              <div
                class="mt-2 whitespace-pre-wrap text-sm leading-relaxed"
                :class="m.error ? 'text-[#F6465D]' : 'text-[#FAFAFA]'"
              >
                {{ m.text }}
              </div>
            </div>
          </div>
        </template>

        <div v-if="chatLoading" class="flex items-center pl-9 text-sm text-[#848E9C]">
          <span class="mr-2 h-1.5 w-1.5 animate-pulse rounded-full bg-[#8A2BE2]"></span>
          思考中…
        </div>
      </div>

      <div class="border-t border-[#2B3139] bg-[#0B0E11] p-3">
        <div class="flex items-center rounded-lg border border-[#2B3139] bg-[#181A20] px-2 transition focus-within:border-[#8A2BE2]">
          <input
            v-model="input"
            placeholder="输入自然语言指令…"
            class="w-full bg-transparent py-2.5 text-sm text-[#FAFAFA] outline-none placeholder:text-[#848E9C]"
            @keyup.enter="send()"
          />
          <button
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#848E9C] transition hover:bg-[#2B3139] hover:text-[#8A2BE2] disabled:opacity-40"
            :disabled="chatLoading"
            @click="send()"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </aside>
  </div>
</template>
