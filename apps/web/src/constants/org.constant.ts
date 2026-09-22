import type { OrgAction } from "@/dtos/org.dto";

/** Confirmation asked before a status change of the selected orgs. */
export const ORG_ACTION_CONFIRM: Record<Exclude<OrgAction, "delete">, string> = {
  suspend: "Khóa tổ chức? Người dùng của tổ chức sẽ không đăng nhập được.",
  activate: "Mở khóa tổ chức?",
};
