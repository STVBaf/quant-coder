import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";

import "./main.css";
import "./charts";

import App from "./App.vue";
import Dashboard from "./views/Dashboard.vue";
import StockDetail from "./views/StockDetail.vue";
import Workspace from "./views/Workspace.vue";
import Login from "./views/Login.vue";
import History from "./views/History.vue";
import { bindApiHandlers } from "./api";
import { useToast } from "./stores/toast";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: Dashboard },
    { path: "/stock/:code", component: StockDetail },
    { path: "/workspace", component: Workspace },
    { path: "/login", component: Login },
    { path: "/history", component: History },
  ],
});

const pinia = createPinia();
const app = createApp(App).use(pinia).use(router);

bindApiHandlers({
  unauthorized: () => router.currentRoute.value.path !== "/login" && router.push("/login"),
  serviceDown: (msg) => useToast(pinia).push(msg, "error"),
});

app.mount("#app");
