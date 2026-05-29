import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000
});

export async function createEvaluationTask(payload) {
  const response = await api.post("/evaluation/tasks", payload);
  return response.data;
}
