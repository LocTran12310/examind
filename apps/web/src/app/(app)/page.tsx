import { redirect } from "next/navigation";
import { homeFor } from "@/lib/nav";
import { getMe } from "@/lib/session";

export default async function Root() {
  const me = await getMe();
  redirect(me ? homeFor(me.role) : "/login");
}
