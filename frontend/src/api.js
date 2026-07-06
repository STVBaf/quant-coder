import axios from "axios";

const api = axios.create({ baseURL: "/api" });

// Set by main.js once Pinia/router exist, so the interceptor can react globally.
let onUnauthorized = null;
let onServiceDown = null;
export function bindApiHandlers({ unauthorized, serviceDown }) {
  onUnauthorized = unauthorized;
  onServiceDown = serviceDown;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Token ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err.response?.status;
    if (status === 401) onUnauthorized?.();
    if (status === 503) onServiceDown?.(err.response?.data?.error || "外部数据源暂时不可用");
    return Promise.reject(err);
  }
);

export const getKline = (code, params) =>
  api.get(`/market/kline/${code}/`, { params }).then((r) => r.data);

export const getOverview = () =>
  api.get("/market/overview/").then((r) => r.data);

export const getQuote = (code) =>
  api.get(`/market/quote/${code}/`).then((r) => r.data);

export const listStrategies = () =>
  api.get("/backtest/strategies/").then((r) => r.data);

export const runBacktest = (payload) =>
  api.post("/backtest/run/", payload).then((r) => r.data);

export const getHistory = () =>
  api.get("/backtest/history/").then((r) => r.data);

export const register = (payload) =>
  api.post("/auth/register/", payload).then((r) => r.data);

export const login = (payload) =>
  api.post("/auth/login/", payload).then((r) => r.data);

export const getWatchlist = () =>
  api.get("/auth/watchlist/").then((r) => r.data);

export const addWatch = (code) =>
  api.post("/auth/watchlist/", { code }).then((r) => r.data);

export const removeWatch = (code) =>
  api.delete(`/auth/watchlist/${code}/`).then((r) => r.data);

export const sendChat = (payload) =>
  api.post("/agent/chat/", payload).then((r) => r.data);

export const createResearch = (payload) =>
  api.post("/agent/research/", payload).then((r) => r.data);

export const getResearch = (id) =>
  api.get(`/agent/research/${id}/`).then((r) => r.data);

export default api;
