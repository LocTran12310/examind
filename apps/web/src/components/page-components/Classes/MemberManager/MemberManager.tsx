"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { UserPlus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { DataTable } from "@/components/data-table/DataTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useMemberManager, useStudentSearch } from "@/hooks/page-hooks/classes/use-member-manager";
import type { User } from "@/lib/types";

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

function AddStudents({ classId, onAdd }: { classId: string; onAdd: (userId: string) => Promise<boolean> }) {
  const [q, setQ] = useState("");
  const [added, setAdded] = useState<Set<string>>(new Set());
  const data = useStudentSearch(q);
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
              <Button size="sm" variant="outline" onClick={async () => (await onAdd(u.id)) && setAdded((s) => new Set(s).add(u.id))}>
                Thêm
              </Button>
            </li>
          ))}
      </ul>
    </div>
  );
}

export interface MemberManagerProps {
  classId: string;
  /** keeps its URL params apart from the page's own table */
  prefix?: string;
}

/** Students of one class as a server-paged table; counts elsewhere refresh through the class queries. */
export function MemberManager({ classId, prefix = "m." }: MemberManagerProps) {
  const m = useMemberManager(classId);
  return (
    <>
      <DataTable
        path="/users"
        prefix={prefix}
        params={m.params}
        columns={COLUMNS}
        getRowId={(u) => u.id}
        reloadKey={m.version}
        onDelete={m.removeStudents}
        deleteLabel={(rows) => `Xóa ${rows.length} học sinh khỏi lớp?`}
        actions={() => (
          <ToolbarButton onClick={() => m.setAdding(true)}>
            <UserPlus /> Thêm học sinh
          </ToolbarButton>
        )}
        emptyText="Lớp chưa có học sinh."
      />
      <FormDialog open={m.adding} onOpenChange={m.setAdding} title="Thêm học sinh vào lớp">
        <AddStudents classId={classId} onAdd={m.addStudent} />
      </FormDialog>
    </>
  );
}
