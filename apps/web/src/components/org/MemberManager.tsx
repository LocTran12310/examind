"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { UserPlus } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { FormDialog } from "@/components/app/FormDialog";
import { DataTable } from "@/components/data-table/DataTable";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { qs, useApi } from "@/lib/hooks";
import type { Page, User } from "@/lib/types";

const COLUMNS: ColumnDef<User, unknown>[] = [
  {
    accessorKey: "full_name",
    header: "Họ tên",
    cell: ({ row }) => (
      <Link href={`/org/students/${row.original.id}`} className="text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
        {row.original.full_name}
      </Link>
    ),
    meta: { filter: { kind: "text" }, sort: "full_name" },
  },
  { accessorKey: "username", header: "Tên đăng nhập", cell: ({ row }) => <span className="font-mono">{row.original.username}</span>, meta: { filter: { kind: "text" }, sort: "username" } },
];

function AddStudents({ classId, onAdded }: { classId: string; onAdded: () => void }) {
  const [q, setQ] = useState("");
  const [added, setAdded] = useState<Set<string>>(new Set());
  const { data } = useApi<Page<User>>(q.trim().length >= 2 ? `/users${qs({ q, role: "student", page_size: 20 })}` : null);
  return (
    <div className="grid gap-3">
      <Input autoFocus aria-label="Tìm học sinh" placeholder="Tìm tên hoặc tên đăng nhập (≥ 2 ký tự)" value={q} onChange={(e) => setQ(e.target.value)} />
      <ul className="max-h-80 divide-y overflow-y-auto">
        {data?.items
          .filter((u) => !u.class_ids.includes(classId) && !added.has(u.id))
          .map((u) => (
            <li key={u.id} className="flex items-center justify-between py-2 text-sm">
              <span>
                {u.full_name} <span className="font-mono text-muted-foreground">{u.username}</span>
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  try {
                    await api(`/classes/${classId}/members`, { body: { user_ids: [u.id] } });
                    setAdded((s) => new Set(s).add(u.id));
                    onAdded();
                  } catch (e) {
                    toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
                  }
                }}
              >
                Thêm
              </Button>
            </li>
          ))}
      </ul>
    </div>
  );
}

/** Students of one class as a server-paged table (`prefix` keeps its URL params apart). */
export function MemberManager({ classId, prefix = "m.", onChange }: { classId: string; prefix?: string; onChange?: () => void }) {
  const [adding, setAdding] = useState(false);
  const [version, setVersion] = useState(0);
  const params = useMemo(() => ({ class_id: classId }), [classId]);
  const changed = () => (setVersion((v) => v + 1), onChange?.());
  return (
    <>
      <DataTable
        path="/users"
        prefix={prefix}
        params={params}
        columns={COLUMNS}
        getRowId={(u) => u.id}
        reloadKey={version}
        onDelete={async (rows) => {
          for (const u of rows) await api(`/classes/${classId}/members/${u.id}`, { method: "DELETE" });
          onChange?.();
        }}
        deleteLabel={(rows) => `Xóa ${rows.length} học sinh khỏi lớp?`}
        actions={() => (
          <ToolbarButton onClick={() => setAdding(true)}>
            <UserPlus /> Thêm học sinh
          </ToolbarButton>
        )}
        emptyText="Lớp chưa có học sinh."
      />
      <FormDialog open={adding} onOpenChange={setAdding} title="Thêm học sinh vào lớp">
        <AddStudents classId={classId} onAdded={changed} />
      </FormDialog>
    </>
  );
}
