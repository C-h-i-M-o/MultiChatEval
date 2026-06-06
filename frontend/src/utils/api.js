import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 120000
});

export async function createEvaluationTask(payload) {
  const response = await api.post("/evaluation/tasks", payload);
  return response.data;
}

export async function listEvaluationTasks({ page, pageSize }) {
  const response = await api.get("/evaluation/tasks", {
    params: {
      page,
      pageSize
    }
  });
  return response.data;
}

export async function getEvaluationTask(taskId) {
  const response = await api.get(`/evaluation/tasks/${taskId}`);
  return response.data;
}

export async function submitResponseFeedback(responseId, payload) {
  const response = await api.post(`/evaluation/responses/${responseId}/feedback`, payload);
  return response.data;
}

export async function listResponseComments(responseId, { page, pageSize }) {
  const response = await api.get(`/evaluation/responses/${responseId}/comments`, {
    params: {
      page,
      pageSize
    }
  });
  return response.data;
}

export async function createResponseComment(responseId, payload) {
  const response = await api.post(`/evaluation/responses/${responseId}/comments`, payload);
  return response.data;
}

export async function deleteResponseComment(commentId) {
  await api.delete(`/evaluation/comments/${commentId}`);
}

export async function streamEvaluationTask(payload, onEvent) {
  const response = await fetch("/api/evaluation/tasks/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "评测任务创建失败");
  }

  if (!response.body) {
    throw new Error("当前浏览器不支持渐进式读取模型结果");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine) {
        onEvent(JSON.parse(trimmedLine));
      }
    }
  }

  buffer += decoder.decode();
  if (buffer.trim()) {
    onEvent(JSON.parse(buffer.trim()));
  }
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
