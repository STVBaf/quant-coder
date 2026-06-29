import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";

import App from "./App.vue";
import Dashboard from "./views/Dashboard.vue";
import StockDetail from "./views/StockDetail.vue";
import Backtest from "./views/Backtest.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: Dashboard },
    { path: "/stock/:code", component: StockDetail },
    { path: "/backtest", component: Backtest },
  ],
});

createApp(App).use(createPinia()).use(router).mount("#app");
