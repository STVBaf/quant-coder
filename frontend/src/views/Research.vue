<script setup>
import { ref, computed, onUnmounted } from "vue";

import Textarea from "primevue/textarea";
import Button from "primevue/button";
import Chip from "primevue/chip";
import InputText from "primevue/inputtext";
import Tag from "primevue/tag";
import ProgressBar from "primevue/progressbar";

import { createResearch, getResearch } from "../api";
import { useToast } from "../stores/toast";

const toast = useToast();

// ---- form ----
const prompt = ref("");
const codeInput = ref("");
const codes = ref(["600519"]);
const samples = [
  "用双均线策略研究贵州茅台，找到夏普比率尽量高的参数组合",
  "研究宁德时代的动量策略，控制最大回撤在 20% 以内",
  "对比 RSI 与布林带在招商银行上的表现，给出更稳健的一个",
];

function addCode() {
  const c = codeInput.value.trim();
  if (c && !codes.value.includes(c)) codes.value.push(c);
  codeInput.value = "";
}
function removeCode(c) {
  codes.value = codes.value.filter((x) => x !== c);
}

// ---- task + polling ----
const task = ref(null);
const starting = ref(false);
let timer = null;

const running = computed(() =>
  task.value && ["pending", "running"].includes(task.value.status)
);

const statusMap = {
  pending: { label: "排队中", severity: "secondary" },
  running: { label: "研究中", severity: "info" },
  done: { label: "已完成", severity: "success" },
  failed: { label: "失败", severity: "danger" },
};

async function start() {
  if (!prompt.value.trim()) return toast.push("请填写研究目标", "error");
  if (!codes.value.length) return toast.push("请至少添加一个股票代码", "error");
  starting.value = true;
  try {
    const { id } = await createResearch({ prompt: prompt.value.trim(), codes: codes.value });
    poll(id);
    timer = setInterval(() => poll(id), 2500);
  } catch (e) {
    toast.push(e.response?.data?.error || "启动失败", "error");
  } finally {
    starting.value = false;
  }
}

async function poll(id) {
  try {
    task.value = await getResearch(id);
    if (!running.value) clearInterval(timer);
  } catch {
    clearInterval(timer);
  }
}

function reset() {
  clearInterval(timer);
  task.value = null;
}

onUnmounted(() => clearInterval(timer));

// ---- iteration helpers ----
const strategyRuns = computed(() =>
  (task.value?.iterations || []).filter((it) => it.kind === "run_strategy")
);

function metricsOf(it) {
  return it.payload?.result?.result?.metrics || null;
}
function okOf(it) {
  return it.payload?.result?.ok;
}
function pct(v) {
  return (v * 100).toFixed(2) + "%";
}
</script>

<template>
  <div class="flex h-full">
    <!-- LEFT: task setup -->
    <aside class="flex w-96 shrink-0 flex-col border-r border-[#2B3139] bg-[#181A20]">
      <div class="flex items-center gap-2 border-b border-[#2B3139] p-4">
        <i class="pi pi-sparkles text-[#8A2BE2]"></i>
        <h2 class="text-sm font-semibold text-[#FAFAFA]">自主研究 Agent</h2>
        <span class="ml-auto rounded border border-[#8A2BE2]/50 px-1.5 py-0.5 text-[10px] text-[#8A2BE2]">
          Claude · Sandbox
        </span>
      </div>

      <div class="flex-1 space-y-5 overflow-y-auto p-4">
        <div class="space-y-1.5">
          <label class="text-xs text-[#848E9C]">研究目标 / Research Goal</label>
          <Textarea v-model="prompt" rows="4" autoResize class="w-full text-sm"
            placeholder="用自然语言描述你想研究什么，例如：找到茅台夏普最高的双均线参数" />
        </div>

        <div class="space-y-1.5">
          <label class="text-xs text-[#848E9C]">标的代码 / Stock Codes</label>
          <div class="flex gap-2">
            <InputText v-model="codeInput" placeholder="如 600519" class="nums flex-1 text-sm"
              @keyup.enter="addCode" />
            <Button icon="pi pi-plus" severity="secondary" @click="addCode" />
          </div>
          <div class="flex flex-wrap gap-2 pt-1">
            <Chip v-for="c in codes" :key="c" :label="c" removable
              class="nums" @remove="removeCode(c)" />
          </div>
        </div>

        <div class="space-y-2 border-t border-[#2B3139] pt-4">
          <label class="text-xs text-[#848E9C]">试试这些 / Examples</label>
          <button v-for="s in samples" :key="s"
            class="block w-full rounded border border-[#2B3139] px-3 py-2 text-left text-xs text-[#848E9C] transition hover:border-[#8A2BE2]"
            @click="prompt = s">
            {{ s }}
          </button>
        </div>
      </div>

      <div class="space-y-2 border-t border-[#2B3139] p-4">
        <Button :label="running ? '研究进行中…' : '开始研究 (Run)'" icon="pi pi-play"
          class="w-full" :loading="starting || running" :disabled="running"
          @click="start" />
        <Button v-if="task && !running" label="新的研究" icon="pi pi-refresh"
          severity="secondary" outlined class="w-full" @click="reset" />
      </div>
    </aside>

    <!-- RIGHT: timeline -->
    <section class="relative flex flex-1 flex-col overflow-hidden bg-[#0B0E11]">
      <!-- empty state -->
      <div v-if="!task" class="flex flex-1 flex-col items-center justify-center text-center">
        <i class="pi pi-sitemap mb-4 text-5xl text-[#2B3139]"></i>
        <p class="text-sm text-[#848E9C]">左侧填写研究目标与标的，Agent 会自主写策略、<br />在沙箱里回测、诊断并迭代改进。</p>
      </div>

      <template v-else>
        <!-- header -->
        <div class="flex items-center gap-3 border-b border-[#2B3139] bg-[#181A20] px-6 py-3">
          <Tag :value="statusMap[task.status]?.label" :severity="statusMap[task.status]?.severity" />
          <span class="truncate text-sm text-[#FAFAFA]">{{ task.prompt }}</span>
          <span class="nums ml-auto shrink-0 text-xs text-[#848E9C]">
            {{ strategyRuns.length }} 次回测
          </span>
        </div>
        <ProgressBar v-if="running" mode="indeterminate" style="height: 2px" />

        <div class="flex-1 space-y-4 overflow-y-auto p-6">
          <!-- final report -->
          <div v-if="task.report"
            class="rounded-lg border border-[#8A2BE2]/40 bg-[#181A20] p-5">
            <div class="mb-2 flex items-center gap-2">
              <i class="pi pi-flag-fill text-[#8A2BE2]"></i>
              <h3 class="text-sm font-semibold text-[#FAFAFA]">研究结论</h3>
            </div>
            <div class="whitespace-pre-wrap text-sm leading-relaxed text-[#EAECEF]">{{ task.report }}</div>
          </div>
          <p v-if="task.error" class="rounded-lg border border-[#F6465D]/40 bg-[#181A20] p-4 text-sm text-[#F6465D]">
            {{ task.error }}
          </p>

          <!-- iteration timeline -->
          <div v-for="it in task.iterations" :key="it.seq" class="flex gap-3">
            <div class="flex flex-col items-center">
              <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border"
                :class="{
                  'border-[#8A2BE2] text-[#8A2BE2]': it.kind === 'thought',
                  'border-[#007AFF] text-[#007AFF]': it.kind === 'run_strategy',
                  'border-[#2B3139] text-[#848E9C]': it.kind === 'tool_call' || it.kind === 'status',
                }">
                <i :class="{
                  'pi pi-comment': it.kind === 'thought',
                  'pi pi-code': it.kind === 'run_strategy',
                  'pi pi-wrench': it.kind === 'tool_call',
                  'pi pi-info-circle': it.kind === 'status',
                }" style="font-size: 0.7rem"></i>
              </div>
              <div class="my-1 w-px flex-1 bg-[#2B3139]"></div>
            </div>

            <div class="flex-1 pb-2">
              <!-- thought -->
              <div v-if="it.kind === 'thought'" class="whitespace-pre-wrap text-sm leading-relaxed text-[#EAECEF]">
                {{ it.payload.text }}
              </div>
              <!-- tool_call -->
              <div v-else-if="it.kind === 'tool_call'" class="nums text-xs text-[#848E9C]">
                调用工具 <code class="text-[#8A2BE2]">{{ it.payload.name?.split("__").pop() }}</code>
              </div>
              <!-- status -->
              <div v-else-if="it.kind === 'status'" class="text-xs text-[#848E9C]">
                {{ it.payload.stage === 'materializing' ? '准备数据集…' : it.payload.stage }}
              </div>
              <!-- run_strategy -->
              <div v-else-if="it.kind === 'run_strategy'"
                class="rounded-lg border border-[#2B3139] bg-[#181A20] p-3">
                <pre class="nums mb-2 max-h-40 overflow-auto rounded bg-[#0B0E11] p-2 text-[11px] leading-relaxed text-[#848E9C]">{{ it.payload.code }}</pre>
                <div v-if="okOf(it) && metricsOf(it)" class="grid grid-cols-4 gap-2">
                  <div v-for="m in [
                    { k: '收益', v: metricsOf(it).total_return, pct: true, color: true },
                    { k: '回撤', v: metricsOf(it).max_drawdown, pct: true, down: true },
                    { k: '夏普', v: metricsOf(it).sharpe },
                    { k: '胜率', v: metricsOf(it).win_rate, pct: true },
                  ]" :key="m.k" class="rounded bg-[#0B0E11] p-2 text-center">
                    <div class="text-[10px] text-[#848E9C]">{{ m.k }}</div>
                    <div class="nums text-sm font-semibold"
                      :class="m.down ? 'text-[#0ECB81]' : m.color ? (m.v >= 0 ? 'text-[#F6465D]' : 'text-[#0ECB81]') : 'text-[#FAFAFA]'">
                      {{ m.pct ? pct(m.v) : m.v }}
                    </div>
                  </div>
                </div>
                <p v-else class="text-xs text-[#F6465D]">
                  执行出错：{{ it.payload.result?.error }}
                </p>
              </div>
            </div>
          </div>

          <div v-if="running" class="flex items-center pl-10 text-sm text-[#848E9C]">
            <span class="mr-2 h-1.5 w-1.5 animate-pulse rounded-full bg-[#8A2BE2]"></span>
            Agent 迭代中…
          </div>
        </div>
      </template>
    </section>
  </div>
</template>
