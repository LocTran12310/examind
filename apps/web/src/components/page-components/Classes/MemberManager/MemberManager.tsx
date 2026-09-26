"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { UserPlus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ToolbarButton } from "@/components/common/DataTable/Toolbar";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMemberManager, useStudentSearch } from "@/hooks/page-hooks/classes/use-member-manager";
import { useUserSearchQuery } from "@/hooks/react-query/use-query-user";
import type { User } from "@/interfaces/user.interface";
import { FromClass } from "../FromClass/FromClass";

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
  const students = useStudentSearch(q);
  return (
    <div className="grid gap-3">
      <Input autoFocus aria-label="Tìm học sinh" placeholder="Tìm tên hoặc tên đăng nhập (≥ 2 ký tự)" value={q} onChange={(e) => setQ(e.target.value)} />
      <ul className="max-h-80 divide-y overflow-y-auto">
        {students
          ?.filter((u) => !u.class_ids.includes(classId) && !added.has(u.id))
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
        useRows={useUserSearchQuery}
        prefix={prefix}
        params={m.params}
        columns={COLUMNS}
        getRowId={(u) => u.id}
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
        {/* two doors, because the two jobs are different sizes: one student somebody names, or the class that
            came before this one. Searching 25 names one at a time was the only door there used to be. */}
        <Tabs defaultValue="from-class">
          <TabsList aria-label="Cách thêm học sinh" className="mb-3">
            <TabsTrigger value="from-class">Từ lớp cũ</TabsTrigger>
            <TabsTrigger value="search">Tìm từng em</TabsTrigger>
          </TabsList>
          <TabsContent value="from-class">
            <FromClass classId={classId} onAdd={async (ids) => {
              const ok = await m.addStudents(ids);
              if (ok) m.setAdding(false);
              return ok;
            }} />
          </TabsContent>
          <TabsContent value="search">
            <AddStudents classId={classId} onAdd={m.addStudent} />
          </TabsContent>
        </Tabs>
      </FormDialog>
    </>
  );
}
