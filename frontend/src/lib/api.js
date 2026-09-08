import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60s — LLM calls can be slow
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — add any global headers here
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
);

// Response interceptor — normalize errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.message ||
      "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

export const queryStandards = (question) =>
  api.post("/api/query", { question }).then((r) => r.data);

export const runGapCheck = (product_description) =>
  api.post("/api/gap-check", { product_description }).then((r) => r.data);

export const searchStandards = (q, category = "", limit = 10) =>
  api.get("/api/search", { params: { q, category, limit } }).then((r) => r.data);

export const fetchGraph = () =>
  api.get("/api/graph").then((r) => r.data);

export const fetchHealth = () =>
  api.get("/api/health").then((r) => r.data);

export default api;
