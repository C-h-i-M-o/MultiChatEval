import { Card, Statistic } from "antd";
import type { ReactNode } from "react";

export interface AdminSummaryItem {
  key: string;
  icon: string;
  title?: string;
  value?: number;
  suffix?: string;
  className?: string;
  content?: ReactNode;
}

interface AdminSummaryGridProps {
  items: AdminSummaryItem[];
}

export function AdminSummaryGrid({ items }: AdminSummaryGridProps) {
  return (
    <div className="quota-summary-grid">
      {items.map((item) => (
        <Card key={item.key} className={`quota-summary-card ${item.className || ""}`.trim()}>
          <span className="quota-summary-icon">{item.icon}</span>
          {item.content ? item.content : <Statistic title={item.title} value={item.value} groupSeparator="," suffix={item.suffix} />}
        </Card>
      ))}
    </div>
  );
}
