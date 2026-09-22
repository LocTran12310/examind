import { useEffect, useState } from "react";
import { ORG_KEY } from "@/constants/auth.constant";
import { useLoginMutation } from "@/hooks/react-query/use-query-auth";
import type { Me } from "@/interfaces/auth.interface";
import { ApiError } from "@/lib/common/http";
import { homeFor } from "@/lib/common/nav";

function readOrg(): string {
  try {
    return localStorage.getItem(ORG_KEY) ?? "";
  } catch {
    return "";
  }
}

/** Org code (remembered from the last login), username and password; `onSuccess` replaces the redirect. */
export function useLoginForm(onSuccess?: (me: Me) => void) {
  const [org, setOrg] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const login = useLoginMutation();

  useEffect(() => setOrg(readOrg()), []);

  return {
    org,
    setOrg,
    username,
    setUsername,
    password,
    setPassword,
    busy: login.isPending,
    error: login.error ? (login.error instanceof ApiError ? login.error.message : "Không kết nối được máy chủ") : null,
    submit: () =>
      login.mutate(
        { org_code: org, username, password },
        {
          onSuccess: (me) => {
            try {
              localStorage.setItem(ORG_KEY, org);
            } catch {}
            if (onSuccess) onSuccess(me);
            // a full load: the app layout reads the new session on the server
            else window.location.assign(me.must_change_password ? "/change-password" : homeFor(me.role));
          },
        },
      ),
  };
}
