import { redirect } from "next/navigation";
import { getMe } from "@/lib/session";
import { AppShell } from "./AppShell";
import { SessionRecovery } from "./SessionRecovery";

export const dynamic = "force-dynamic";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const me = await getMe();
  if (!me) return <SessionRecovery />;
  if (me.must_change_password) redirect("/change-password");
  return <AppShell me={me}>{children}</AppShell>;
}
