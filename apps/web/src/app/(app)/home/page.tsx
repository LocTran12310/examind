import { Card, PageHeader } from "@/components/ui";
import { getMe } from "@/lib/session";

export default async function StudentHome() {
  const me = await getMe();
  return (
    <>
      <PageHeader title={`Xin chào, ${me?.full_name ?? ""}`} subtitle={me?.org.name} />
      <Card>Chưa có bài được giao.</Card>
    </>
  );
}
