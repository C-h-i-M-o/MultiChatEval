import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000
});

export async function createEvaluationTask(payload) {
  const response = await api.post("/evaluation/tasks", payload);
  return response.data;
}

export async function listModelConfigs() {
  const response = await api.get("/model-configs");
  return response.data;
}

export async function createModelConfig(payload) {
  const response = await api.post("/model-configs", payload);
  return response.data;
}

export async function updateModelConfig(id, payload) {
  const response = await api.put(`/model-configs/${id}`, payload);
  return response.data;
}

export async function deleteModelConfig(id) {
  const response = await api.delete(`/model-configs/${id}`);
  return response.data;
}

export async function testModelConfig(payload) {
  const response = await api.post("/model-configs/test", payload);
  return response.data;
}
