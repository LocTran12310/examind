import { useState } from "react";
import { toast } from "sonner";
import { useSwitchOrg } from "@/hooks/common/use-switch-org";
import { useMyOrgsQuery } from "@/hooks/react-query/use-query-auth";
import type { Me, MyOrg } from "@/interfaces/auth.interface";
import { ApiError } from "@/lib/common/http";

/** The header org selector: my orgs, and switching to one of them. */
export function useOrgSwitcher(me: Me) {
  const [open, setOpen] = useState(false);
  const { data } = useMyOrgsQuery();
  const { busy, switchTo } = useSwitchOrg();
  const orgs = data ?? [];
  return {
    open,
    setOpen,
    busy,
    single: orgs.length <= 1,
    searchable: orgs.length > 6,
    // before the list arrives, the current org alone
    orgs: orgs.length ? orgs : [{ ...me.org, role: me.role, is_home: true }],
    choose: async (o: MyOrg) => {
      setOpen(false);
      if (o.id === me.org.id) return;
      try {
        await switchTo(o.id);
      } catch (e) {
        toast.error(e instanceof ApiError ? e.message : "Không chuyển được tổ chức");
      }
    },
  };
}
