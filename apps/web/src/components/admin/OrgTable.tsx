"use client";

import { Badge, Button, Table, td, th } from "@/components/ui";
import type { Org } from "@/lib/types";

export function OrgTable({
  orgs,
  onEdit,
  onAction,
}: {
  orgs: Org[];
  onEdit: (o: Org) => void;
  onAction: (o: Org, action: "suspend" | "activate" | "delete") => void;
}) {
  return (
    <Table>
      <thead className="bg-gray-50">
        <tr>
          <th className={th}>Mã</th>
          <th className={th}>Tên</th>
          <th className={th}>Trạng thái</th>
          <th className={th}>Người dùng</th>
          <th className={th}>Ngày tạo</th>
          <th className={th} />
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {orgs.map((o) => (
          <tr key={o.id} data-testid={`org-${o.code}`}>
            <td className={`${td} font-mono`}>{o.code}</td>
            <td className={td}>{o.name}</td>
            <td className={td}>
              {o.deleted_at ? (
                <Badge tone="red">Đã xóa</Badge>
              ) : o.status === "active" ? (
                <Badge tone="green">Hoạt động</Badge>
              ) : (
                <Badge tone="amber">Tạm khóa</Badge>
              )}
              {o.is_system && <span className="ml-1"><Badge tone="blue">Hệ thống</Badge></span>}
            </td>
            <td className={td}>{o.user_count}</td>
            <td className={td}>{new Date(o.created_at).toLocaleDateString("vi-VN")}</td>
            <td className={`${td} text-right whitespace-nowrap`}>
              <div className="flex justify-end gap-1">
                <Button size="sm" onClick={() => onEdit(o)}>
                  Sửa
                </Button>
                {!o.is_system && !o.deleted_at && (
                  <>
                    {o.status === "active" ? (
                      <Button size="sm" onClick={() => onAction(o, "suspend")}>
                        Khóa
                      </Button>
                    ) : (
                      <Button size="sm" onClick={() => onAction(o, "activate")}>
                        Mở khóa
                      </Button>
                    )}
                    <Button size="sm" variant="danger" onClick={() => onAction(o, "delete")}>
                      Xóa
                    </Button>
                  </>
                )}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
