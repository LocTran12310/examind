import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getMe } from "@/lib/session";
import { AppShell } from "./AppShell";
import { SessionRecovery } from "./SessionRecovery";

export const dynamic = "force-dynamic";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const me = await getMe();
  if (!me) return <SessionRecovery />;
  if (me.must_change_password) redirect("/change-password");
  const sidebar = (await cookies()).get("sidebar_state")?.value;
  return (
    <AppShell me={me} sidebarOpen={sidebar !== "false"}>
      {children}
    </AppShell>
  );
}
