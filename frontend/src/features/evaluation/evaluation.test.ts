import { describe, expect, test } from "vitest";

import { applyFeedbackResult, createPendingResponses, mergeStreamEvent } from "./evaluation";
import type { EvaluationTaskState, ModelResponse } from "./types";

const successfulResponse: ModelResponse = {
  id: 31,
  modelConfigId: 2,
  modelName: "DeepSeek",
  provider: "deepseek",
  answer: "答案",
  latencyMs: 1200,
  inputTokens: 5,
  outputTokens: 8,
  cacheHitTokens: 0,
  cacheCreationTokens: 0,
  totalTokens: 13,
  estimatedCost: 0.02,
  currency: "CNY",
  costDetails: {
    inputCost: 0.01,
    outputCost: 0.01,
    cacheHitCost: 0,
    cacheCreationCost: 0
  },
  status: "success",
  score: {
    relevance: 9,
    completeness: 8,
    clarity: 8,
    format: 7,
    safety: 10,
    final: 8.5,
    details: {},
    ruleFinal: 8.5,
    judgeFinal: null,
    baseFinal: 8.5,
    feedbackScore: null,
    judgeComment: null,
    judgeDetails: {}
  },
  feedback: {
    liked: false,
    likeCount: 0,
    disliked: false,
    dislikeCount: 0
  }
};

describe("React 阶段三评测状态", () => {
  test("创建等待卡片时保留用户选择模型顺序", () => {
    expect(
      createPendingResponses(
        [5, 2],
        [
          { id: 2, providerName: "deepseek", displayName: "DeepSeek", modelName: "deepseek-chat" },
          { id: 5, providerName: "minimax", displayName: "MiniMax", modelName: "abab" }
        ]
      )
    ).toEqual([
      { id: "pending-5", modelConfigId: 5, modelName: "MiniMax", pending: true },
      { id: "pending-2", modelConfigId: 2, modelName: "DeepSeek", pending: true }
    ]);
  });

  test("模型响应事件替换对应等待卡片并保留其余顺序", () => {
    const state: EvaluationTaskState = {
      taskId: 12,
      status: "running",
      prompt: "问题",
      responses: [
        { id: "pending-5", modelConfigId: 5, modelName: "MiniMax", pending: true },
        { id: "pending-2", modelConfigId: 2, modelName: "DeepSeek", pending: true }
      ]
    };

    expect(mergeStreamEvent(state, { type: "model_response", response: successfulResponse })).toEqual({
      ...state,
      responses: [
        { id: "pending-5", modelConfigId: 5, modelName: "MiniMax", pending: true },
        successfulResponse
      ]
    });
  });

  test("反馈结果同步更新对应回答", () => {
    const state: EvaluationTaskState = {
      taskId: 12,
      status: "completed",
      prompt: "问题",
      responses: [successfulResponse]
    };

    expect(
      applyFeedbackResult(state, {
        responseId: 31,
        feedbackType: "like",
        active: true,
        feedback: { liked: true, likeCount: 1, disliked: false, dislikeCount: 0 },
        score: { ...successfulResponse.score, final: 8.6, feedbackScore: 10 }
      }).responses[0]
    ).toMatchObject({
      feedback: { liked: true, likeCount: 1 },
      score: { final: 8.6, feedbackScore: 10 }
    });
  });
});
