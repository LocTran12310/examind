import { redirect } from "next/navigation";
import { homeFor } from "@/lib/common/nav";
import { getMe } from "@/lib/common/session";

export default async function Root() {
  const me = await getMe();
  redirect(me ? homeFor(me.role) : "/login");
}
