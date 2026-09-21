"use client";

import Link from "next/link";
import { ClassCreateForm } from "@/components/org/ClassForms";
import { Card, Empty, PageHeader, Table, td, th } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { SchoolClass } from "@/lib/types";

export default function ClassesPage() {
  const { data, reload } = useApi<SchoolClass[]>("/classes");
  return (
    <>
      <PageHeader title="Lớp học" subtitle={data ? `${data.length} lớp` : undefined} />
      <Card className="mb-4">
        <ClassCreateForm onCreated={reload} />
      </Card>
      {data && data.length === 0 && <Empty>Chưa có lớp nào.</Empty>}
      {data && data.length > 0 && (
        <Table>
          <thead className="bg-gray-50">
            <tr>
              <th className={th}>Lớp</th>
              <th className={th}>Khối</th>
              <th className={th}>Năm học</th>
              <th className={th}>Sĩ số</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.map((c) => (
              <tr key={c.id}>
                <td className={td}>
                  <Link className="font-medium text-brand-700 hover:underline" href={`/org/classes/${c.id}`}>
                    {c.name}
                  </Link>
                </td>
                <td className={td}>{c.grade ?? ""}</td>
                <td className={td}>{c.school_year}</td>
                <td className={td}>{c.member_count}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </>
  );
}
