<script setup>
// Fear & Greed style semicircular gauge driven by the up/down ratio.
// 0 = all-down (绿), 100 = all-up (红). Needle + arc animate via CSS transition.
import { computed } from "vue";

const props = defineProps({
  up: { type: Number, default: 0 },
  down: { type: Number, default: 0 },
});

// 0..100 bullishness
const score = computed(() => {
  const t = props.up + props.down;
  return t ? Math.round((props.up / t) * 100) : 50;
});

// Needle sweeps -90deg (all down) .. +90deg (all up).
const angle = computed(() => -90 + (score.value / 100) * 180);

const label = computed(() => {
  const s = score.value;
  if (s >= 75) return "极度贪婪";
  if (s >= 58) return "贪婪";
  if (s >= 42) return "中性";
  if (s >= 25) return "恐慌";
  return "极度恐慌";
});

const labelColor = computed(() =>
  score.value >= 50 ? "#f6465d" : "#0ecb81"
);

// Arc geometry: semicircle radius 80, center (100,100).
const R = 80;
const cx = 100;
const cy = 100;
const arcPath = (fromPct, toPct) => {
  const a0 = Math.PI - (fromPct / 100) * Math.PI;
  const a1 = Math.PI - (toPct / 100) * Math.PI;
  const x0 = cx + R * Math.cos(a0);
  const y0 = cy - R * Math.sin(a0);
  const x1 = cx + R * Math.cos(a1);
  const y1 = cy - R * Math.sin(a1);
  return `M ${x0} ${y0} A ${R} ${R} 0 0 1 ${x1} ${y1}`;
};
</script>

<template>
  <div class="flex flex-col items-center">
    <svg viewBox="0 0 200 116" class="w-full max-w-[260px]">
      <!-- green (down) half -->
      <path :d="arcPath(0, 50)" fill="none" stroke="#0ecb81" stroke-width="10"
        stroke-linecap="round" opacity="0.85" />
      <!-- red (up) half -->
      <path :d="arcPath(50, 100)" fill="none" stroke="#f6465d" stroke-width="10"
        stroke-linecap="round" opacity="0.85" />
      <!-- needle -->
      <g :style="{ transform: `rotate(${angle}deg)`, transformOrigin: '100px 100px', transition: 'transform 0.8s cubic-bezier(0.16,1,0.3,1)' }">
        <line x1="100" y1="100" x2="100" y2="34" stroke="#fafafa" stroke-width="2.5" stroke-linecap="round" />
        <circle cx="100" cy="100" r="5" fill="#fafafa" />
      </g>
    </svg>
    <div class="-mt-2 text-center">
      <div class="nums text-3xl font-bold" :style="{ color: labelColor }">{{ score }}</div>
      <div class="mt-0.5 text-xs tracking-widest" :style="{ color: labelColor }">{{ label }}</div>
    </div>
  </div>
</template>
