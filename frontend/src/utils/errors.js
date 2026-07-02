const FIELD_NAMES = {
  password: "密码",
  username: "用户名"
};

const FIELD_LENGTHS = {
  password: { min: 8, max: 128 },
  username: { min: 3, max: 64 }
};

function formatValidationError(detail) {
  if (!Array.isArray(detail) || detail.length === 0) {
    return "";
  }

  const messages = detail
    .map((issue) => formatValidationIssue(issue))
    .filter(Boolean);

  return messages.join("；");
}

function formatValidationIssue(issue) {
  const field = Array.isArray(issue?.loc) ? issue.loc.at(-1) : null;
  const fieldName = FIELD_NAMES[field] || "输入内容";
  const limits = FIELD_LENGTHS[field];

  if (issue?.type === "string_too_short") {
    return `${fieldName}长度不能少于 ${issue?.ctx?.min_length || limits?.min || "规定"} 位`;
  }
  if (issue?.type === "string_too_long") {
    return `${fieldName}长度不能超过 ${issue?.ctx?.max_length || limits?.max || "规定"} 位`;
  }
  return typeof issue?.msg === "string" && issue.msg.trim() ? issue.msg : `${fieldName}格式不正确`;
}

export function getApiErrorMessage(error, fallbackMessage) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  const validationMessage = formatValidationError(detail);
  if (validationMessage) {
    return validationMessage;
  }

  if (detail && typeof detail === "object" && typeof detail.msg === "string") {
    return formatValidationIssue(detail);
  }

  return typeof error?.message === "string" && error.message.trim() ? error.message : fallbackMessage;
}
