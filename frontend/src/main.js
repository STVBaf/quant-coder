import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import PrimeVue from "primevue/config";
import Aura from "@primevue/themes/aura";
import { definePreset } from "@primevue/themes";
import "primeicons/primeicons.css";

import "./main.css";
import "./charts";

import App from "./App.vue";
import Dashboard from "./views/Dashboard.vue";
import StockDetail from "./views/StockDetail.vue";
import Workspace from "./views/Workspace.vue";
import Login from "./views/Login.vue";
import History from "./views/History.vue";
import Research from "./views/Research.vue";
import { bindApiHandlers } from "./api";
import { useToast } from "./stores/toast";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: Dashboard },
    { path: "/stock/:code", component: StockDetail },
    { path: "/workspace", component: Workspace },
    { path: "/research", component: Research },
    { path: "/login", component: Login },
    { path: "/history", component: History },
  ],
});

// Retint PrimeVue's Aura preset toward our brand blue so components blend into
// the OKX dark theme instead of Aura's default teal.
const QuantPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: "#e6f2ff", 100: "#cce4ff", 200: "#99c9ff", 300: "#66adff",
      400: "#3392ff", 500: "#007aff", 600: "#0062cc", 700: "#004999",
      800: "#003166", 900: "#001833", 950: "#000c1a",
    },
  },
});

const pinia = createPinia();
const app = createApp(App).use(pinia).use(router);
app.use(PrimeVue, {
  theme: {
    preset: QuantPreset,
    options: {
      // Force dark permanently — the app is dark-only. Scoping to <html class="dark">.
      darkModeSelector: ".dark",
      cssLayer: { name: "primevue", order: "theme, base, primevue" },
    },
  },
});

bindApiHandlers({
  unauthorized: () => router.currentRoute.value.path !== "/login" && router.push("/login"),
  serviceDown: (msg) => useToast(pinia).push(msg, "error"),
});

app.mount("#app");
