<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

import { getHistory } from "../api";
import { useBacktest } from "../stores/backtest";

const router = useRouter();
const bt = useBacktest();
const runs = ref([]);
const error = ref("");

const pct = (v) => (v * 100).toFixed(2) + "%";

async function rerun(r) {
  await bt.run({ code: r.code, kind: r.kind, start: r.start, end: r.end });
  router.push("/workspace");
}

onMounted(async () => {
  try {
    runs.value = await getHistory();
  } catch {
    error.value = "请先登录后查看历史";
  }
});
</script>

<template>
  <div class="h-full space-y-4 overflow-y-auto p-6">
    <h2 class="text-lg font-semibold text-[#FAFAFA]">回测历史</h2>
    <p v-if="error" class="text-sm text-[#F6465D]">{{ error }}</p>
    <p v-else-if="!runs.length" class="text-sm text-[#848E9C]">暂无历史，去工作台跑一个吧</p>

    <div v-if="runs.length" class="card overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[#2B3139] bg-[#0B0E11] text-left text-xs text-[#848E9C]">
            <th class="px-4 py-3 font-medium">执行时间</th>
            <th class="px-4 py-3 font-medium">标的</th>
            <th class="px-4 py-3 font-medium">策略</th>
            <th class="px-4 py-3 font-medium">区间</th>
            <th class="px-4 py-3 text-right font-medium">累计收益</th>
            <th class="px-4 py-3 text-right font-medium">最大回撤</th>
            <th class="px-4 py-3 text-right font-medium">夏普</th>
            <th class="px-4 py-3 text-right font-medium">胜率</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in runs"
            :key="r.id"
            class="border-b border-[#2B3139]/50 transition hover:bg-[#2B3139]/30"
          >
            <td class="nums px-4 py-3 text-xs text-[#848E9C]">
              {{ new Date(r.created_at).toLocaleString("zh-CN") }}
            </td>
            <td class="px-4 py-3">
              <div class="text-[#FAFAFA]">{{ r.name }}</div>
              <div class="nums text-xs text-[#848E9C]">{{ r.code }}</div>
            </td>
            <td class="px-4 py-3 text-[#EAECEF]">{{ r.strategy }}</td>
            <td class="nums px-4 py-3 text-xs text-[#848E9C]">{{ r.start }} ~ {{ r.end }}</td>
            <td
              class="nums px-4 py-3 text-right font-semibold"
              :class="r.metrics.total_return >= 0 ? 'text-[#F6465D]' : 'text-[#0ECB81]'"
            >
              {{ pct(r.metrics.total_return) }}
            </td>
            <td class="nums px-4 py-3 text-right text-[#0ECB81]">{{ pct(r.metrics.max_drawdown) }}</td>
            <td class="nums px-4 py-3 text-right text-[#EAECEF]">{{ r.metrics.sharpe }}</td>
            <td class="nums px-4 py-3 text-right text-[#EAECEF]">{{ pct(r.metrics.win_rate) }}</td>
            <td class="px-4 py-3 text-right">
              <button
                class="rounded-md border border-[#2B3139] px-2 py-1 text-xs text-[#848E9C] transition hover:border-[#007AFF] hover:text-[#007AFF]"
                title="用此配置重新运行"
                @click="rerun(r)"
              >
                ↻ 重跑
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
