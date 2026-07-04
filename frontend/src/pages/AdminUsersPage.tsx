import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Input, InputNumber, Popconfirm, Select, Space, Statistic, Table, Tag, message } from "antd";
import type { TableColumnsType, TablePaginationConfig } from "antd";

import { ApiError, listAdminUsers, updateAdminUserStatus, updateUserQuota } from "../api/client";
import type { AdminUserUsage, UserRole, UserStatus } from "../api/client";
import { useAuth } from "../features/auth/AuthContext";

const DEFAULT_PAGE_SIZE = 10;

export function AdminUsersPage() {
  const auth = useAuth();
  const [users, setUsers] = useState<AdminUserUsage[]>([]);
  const [draftLimits, setDraftLimits] = useState<Record<number, number>>({});
  const [keyword, setKeyword] = useState("");
  const [roleFilter, setRoleFilter] = useState<UserRole | "all">("all");
  const [statusFilter, setStatusFilter] = useState<UserStatus | "all">("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [savingIds, setSavingIds] = useState<number[]>([]);
  const [statusSavingIds, setStatusSavingIds] = useState<number[]>([]);

  const normalUserCount = users.filter((user) => user.role === "user").length;
  const totalUsedTokens = users.reduce((total, user) => total + user.usedTokens, 0);

  const loadUsers = useCallback(async (): Promise<void> => {
    setLoading(true);
    try {
      const result = await listAdminUsers({
        page,
        pageSize,
        keyword,
        role: roleFilter,
        status: statusFilter
      });
      setUsers(result.items);
      setTotal(result.total);
      setDraftLimits((items) => ({
        ...items,
        ...Object.fromEntries(
          result.items.filter((user) => user.dailyLimit !== null).map((user) => [user.id, user.dailyLimit || 0])
        )
      }));
    } catch (error) {
      message.error(getErrorMessage(error, "用户额度加载失败"));
    } finally {
      setLoading(false);
    }
  }, [keyword, page, pageSize, roleFilter, statusFilter]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

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
      },
      {
        title: "操作",
        width: 140,
        render: (_, user) => {
          const nextStatus: UserStatus = user.status === "active" ? "disabled" : "active";
          const isSelf = auth.user?.id === user.id;
          const label = user.status === "active" ? "封号" : "解封";
          return (
            <Popconfirm
              title={`${label}用户`}
              description={`确认${label} ${user.username}？`}
              okText="确认"
              cancelText="取消"
              disabled={isSelf}
              onConfirm={() => void saveStatus(user, nextStatus)}
            >
              <Button danger={nextStatus === "disabled"} disabled={isSelf} loading={statusSavingIds.includes(user.id)}>
                {label}
              </Button>
            </Popconfirm>
          );
        }
      }
    ],
    [auth.user?.id, draftLimits, savingIds, statusSavingIds]
  );

  const tablePagination = useMemo<TablePaginationConfig>(
    () => ({
      current: page,
      pageSize,
      total,
      showSizeChanger: true,
      showTotal: (count) => `共 ${count} 个用户`
    }),
    [page, pageSize, total]
  );

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

  async function saveStatus(user: AdminUserUsage, nextStatus: UserStatus): Promise<void> {
    setStatusSavingIds((ids) => [...ids, user.id]);
    try {
      const updated = await updateAdminUserStatus(user.id, nextStatus);
      setUsers((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      message.success(nextStatus === "disabled" ? "用户已封禁" : "用户已解封");
    } catch (error) {
      message.error(getErrorMessage(error, "用户状态更新失败"));
    } finally {
      setStatusSavingIds((ids) => ids.filter((id) => id !== user.id));
    }
  }

  function handleTableChange(pagination: TablePaginationConfig): void {
    setPage(pagination.current || 1);
    setPageSize(pagination.pageSize || DEFAULT_PAGE_SIZE);
  }

  function resetToFirstPage(): void {
    setPage(1);
  }

  return (
    <section className="admin-page">
      <header className="page-head">
        <div><p className="eyebrow">Token Quotas</p><h2>用户额度</h2></div>
      </header>
      <div className="quota-summary-grid">
        <Card className="quota-summary-card quota-summary-card-users">
          <span className="quota-summary-icon">U</span>
          <Statistic title="当前页普通用户" value={normalUserCount} />
        </Card>
        <Card className="quota-summary-card quota-summary-card-tokens">
          <span className="quota-summary-icon">T</span>
          <Statistic title="当前页今日用量" value={totalUsedTokens} groupSeparator="," suffix="Token" />
        </Card>
        <Card className="quota-summary-card quota-summary-card-note">
          <span className="quota-summary-icon">Q</span>
          <p className="m-0 leading-7">额度按北京时间自然日统计。管理员账号不受每日 Token 上限限制。</p>
        </Card>
      </div>
      <section className="user-filter-bar" aria-label="用户筛选">
        <div className="user-filter-copy">
          <span>用户筛选</span>
          <strong>共 {total.toLocaleString("zh-CN")} 个用户</strong>
        </div>
        <div className="user-filter-controls">
          <Input.Search
            allowClear
            className="user-filter-search"
            placeholder="搜索用户名"
            value={keyword}
            onChange={(event) => {
              setKeyword(event.target.value);
              resetToFirstPage();
            }}
            onSearch={() => resetToFirstPage()}
          />
          <Select
            className="user-filter-select"
            value={roleFilter}
            options={[
              { value: "all", label: "全部角色" },
              { value: "user", label: "普通用户" },
              { value: "admin", label: "管理员" }
            ]}
            onChange={(value: UserRole | "all") => {
              setRoleFilter(value);
              resetToFirstPage();
            }}
          />
          <Select
            className="user-filter-select"
            value={statusFilter}
            options={[
              { value: "all", label: "全部状态" },
              { value: "active", label: "正常" },
              { value: "disabled", label: "已禁用" }
            ]}
            onChange={(value: UserStatus | "all") => {
              setStatusFilter(value);
              resetToFirstPage();
            }}
          />
          <Button loading={loading} onClick={() => void loadUsers()}>刷新</Button>
        </div>
      </section>
      <Card className="admin-table-panel" styles={{ body: { padding: 0 } }}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={users}
          loading={loading}
          pagination={tablePagination}
          onChange={handleTableChange}
        />
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
