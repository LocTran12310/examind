import { useRouter } from "next/navigation";
import { useLogoutMutation } from "@/hooks/react-query/use-query-auth";

/** Sign out: the session ends on the server, the cache is cleared, then the login page. */
export function useUserMenu() {
  const router = useRouter();
  const logout = useLogoutMutation();
  return {
    logout: async () => {
      await logout.mutateAsync();
      router.push("/login");
      router.refresh();
    },
  };
}
