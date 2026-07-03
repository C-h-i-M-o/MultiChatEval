import type {
  AvailableModelConfig,
  DisplayModelResponse,
  EvaluationStreamEvent,
  EvaluationTaskState,
  FeedbackToggleResult,
  ModelResponse,
  PendingModelResponse
} from "./types";

export function createPendingResponses(
  modelIds: number[],
  availableModels: AvailableModelConfig[]
): PendingModelResponse[] {
  const modelNameMap = new Map(availableModels.map((modelConfig) => [modelConfig.id, modelConfig.displayName]));
  return modelIds.map((modelId) => ({
    id: `pending-${modelId}`,
    modelConfigId: modelId,
    modelName: modelNameMap.get(modelId) || `模型 ${modelId}`,
    pending: true
  }));
}

export function mergeStreamEvent(
  state: EvaluationTaskState | null,
  event: EvaluationStreamEvent
): EvaluationTaskState {
  if (event.type === "task_started") {
    return {
      taskId: event.taskId,
      status: event.status,
      prompt: event.prompt,
      responses: state?.responses || []
    };
  }

  if (event.type === "model_response") {
    return {
      ...(state || { taskId: null, status: "running", prompt: "", responses: [] }),
      responses: mergeModelResponse(state?.responses || [], event.response)
    };
  }

  return {
    taskId: event.task.taskId,
    status: event.task.status,
    prompt: event.task.prompt,
    visibility: event.task.visibility,
    responses: event.task.responses
  };
}

export function applyFeedbackResult(state: EvaluationTaskState, result: FeedbackToggleResult): EvaluationTaskState {
  return {
    ...state,
    responses: state.responses.map((response) => {
      if (isPendingResponse(response) || response.id !== result.responseId) {
        return response;
      }
      return {
        ...response,
        feedback: result.feedback,
        score: result.score
      };
    })
  };
}

export function isPendingResponse(response: DisplayModelResponse): response is PendingModelResponse {
  return "pending" in response && response.pending;
}

function mergeModelResponse(responses: DisplayModelResponse[], nextResponse: ModelResponse): DisplayModelResponse[] {
  const targetModelId = nextResponse.modelConfigId;
  let replaced = false;
  const nextResponses = responses.map((response) => {
    if (targetModelId !== null && response.modelConfigId === targetModelId) {
      replaced = true;
      return nextResponse;
    }
    if (!isPendingResponse(response) && response.id === nextResponse.id) {
      replaced = true;
      return nextResponse;
    }
    return response;
  });

  return replaced ? nextResponses : [...nextResponses, nextResponse];
}
