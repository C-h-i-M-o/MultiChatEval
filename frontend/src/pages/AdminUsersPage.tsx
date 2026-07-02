import { useEffect, useState } from "react";

import { ApiError, listAdminUsers, updateUserQuota } from "../api/client";
import type { AdminUserUsage } from "../api/client";

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserUsage[]>([]);
  const [draftLimits, setDraftLimits] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState(false);
  const [savingIds, setSavingIds] = useState<number[]>([]);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    void loadUsers();
  }, []);

  async function loadUsers(): Promise<void> {
    setLoading(true);
    setErrorMessage("");
    try {
      const result = await listAdminUsers();
      setUsers(result);
      setDraftLimits(Object.fromEntries(result.filter((user) => user.dailyLimit !== null).map((user) => [user.id, user.dailyLimit || 0])));
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "用户额度加载失败"));
    } finally {
      setLoading(false);
    }
  }

  async function saveQuota(user: AdminUserUsage): Promise<void> {
    setSavingIds((ids) => [...ids, user.id]);
    setErrorMessage("");
    try {
      const updated = await updateUserQuota(user.id, draftLimits[user.id] || 0);
      setUsers((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setDraftLimits((items) => ({ ...items, [updated.id]: updated.dailyLimit || 0 }));
    } catch (error) {
      setErrorMessage(getErrorMessage(error, "额度更新失败"));
    } finally {
      setSavingIds((ids) => ids.filter((id) => id !== user.id));
    }
  }

  const normalUserCount = users.filter((user) => user.role === "user").length;
  const totalUsedTokens = users.reduce((total, user) => total + user.usedTokens, 0);

  return (
    <section className="admin-page">
      <header className="page-head">
        <div><p className="eyebrow">Token Quotas</p><h2>用户额度</h2></div>
        <button type="button" onClick={() => void loadUsers()}>{loading ? "刷新中" : "刷新"}</button>
      </header>
      {errorMessage ? <p className="alert-message error">{errorMessage}</p> : null}
      <section className="summary-grid">
        <article><span>普通用户</span><strong>{normalUserCount}</strong></article>
        <article><span>今日总用量</span><strong>{totalUsedTokens.toLocaleString("zh-CN")}</strong></article>
        <p>额度按北京时间自然日统计。管理员账号不受每日 Token 上限限制。</p>
      </section>
      <section className="admin-table-panel">
        <div className="table-list">
          {users.map((user) => (
            <article key={user.id} className="table-row-card quota-row">
              <div>
                <strong>{user.username}</strong>
                <span>{user.role === "admin" ? "管理员" : "普通用户"} · {user.status === "active" ? "正常" : "已禁用"}</span>
                <small>今日已用 {user.usedTokens.toLocaleString("zh-CN")} Token</small>
              </div>
              {user.role === "admin" ? (
                <strong>不限额</strong>
              ) : (
                <div className="quota-editor">
                  <input
                    type="number"
                    min={0}
                    step={10000}
                    value={draftLimits[user.id] ?? 0}
                    onChange={(event) => setDraftLimits((items) => ({ ...items, [user.id]: Number(event.target.value) }))}
                  />
                  <button type="button" disabled={savingIds.includes(user.id)} onClick={() => void saveQuota(user)}>
                    {savingIds.includes(user.id) ? "保存中" : "保存"}
                  </button>
                </div>
              )}
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}
