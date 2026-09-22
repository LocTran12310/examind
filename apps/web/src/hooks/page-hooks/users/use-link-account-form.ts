import { useState } from "react";
import { useLinkUserMutation } from "@/hooks/react-query/use-query-user";
import type { User } from "@/interfaces/user.interface";
import { formErrors } from "@/lib/common/form-errors";

/** An account of another org (home org code + username) joins this org with a role. */
export function useLinkAccountForm(onDone: (u: User) => void) {
  const [orgCode, setOrgCode] = useState("");
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("teacher");
  const link = useLinkUserMutation();
  const { fields, message } = formErrors(link.error);
  return {
    orgCode,
    setOrgCode,
    username,
    setUsername,
    role,
    setRole,
    busy: link.isPending,
    fields,
    message,
    submit: () => link.mutate({ org_code: orgCode, username, role }, { onSuccess: onDone }),
  };
}
