import { defineStore } from "pinia";
import { ref } from "vue";

import { runBacktest } from "../api";

// Shared backtest state so both the param panel and the Agent chat can
// trigger a run and have the center chart react (自然语言驱动 UI).
export const useBacktest = defineStore("backtest", () => {
  const result = ref(null);
  const params = ref(null); // last-run {code, kind, params, start, end}
  const loading = ref(false);
  const error = ref("");

  async function run(payload) {
    loading.value = true;
    error.value = "";
    try {
      result.value = await runBacktest(payload);
      params.value = payload;
      return result.value;
    } catch (e) {
      error.value = e.response?.data?.error || "回测失败";
      throw e;
    } finally {
      loading.value = false;
    }
  }

  // Apply a result the Agent already computed (from its trace), so we don't
  // re-run the backtest just to redraw the chart.
  function applyResult(res, meta) {
    result.value = res;
    if (meta) params.value = meta;
  }

  return { result, params, loading, error, run, applyResult };
});
