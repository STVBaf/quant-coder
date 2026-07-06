import { defineStore } from "pinia";
import { ref } from "vue";

let seq = 0;

export const useToast = defineStore("toast", () => {
  const items = ref([]);

  function push(text, type = "info") {
    const id = ++seq;
    items.value.push({ id, text, type });
    setTimeout(() => dismiss(id), 4000);
  }

  function dismiss(id) {
    items.value = items.value.filter((t) => t.id !== id);
  }

  return { items, push, dismiss };
});
