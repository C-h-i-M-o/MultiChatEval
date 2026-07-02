import { afterEach, describe, expect, test, vi } from "vitest";

import { ApiError, getCurrentUser, getHealthStatus } from "./client";

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
});
