export interface ParsedThinkContent {
  answer: string;
  thought: string;
}

export function parseThinkContent(content: string): ParsedThinkContent {
  const thoughts: string[] = [];
  let answer = content || "";

  answer = answer.replace(/<think>([\s\S]*?)<\/think>/gi, (_match, thought: string) => {
    const trimmedThought = thought.trim();
    if (trimmedThought) {
      thoughts.push(trimmedThought);
    }
    return "";
  });

  const unmatchedStart = answer.search(/<think>/i);
  if (unmatchedStart >= 0) {
    const thought = answer.slice(unmatchedStart).replace(/<think>/i, "").trim();
    if (thought) {
      thoughts.push(thought);
    }
    answer = answer.slice(0, unmatchedStart);
  }

  return {
    answer: answer.trim(),
    thought: thoughts.join("\n\n---\n\n")
  };
}

export function toAnswerPreview(answer: string): string {
  const parsed = parseThinkContent(answer || "暂无回答内容");
  const plainText = parsed.answer
    .replace(/```[\s\S]*?```/g, " 代码块 ")
    .replace(/[#>*_`|[\]()~-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  return plainText || "暂无回答内容";
}
