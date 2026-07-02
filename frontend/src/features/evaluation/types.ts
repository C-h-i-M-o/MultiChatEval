import type { AvailableModel, EvaluationVisibility, FeedbackType } from "../../api/client";

export interface EvaluationScore {
  relevance: number;
  completeness: number;
  clarity: number;
  format: number;
  safety: number;
  final: number;
  details: Record<string, string[]>;
  ruleFinal?: number | null;
  judgeFinal?: number | null;
  baseFinal?: number | null;
  feedbackScore?: number | null;
  judgeComment?: string | null;
  judgeDetails?: Record<string, string[]>;
}

export interface EvaluationFeedback {
  liked: boolean;
  likeCount: number;
  disliked: boolean;
  dislikeCount: number;
}

export interface ModelCostDetails {
  inputCost: number;
  outputCost: number;
  cacheHitCost: number;
  cacheCreationCost: number;
}

export interface ModelResponse {
  id: number;
  modelConfigId: number | null;
  modelName: string;
  provider: string;
  answer: string;
  latencyMs: number;
  inputTokens: number;
  outputTokens: number;
  cacheHitTokens: number;
  cacheCreationTokens: number;
  totalTokens: number;
  estimatedCost: number;
  currency: "CNY" | "USD";
  costDetails: ModelCostDetails;
  status: string;
  score: EvaluationScore;
  feedback: EvaluationFeedback;
}

export interface PendingModelResponse {
  id: string;
  modelConfigId: number;
  modelName: string;
  pending: true;
}

export type DisplayModelResponse = ModelResponse | PendingModelResponse;

export interface EvaluationTaskState {
  taskId: number | null;
  status: string;
  prompt: string;
  visibility?: EvaluationVisibility;
  responses: DisplayModelResponse[];
}

export interface EvaluationTaskRead {
  taskId: number;
  status: string;
  prompt: string;
  createdAt?: string | null;
  completedAt?: string | null;
  ownerId?: number | null;
  ownerUsername: string;
  visibility: EvaluationVisibility;
  responses: ModelResponse[];
}

export type EvaluationStreamEvent =
  | {
      type: "task_started";
      taskId: number;
      prompt: string;
      status: string;
    }
  | {
      type: "model_response";
      response: ModelResponse;
    }
  | {
      type: "task_completed";
      task: EvaluationTaskRead;
    };

export interface FeedbackToggleResult {
  responseId: number;
  feedbackType: FeedbackType;
  active: boolean;
  feedback: EvaluationFeedback;
  score: EvaluationScore;
}

export type AvailableModelConfig = AvailableModel;
