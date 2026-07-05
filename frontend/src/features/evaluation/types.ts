import type { AvailableModel, EvaluationVisibility, FeedbackType } from "../../api/client";

export interface EvaluationScore {
  relevance: number;
  completeness: number;
  clarity: number;
  format: number;
  safety: number;
  final: number | null;
  details: Record<string, string[]>;
  ruleFinal?: number | null;
  judgeFinal?: number | null;
  baseFinal?: number | null;
  feedbackScore?: number | null;
  judgeComment?: string | null;
  judgeDetails?: Record<string, string[]>;
  scoreStatus?: ScoreStatus;
  excludedFromStats?: boolean;
  judgeRuns?: JudgeRun[];
  judgeScoreRange?: number | null;
}

export type ScoreStatus = "scored" | "judge_failed" | "judge_unstable" | "judge_disabled" | "model_failed";

export interface JudgeRun {
  runIndex: number;
  promptCode: string;
  score: number | null;
  confidence: number | null;
  comment: string | null;
  error: string | null;
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

export interface StreamingModelResponse {
  id: string;
  modelConfigId: number;
  modelName: string;
  answer: string;
  streaming: boolean;
  scoring: boolean;
}

export type DisplayModelResponse = ModelResponse | PendingModelResponse | StreamingModelResponse;

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

export interface EvaluationTaskListItem {
  taskId: number;
  status: string;
  prompt: string;
  createdAt: string;
  completedAt?: string | null;
  responseCount: number;
  ownerId?: number | null;
  ownerUsername: string;
  visibility: EvaluationVisibility;
}

export interface EvaluationTaskListRead {
  items: EvaluationTaskListItem[];
  total: number;
  page: number;
  pageSize: number;
}

export interface CommentRead {
  id: number;
  responseId: number;
  userId: number;
  username: string;
  content: string;
  createdAt: string;
  canDelete: boolean;
}

export interface CommentListRead {
  items: CommentRead[];
  total: number;
  page: number;
  pageSize: number;
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
      type: "model_delta";
      modelConfigId: number;
      delta: string;
    }
  | {
      type: "model_answer_completed";
      modelConfigId: number;
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
