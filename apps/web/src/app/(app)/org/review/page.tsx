"use client";

import { useState } from "react";
import { useMe } from "@/app/(app)/AppShell";
import { ReviewList } from "@/components/review/ReviewList";
import { FormAlert } from "@/components/app/FormAlert";
import { EmptyState } from "@/components/app/EmptyState";
import { PageHeader } from "@/components/app/PageHeader";
import { api, ApiError } from "@/lib/api";
import { qs, useApi } from "@/lib/hooks";
import type { Page, ReviewDocument, User } from "@/lib/types";

export default function ReviewPage() {
  const me = useMe();
  const [mine, setMine] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data, reload } = useApi<ReviewDocument[]>(`/review/documents${qs({ mine: mine || undefined })}`);
  const canAssign = me.role === "org_admin";
  const { data: teachers } = useApi<Page<User>>(canAssign ? "/users?role=teacher&page_size=200" : null);
  const pending = (data ?? []).reduce((n, r) => n + r.counts.needs_review + r.spot_pending + (r.counts.flagged ?? 0), 0);

  return (
    <>
      <PageHeader title="Duyệt câu hỏi" description={data ? `${pending} câu đang chờ xem` : undefined} />
      <label className="mb-4 flex items-center gap-2 text-sm text-muted-foreground">
        <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} /> Của tôi
      </label>
      {error && <div className="mb-3"><FormAlert>{error}</FormAlert></div>}
      {data && data.length === 0 && <EmptyState>Không có đề nào cần duyệt.</EmptyState>}
      {data && data.length > 0 && (
        <ReviewList
          rows={data}
          teachers={[...(teachers?.items ?? []), ...(canAssign ? [{ ...me, email: null, is_active: true, last_login_at: null, created_at: "", class_ids: [] }] : [])]}
          canAssign={canAssign}
          onAssign={async (docId, userId) => {
            setError(null);
            try {
              await api(`/review/documents/${docId}`, { method: "PATCH", body: { assigned_to: userId } });
              await reload();
            } catch (e) {
              setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
            }
          }}
        />
      )}
    </>
  );
}
