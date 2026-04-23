import axios from "axios";

const api = axios.create({ baseURL: "/api" });

// Clients
export const getClients = () => api.get("/clients").then((r) => r.data);

export const createClient = (payload) =>
  api.post("/clients", payload).then((r) => r.data);

export const updateClient = (id, payload) =>
  api.patch(`/clients/${id}`, payload).then((r) => r.data);

export const deleteClient = (id) => api.delete(`/clients/${id}`);

// Stats
export const getSummary = () => api.get("/stats/summary").then((r) => r.data);

export const getTimeline = (minutes = 30) =>
  api.get("/stats/timeline", { params: { minutes } }).then((r) => r.data);

export const getThrottledClients = () =>
  api.get("/stats/throttled-clients").then((r) => r.data);

export const getClientStats = (id) =>
  api.get(`/stats/clients/${id}`).then((r) => r.data);

// Gateway test
export const fireTestRequest = (apiKey) =>
  api
    .get("/gateway/test", { headers: { "X-API-Key": apiKey } })
    .then((r) => ({ status: r.status, data: r.data, headers: r.headers }))
    .catch((e) => ({
      status: e.response?.status,
      data: e.response?.data,
      headers: e.response?.headers,
    }));
