import { useEffect, useMemo, useState } from "react";
import { Button, Card, InputNumber, Space, Statistic, Table, Tag, message } from "antd";
import type { TableColumnsType } from "antd";

import { ApiError, listAdminUsers, updateUserQuota } from "../api/client";
import type { AdminUserUsage } from "../api/client";

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUserUsage[]>([]);
  const [draftLimits, setDraftLimits] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState(false);
  const [savingIds, setSavingIds] = useState<number[]>([]);

  useEffect(() => {
    void loadUsers();
  }, []);

  const normalUserCount = users.filter((user) => user.role === "user").length;
  const totalUsedTokens = users.reduce((total, user) => total + user.usedTokens, 0);

  const columns = useMemo<TableColumnsType<AdminUserUsage>>(
    () => [
      { title: "用户", dataIndex: "username" },
      {
        title: "角色",
        dataIndex: "role",
        width: 120,
        render: (role: AdminUserUsage["role"]) => <Tag color={role === "admin" ? "gold" : "green"}>{role === "admin" ? "管理员" : "普通用户"}</Tag>
      },
      {
        title: "状态",
        dataIndex: "status",
        width: 110,
        render: (status: AdminUserUsage["status"]) => <Tag color={status === "active" ? "success" : "default"}>{status === "active" ? "正常" : "已禁用"}</Tag>
      },
      {
        title: "今日已用 Token",
        dataIndex: "usedTokens",
        render: (value: number) => value.toLocaleString("zh-CN")
      },
      {
        title: "每日额度",
        width: 280,
        render: (_, user) =>
          user.role === "admin" ? (
            <strong>不限额</strong>
          ) : (
            <Space.Compact>
              <InputNumber
                min={0}
                step={10000}
                value={draftLimits[user.id] ?? 0}
                onChange={(value) => setDraftLimits((items) => ({ ...items, [user.id]: Number(value || 0) }))}
              />
              <Button type="primary" loading={savingIds.includes(user.id)} onClick={() => void saveQuota(user)}>
                保存
              </Button>
            </Space.Compact>
          )
      }
    ],
    [draftLimits, savingIds]
  );

  async function loadUsers(): Promise<void> {
    setLoading(true);
    try {
      const result = await listAdminUsers();
      setUsers(result);
      setDraftLimits(Object.fromEntries(result.filter((user) => user.dailyLimit !== null).map((user) => [user.id, user.dailyLimit || 0])));
    } catch (error) {
      message.error(getErrorMessage(error, "用户额度加载失败"));
    } finally {
      setLoading(false);
    }
  }

  async function saveQuota(user: AdminUserUsage): Promise<void> {
    setSavingIds((ids) => [...ids, user.id]);
    try {
      const updated = await updateUserQuota(user.id, draftLimits[user.id] || 0);
      setUsers((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setDraftLimits((items) => ({ ...items, [updated.id]: updated.dailyLimit || 0 }));
      message.success("用户额度已保存");
    } catch (error) {
      message.error(getErrorMessage(error, "额度更新失败"));
    } finally {
      setSavingIds((ids) => ids.filter((id) => id !== user.id));
    }
  }

  return (
    <section className="admin-page">
      <header className="page-head">
        <div><p className="eyebrow">Token Quotas</p><h2>用户额度</h2></div>
        <Button loading={loading} onClick={() => void loadUsers()}>刷新</Button>
      </header>
      <div className="quota-summary-grid">
        <Card className="quota-summary-card quota-summary-card-users">
          <span className="quota-summary-icon">U</span>
          <Statistic title="普通用户" value={normalUserCount} />
        </Card>
        <Card className="quota-summary-card quota-summary-card-tokens">
          <span className="quota-summary-icon">T</span>
          <Statistic title="今日总用量" value={totalUsedTokens} groupSeparator="," suffix="Token" />
        </Card>
        <Card className="quota-summary-card quota-summary-card-note">
          <span className="quota-summary-icon">Q</span>
          <p className="m-0 leading-7">额度按北京时间自然日统计。管理员账号不受每日 Token 上限限制。</p>
        </Card>
      </div>
      <Card className="admin-table-panel" styles={{ body: { padding: 0 } }}>
        <Table rowKey="id" columns={columns} dataSource={users} loading={loading} pagination={false} />
      </Card>
    </section>
  );
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
}
