import type { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { ToneBadge } from "@/components/app/ToneBadge";
import { filterKinds } from "@/components/common/DataTable/DataTable";
import { ROLE_LABEL } from "@/constants/role.constant";
import { useMe } from "@/hooks/common/use-me";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useClassOptionsQuery } from "@/hooks/react-query/use-query-class";
import { useFetchAllUsers, useResetPasswordMutation, useSetUsersActiveMutation, useUnlinkUsersMutation } from "@/hooks/react-query/use-query-user";
import type { Credential, User } from "@/interfaces/user.interface";
import { ApiError } from "@/lib/common/http";
import { toSearchBody } from "@/lib/common/search-body";
import { downloadText, toCsv } from "@/lib/csv";
import { fmt } from "@/lib/dates";

const failed = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");

function status(u: User) {
  if (!u.is_active) return <ToneBadge tone="red">Đã khóa</ToneBadge>;
  if (u.must_change_password) return <ToneBadge tone="amber">Chờ đổi mật khẩu</ToneBadge>;
  return <ToneBadge tone="green">Hoạt động</ToneBadge>;
}

/** Columns, dialogs and toolbar actions of the Users page (teachers see and manage students only). */
export function useUsersPage() {
  const me = useMe();
  const tq = useTableQuery();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [resetFor, setResetFor] = useState<User | null>(null);
  const [reset, setReset] = useState<Credential | null>(null);
  const [linking, setLinking] = useState(false);
  const [unlinking, setUnlinking] = useState<User[] | null>(null);
  const { data: classes } = useClassOptionsQuery();
  const classById = useMemo(() => new Map(classes?.map((c) => [c.id, c]) ?? []), [classes]);
  const setActive = useSetUsersActiveMutation();
  const resetPassword = useResetPasswordMutation();
  const unlink = useUnlinkUsersMutation();
  const fetchAll = useFetchAllUsers();

  const columns = useMemo<ColumnDef<User, unknown>[]>(
    () => [
      {
        accessorKey: "full_name",
        header: "Họ tên",
        cell: ({ row }) => (
          <span className="inline-flex items-center gap-2">
            {row.original.role === "student" ? (
              <Link href={`/org/students/${row.original.id}`} className="text-primary hover:underline">
                {row.original.full_name}
              </Link>
            ) : (
              row.original.full_name
            )}
            {row.original.is_home === false && <ToneBadge tone="blue">Từ {row.original.home_org_code}</ToneBadge>}
          </span>
        ),
        meta: { filter: { kind: "text" }, sort: "full_name" },
      },
      { accessorKey: "username", header: "Tên đăng nhập", cell: ({ row }) => <span className="font-mono">{row.original.username}</span>, meta: { filter: { kind: "text" }, sort: "username" } },
      ...(me.role === "org_admin"
        ? [
            {
              accessorKey: "role",
              header: "Vai trò",
              cell: ({ row }) => ROLE_LABEL[row.original.role],
              meta: { filter: { kind: "select", options: (["student", "teacher", "org_admin"] as const).map((r) => ({ value: r, label: ROLE_LABEL[r] })) }, sort: "role" },
            } satisfies ColumnDef<User, unknown>,
          ]
        : []),
      {
        id: "class_id",
        header: "Lớp",
        cell: ({ row }) => row.original.class_ids.map((id) => classById.get(id)?.name).filter(Boolean).join(", "),
        // a parameter of the users search (members of one class), not a column filter
        meta: { filter: { kind: "select", param: true, options: (classes ?? []).map((c) => ({ value: c.id, label: `${c.name} (${c.school_year})` })) } },
      },
      { accessorKey: "is_active", header: "Trạng thái", cell: ({ row }) => status(row.original), meta: { filter: { kind: "select", options: [{ value: "true", label: "Hoạt động" }, { value: "false", label: "Đã khóa" }] } } },
      {
        accessorKey: "last_login_at",
        header: "Đăng nhập gần nhất",
        cell: ({ row }) => fmt(row.original.last_login_at),
        meta: { filter: { kind: "date" }, sort: "last_login_at" },
      },
    ],
    [me.role, classes, classById],
  );

  async function changeActive(users: User[], active: boolean) {
    try {
      await setActive.mutateAsync({ ids: users.filter((u) => u.id !== me.id).map((u) => u.id), active });
      toast.success(active ? "Đã mở khóa" : "Đã khóa");
    } catch (e) {
      failed(e);
    }
  }

  return {
    me,
    columns,
    creating,
    setCreating,
    editing,
    setEditing,
    resetFor,
    setResetFor,
    reset,
    setReset,
    linking,
    setLinking,
    unlinking,
    setUnlinking,
    lock: (users: User[]) => changeActive(users, false),
    unlock: (users: User[]) => changeActive(users, true),
    confirmReset: async () => {
      const u = resetFor!;
      setResetFor(null);
      try {
        setReset(await resetPassword.mutateAsync(u.id));
      } catch (e) {
        failed(e);
      }
    },
    linked: (u: User) => {
      setLinking(false);
      toast.success(`Đã thêm ${u.full_name}`);
    },
    confirmUnlink: async () => {
      const rows = unlinking ?? [];
      setUnlinking(null);
      try {
        await unlink.mutateAsync(rows.map((u) => u.id));
      } catch (e) {
        failed(e);
      }
    },
    /** Every row of the current filters as CSV. */
    exportCsv: async () => {
      const users = await fetchAll(toSearchBody(tq.apiParams, filterKinds(columns)));
      const rows = users.map((u) => ({ full_name: u.full_name, username: u.username, email: u.email ?? "", role: ROLE_LABEL[u.role], classes: u.class_ids.map((id) => classById.get(id)?.name).join(" ") }));
      downloadText("nguoi-dung.csv", toCsv(rows, [["full_name", "Họ tên"], ["username", "Tên đăng nhập"], ["email", "Email"], ["role", "Vai trò"], ["classes", "Lớp"]]));
    },
  };
}
