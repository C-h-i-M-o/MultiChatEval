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

test("getApiErrorMessage joins multiple validation messages", () => {
  const error = {
    response: {
      data: {
        detail: [
          {
            type: "string_too_short",
            loc: ["body", "username"],
            msg: "String should have at least 3 characters"
          },
          {
            type: "string_too_long",
            loc: ["body", "password"],
            msg: "String should have at most 128 characters"
          }
        ]
      }
    }
  };

  assert.equal(getApiErrorMessage(error, "认证失败"), "用户名长度不能少于 3 位；密码长度不能超过 128 位");
});

test("getApiErrorMessage handles object detail without object string", () => {
  const error = {
    response: {
      data: {
        detail: {
          loc: ["body", "content"],
          msg: "评论不能为空"
        }
      }
    }
  };

  assert.equal(getApiErrorMessage(error, "评论发布失败"), "评论不能为空");
});
