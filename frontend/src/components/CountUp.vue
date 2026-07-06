<script setup>
// Smoothly animates a number toward `value` with requestAnimationFrame, and
// flashes red/green on every change (交易终端 tick effect). 红涨绿跌.
import { ref, watch, onUnmounted } from "vue";

const props = defineProps({
  value: { type: Number, default: 0 },
  decimals: { type: Number, default: 2 },
  duration: { type: Number, default: 600 },
  flash: { type: Boolean, default: true }, // flash on change
});

const display = ref(props.value);
const flashClass = ref("");
let raf = null;
let flashTimer = null;

function animate(to) {
  const from = display.value;
  const start = performance.now();
  cancelAnimationFrame(raf);
  const step = (now) => {
    const t = Math.min((now - start) / props.duration, 1);
    const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic
    display.value = from + (to - from) * eased;
    if (t < 1) raf = requestAnimationFrame(step);
    else display.value = to;
  };
  raf = requestAnimationFrame(step);
}

watch(
  () => props.value,
  (to, prev) => {
    if (props.flash && to !== prev) {
      flashClass.value = to >= prev ? "fx-up" : "fx-down";
      clearTimeout(flashTimer);
      flashTimer = setTimeout(() => (flashClass.value = ""), 600);
    }
    animate(to);
  }
);

onUnmounted(() => {
  cancelAnimationFrame(raf);
  clearTimeout(flashTimer);
});
</script>

<template>
  <span class="nums rounded px-0.5" :class="flashClass">
    {{ display.toFixed(decimals) }}
  </span>
</template>
