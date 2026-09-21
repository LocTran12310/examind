"use client";

import { Badge, Button, Table, td, th } from "@/components/ui";
import { ROLE_LABEL, type User } from "@/lib/types";

export function UserTable({
  users,
  meId,
  className,
  onEdit,
  onReset,
  onToggle,
}: {
  users: User[];
  meId: string;
  className: (id: string) => string;
  onEdit: (u: User) => void;
  onReset: (u: User) => void;
  onToggle: (u: User) => void;
}) {
  return (
    <Table>
      <thead className="bg-gray-50">
        <tr>
          <th className={th}>Họ tên</th>
          <th className={th}>Tên đăng nhập</th>
          <th className={th}>Vai trò</th>
          <th className={th}>Lớp</th>
          <th className={th}>Trạng thái</th>
          <th className={th} />
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {users.map((u) => (
          <tr key={u.id} data-testid={`user-${u.username}`} className={u.is_active ? "" : "opacity-60"}>
            <td className={td}>{u.full_name}</td>
            <td className={`${td} font-mono`}>{u.username}</td>
            <td className={td}>{ROLE_LABEL[u.role]}</td>
            <td className={td}>{u.class_ids.map(className).filter(Boolean).join(", ")}</td>
            <td className={td}>
              {!u.is_active ? (
                <Badge tone="red">Đã khóa</Badge>
              ) : u.must_change_password ? (
                <Badge tone="amber">Chờ đổi mật khẩu</Badge>
              ) : (
                <Badge tone="green">Hoạt động</Badge>
              )}
            </td>
            <td className={`${td} whitespace-nowrap text-right`}>
              <div className="flex justify-end gap-1">
                <Button size="sm" onClick={() => onEdit(u)}>
                  Sửa
                </Button>
                <Button size="sm" onClick={() => onReset(u)}>
                  Đặt lại mật khẩu
                </Button>
                {u.id !== meId && (
                  <Button size="sm" variant={u.is_active ? "danger" : "secondary"} onClick={() => onToggle(u)}>
                    {u.is_active ? "Khóa" : "Mở khóa"}
                  </Button>
                )}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
