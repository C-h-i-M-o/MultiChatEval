import test from "node:test";
import assert from "node:assert/strict";

import { getApiErrorMessage } from "../src/utils/errors.js";

test("getApiErrorMessage extracts FastAPI validation detail arrays", () => {
  const error = {
    response: {
      data: {
        detail: [
          {
            type: "string_too_short",
            loc: ["body", "password"],
            msg: "String should have at least 8 characters"
          }
        ]
      }
    }
  };

  assert.equal(getApiErrorMessage(error, "认证失败"), "密码长度不能少于 8 位");
});
