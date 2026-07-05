import { Button, Input, Select } from "antd";

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
  onSearchChange,
  onSearchSubmit,
  onRoleChange,
  onStatusChange,
  onRefresh
}: AdminFilterBarProps<RoleValue, StatusValue>) {
  return (
    <section className="user-filter-bar" aria-label={title}>
      <div className="user-filter-copy">
        <span>{title}</span>
        <strong>共 {total.toLocaleString("zh-CN")} 条</strong>
      </div>
      <div className="user-filter-controls">
        <Input.Search
          allowClear
          className="user-filter-search"
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          onSearch={onSearchSubmit}
        />
        <Select<RoleValue>
          className="user-filter-select"
          value={roleValue}
          options={roleOptions}
          onChange={onRoleChange}
        />
        <Select<StatusValue>
          className="user-filter-select"
          value={statusValue}
          options={statusOptions}
          onChange={onStatusChange}
        />
        <Button loading={loading} onClick={onRefresh}>
          刷新
        </Button>
      </div>
    </section>
  );
}
