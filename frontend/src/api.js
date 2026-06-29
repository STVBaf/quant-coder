import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export const getKline = (code, params) =>
  api.get(`/market/kline/${code}/`, { params }).then((r) => r.data);

export const getOverview = () =>
  api.get("/market/overview/").then((r) => r.data);

export const listStrategies = () =>
  api.get("/backtest/strategies/").then((r) => r.data);

export const runBacktest = (payload) =>
  api.post("/backtest/run/", payload).then((r) => r.data);

export default api;
