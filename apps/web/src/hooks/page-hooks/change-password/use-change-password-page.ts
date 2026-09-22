import { useState } from "react";
import { useChangePasswordMutation } from "@/hooks/react-query/use-query-auth";
import { ApiError } from "@/lib/common/http";
import { homeFor } from "@/lib/nav";

/** New password twice (checked here), then the role's home page. */
export function useChangePasswordPage() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);
  const change = useChangePasswordMutation();
  const err = change.error;
  const fields: Record<string, string> = err instanceof ApiError && err.fields ? err.fields : {};
  const error = err && !(err instanceof ApiError && err.fields) ? (err instanceof ApiError ? err.message : "Có lỗi xảy ra") : null;
  return {
    current,
    setCurrent,
    next,
    setNext,
    confirm,
    setConfirm,
    errors: mismatch ? { confirm: "Mật khẩu nhập lại không khớp" } : fields,
    error: mismatch ? null : error,
    submit: () => {
      setMismatch(false);
      change.reset();
      if (next !== confirm) return setMismatch(true);
      // a full load: the app layout reads the session (no longer "must change password") on the server
      change.mutate({ current_password: current, new_password: next }, { onSuccess: (me) => window.location.assign(homeFor(me.role)) });
    },
  };
}
