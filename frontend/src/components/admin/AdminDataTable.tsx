import { Card, Table } from "antd";
import type { TableColumnsType } from "antd";
import type { Key } from "react";

interface AdminDataTableProps<T extends object> {
  rowKey: keyof T | ((record: T) => Key);
  columns: TableColumnsType<T>;
  dataSource: T[];
  loading: boolean;
  page: number;
  pageSize: number;
  total: number;
  totalLabel: string;
  onPageChange: (page: number, pageSize: number) => void;
}

export function AdminDataTable<T extends object>({
  rowKey,
  columns,
  dataSource,
  loading,
  page,
  pageSize,
  total,
  totalLabel,
  onPageChange
}: AdminDataTableProps<T>) {
  return (
    <Card className="admin-table-panel" styles={{ body: { padding: 0 } }}>
      <Table<T>
        rowKey={rowKey}
        columns={columns}
        dataSource={dataSource}
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showTotal: (count) => `共 ${count} ${totalLabel}`
        }}
        onChange={(pagination) => onPageChange(pagination.current || 1, pagination.pageSize || pageSize)}
      />
    </Card>
  );
}
