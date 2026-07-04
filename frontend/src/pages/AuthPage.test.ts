import { describe, expect, test } from "vitest";

import { getPasswordRuleStates, getRegisterInlineMessage, isRegisterSubmitDisabled } from "./AuthPage";

describe("注册页实时密码校验", () => {
  test("逐项返回密码规则是否满足", () => {
    expect(getPasswordRuleStates("abc")).toEqual([
      { key: "length", label: "至少 8 位", valid: false },
      { key: "digit", label: "包含数字", valid: false },
      { key: "lowercase", label: "包含小写字母", valid: true },
      { key: "uppercase", label: "包含大写字母", valid: false }
    ]);

    expect(getPasswordRuleStates("Password1").every((rule) => rule.valid)).toBe(true);
  });

  test("实时提示确认密码不一致", () => {
    expect(getRegisterInlineMessage("Password1", "Password2")).toBe("两次输入的密码不一致");
    expect(getRegisterInlineMessage("Password1", "Password1")).toBeNull();
  });

  test("注册按钮在密码不合规或确认密码不一致时禁用", () => {
    expect(isRegisterSubmitDisabled("demo", "password1", "password1", false)).toBe(true);
    expect(isRegisterSubmitDisabled("demo", "Password1", "Password2", false)).toBe(true);
    expect(isRegisterSubmitDisabled("demo", "Password1", "Password1", false)).toBe(false);
    expect(isRegisterSubmitDisabled("demo", "Password1", "Password1", true)).toBe(true);
  });
});
