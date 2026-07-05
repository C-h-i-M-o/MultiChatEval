import { Button, Input, Select } from "antd";
import type { ReactNode } from "react";

export interface AdminFilterOption<T extends string> {
  value: T;
  label: string;
}

interface AdminFilterBarProps<RoleValue extends string, StatusValue extends string> {
  title: string;
  total: number;
  searchValue: string;
  searchPlaceholder: string;
  roleValue: RoleValue;
  roleOptions: Array<AdminFilterOption<RoleValue>>;
  statusValue: StatusValue;
  statusOptions: Array<AdminFilterOption<StatusValue>>;
  loading: boolean;
  actions?: ReactNode;
  onSearchChange: (value: string) => void;
  onSearchSubmit: () => void;
  onRoleChange: (value: RoleValue) => void;
  onStatusChange: (value: StatusValue) => void;
  onRefresh: () => void;
}

export function AdminFilterBar<RoleValue extends string, StatusValue extends string>({
  title,
  total,
  searchValue,
  searchPlaceholder,
  roleValue,
  roleOptions,
  statusValue,
  statusOptions,
  loading,
  actions,
  onSearchChange,
  onSearchSubmit,
  onRoleChange,
  onStatusChange,
  onRefresh
}: AdminFilterBarProps<RoleValue, StatusValue>) {
  const hasActiveFilters =
    searchValue.trim().length > 0 || roleValue !== roleOptions[0]?.value || statusValue !== statusOptions[0]?.value;

  return (
    <section className={hasActiveFilters ? "user-filter-bar user-filter-bar-active" : "user-filter-bar"} aria-label={title}>
      <div className="user-filter-head">
        <div className="user-filter-copy">
          <span>{title}</span>
          <strong>共 {total.toLocaleString("zh-CN")} 条</strong>
        </div>
        {actions ? <div className="user-filter-actions">{actions}</div> : null}
      </div>
      <div className="user-filter-controls">
        <Input.Search
          allowClear
          className="user-filter-search user-filter-control-item"
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          onSearch={onSearchSubmit}
        />
        <Select<RoleValue>
          className="user-filter-select user-filter-control-item"
          value={roleValue}
          options={roleOptions}
          onChange={onRoleChange}
        />
        <Select<StatusValue>
          className="user-filter-select user-filter-control-item"
          value={statusValue}
          options={statusOptions}
          onChange={onStatusChange}
        />
        <Button className="user-filter-control-item" loading={loading} onClick={onRefresh}>
          刷新
        </Button>
      </div>
    </section>
  );
}
