import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { MEMBER_ROLE_OPTIONS, ROLE_LABEL } from "@/constants/role.constant";
import type { UpdateMembershipBody } from "@/dtos/org.dto";
import { useAddMembershipMutation, useRemoveMembershipsMutation, useUpdateMembershipsMutation } from "@/hooks/react-query/use-query-membership";
import { useOrgOptionsQuery } from "@/hooks/react-query/use-query-org";
import type { Role } from "@/interfaces/auth.interface";
import type { Membership } from "@/interfaces/org.interface";
import { ApiError } from "@/lib/common/http";
import { formErrors } from "@/lib/common/form-errors";

/** Which side the table shows: an org's members, or an account's organisations. */
export type MembershipTableSide = { kind: "org"; orgId: string; orgName: string } | { kind: "user"; userId: string; userName: string };

const serviceSide = (side: MembershipTableSide) => (side.kind === "org" ? { org_id: side.orgId } : { user_id: side.userId });

/** Columns, role / lock changes and removal of one side's memberships. */
export function useMembershipTable(side: MembershipTableSide) {
  const [adding, setAdding] = useState(false);
  const [history, setHistory] = useState(false);
  const id = side.kind === "org" ? side.orgId : side.userId;
  const params = useMemo(() => (side.kind === "org" ? { org_id: id } : { user_id: id }), [side.kind, id]);
  const update = useUpdateMembershipsMutation(params);
  const remove = useRemoveMembershipsMutation(params);

  const columns = useMemo<ColumnDef<Membership, unknown>[]>(
    () => [
      ...(side.kind === "org"
        ? [
            { accessorKey: "full_name", header: "Họ tên", meta: { filter: { kind: "text" }, sort: "full_name" } } as ColumnDef<Membership, unknown>,
            { accessorKey: "username", header: "Tên đăng nhập", cell: ({ row }) => <span className="font-mono">{row.original.home_org_code}/{row.original.username}</span>, meta: { filter: { kind: "text" } } } as ColumnDef<Membership, unknown>,
          ]
        : [{ accessorKey: "org_name", header: "Tổ chức", cell: ({ row }) => `${row.original.org_name} (${row.original.org_code})`, meta: { filter: { kind: "text" } } } as ColumnDef<Membership, unknown>]),
      { accessorKey: "role", header: "Vai trò", cell: ({ row }) => ROLE_LABEL[row.original.role], meta: { filter: { kind: "select", options: MEMBER_ROLE_OPTIONS } } },
      {
        id: "status",
        header: "Trạng thái",
        cell: ({ row }) => (
          <span className="inline-flex gap-1">
            {row.original.is_home ? <ToneBadge tone="blue">Tổ chức gốc</ToneBadge> : null}
            {row.original.is_active ? <ToneBadge tone="green">Hoạt động</ToneBadge> : <ToneBadge tone="red">Đã khóa</ToneBadge>}
          </span>
        ),
      },
    ],
    [side.kind],
  );

  async function patch(rows: Membership[], body: UpdateMembershipBody) {
    try {
      await update.mutateAsync({ rows, body });
    } catch (e) {
      toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return {
    params,
    columns,
    adding,
    setAdding,
    history,
    setHistory,
    setRole: (rows: Membership[], role: Role) => patch(rows, { role }),
    // the home org cannot be locked or removed
    lock: (rows: Membership[]) => patch(rows.filter((m) => !m.is_home), { is_active: false }),
    unlock: (rows: Membership[]) => patch(rows.filter((m) => !m.is_home), { is_active: true }),
    removeRows: (rows: Membership[]) => remove.mutateAsync(rows.filter((m) => !m.is_home)),
  };
}

/** Add a membership: by home org code + username (org side) or by picking an org (account side). */
export function useMembershipAddForm(side: MembershipTableSide, onDone: () => void) {
  const [orgCode, setOrgCode] = useState("");
  const [username, setUsername] = useState("");
  const [orgId, setOrgId] = useState("");
  const [role, setRole] = useState<string>("teacher");
  const add = useAddMembershipMutation(serviceSide(side));
  const { data: orgs } = useOrgOptionsQuery(side.kind === "user");
  const { fields, message } = formErrors(add.error);
  return {
    orgCode,
    setOrgCode,
    username,
    setUsername,
    orgId,
    setOrgId,
    role,
    setRole,
    orgOptions: (orgs ?? []).filter((o) => !o.is_system && !o.deleted_at).map((o) => ({ value: o.id, label: `${o.name} (${o.code})` })),
    busy: add.isPending,
    fields,
    message,
    submit: () => add.mutate(side.kind === "org" ? { org_code: orgCode, username, role } : { org_id: orgId, role }, { onSuccess: onDone }),
  };
}
