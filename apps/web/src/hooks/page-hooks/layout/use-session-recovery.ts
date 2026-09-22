import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useRefreshSessionMutation } from "@/hooks/react-query/use-query-auth";

/** Access cookie expired: try the refresh cookie once, then fall back to /login. */
export function useSessionRecovery() {
  const router = useRouter();
  const { mutate } = useRefreshSessionMutation();
  useEffect(() => {
    mutate(undefined, {
      onSuccess: () => router.refresh(),
      onError: () => window.location.assign("/login"),
    });
  }, [mutate, router]);
}
