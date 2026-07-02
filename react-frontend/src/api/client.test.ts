import { afterEach, describe, expect, test, vi } from "vitest";

import { ApiError, getCurrentUser, getHealthStatus, loginUser, logoutUser, registerUser } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

function mockJsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: init.status ?? 200,
    headers: {
      "Content-Type": "application/json"
    }
  });
}

describe("React 阶段一 API 客户端", () => {
  test("读取后端健康检查", async () => {
    const fetchMock = vi.fn().mockResolvedValue(mockJsonResponse({ status: "ok" }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getHealthStatus()).resolves.toEqual({ status: "ok" });

    expect(fetchMock).toHaveBeenCalledWith("/api/health", {
      credentials: "include",
      headers: {
        Accept: "application/json"
      }
    });
  });

  test("读取当前登录用户", async () => {
    const user = { id: 1, username: "admin", role: "admin", status: "active" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockJsonResponse(user)));

    await expect(getCurrentUser()).resolves.toEqual(user);
  });

  test("非 2xx 响应抛出带状态码的错误", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockJsonResponse({ detail: "未登录" }, { status: 401 })));

    await expect(getCurrentUser()).rejects.toEqual(new ApiError(401, "未登录"));
  });

  test("FastAPI 校验错误不会显示为对象字符串", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        mockJsonResponse(
          {
            detail: [
              {
                loc: ["body", "password"],
                msg: "String should have at least 8 characters",
                type: "string_too_short"
              }
            ]
          },
          { status: 422 }
        )
      )
    );

    await expect(loginUser({ username: "test", password: "123" })).rejects.toEqual(
      new ApiError(422, "密码长度不能少于 8 位")
    );
  });
});

describe("React 阶段二认证 API 客户端", () => {
  test("登录请求使用 HttpOnly Cookie 会话语义", async () => {
    const user = { id: 2, username: "demo", role: "user", status: "active" };
    const fetchMock = vi.fn().mockResolvedValue(mockJsonResponse(user));
    vi.stubGlobal("fetch", fetchMock);

    await expect(loginUser({ username: "demo", password: "password123" })).resolves.toEqual(user);

    expect(fetchMock).toHaveBeenCalledWith("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ username: "demo", password: "password123" })
    });
  });

  test("注册请求返回当前用户", async () => {
    const user = { id: 3, username: "newuser", role: "user", status: "active" };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(mockJsonResponse(user, { status: 201 })));

    await expect(registerUser({ username: "newuser", password: "password123" })).resolves.toEqual(user);
  });

  test("退出请求不解析空响应体", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(logoutUser()).resolves.toBeUndefined();

    expect(fetchMock).toHaveBeenCalledWith("/api/auth/logout", {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json"
      }
    });
  });
});
