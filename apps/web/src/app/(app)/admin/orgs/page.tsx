"use client";

import { useState } from "react";
import { OrgCreateForm, OrgEditForm } from "@/components/admin/OrgForm";
import { OrgTable } from "@/components/admin/OrgTable";
import { Alert, Button, Input, Modal, PageHeader } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { qs, useApi } from "@/lib/hooks";
import type { Org, Page } from "@/lib/types";

const CONFIRM = {
  suspend: "Khóa tổ chức này? Người dùng sẽ không đăng nhập được.",
  activate: "Mở khóa tổ chức này?",
  delete: "Xóa tổ chức này? Tổ chức sẽ bị ẩn và không đăng nhập được.",
};

export default function OrgsPage() {
  const [q, setQ] = useState("");
  const [showDeleted, setShowDeleted] = useState(false);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Org | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { data, reload } = useApi<Page<Org>>(`/admin/orgs${qs({ q, include_deleted: showDeleted || undefined })}`);

  async function act(o: Org, action: keyof typeof CONFIRM) {
    if (!window.confirm(CONFIRM[action])) return;
    setError(null);
    try {
      if (action === "delete") await api(`/admin/orgs/${o.id}`, { method: "DELETE" });
      else await api(`/admin/orgs/${o.id}/${action}`, { method: "POST" });
      await reload();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
    }
  }

  return (
    <>
      <PageHeader
        title="Tổ chức"
        subtitle={data ? `${data.total} tổ chức` : undefined}
        actions={
          <Button variant="primary" onClick={() => setCreating(true)}>
            Tạo tổ chức
          </Button>
        }
      />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Input placeholder="Tìm theo mã hoặc tên" className="max-w-xs" value={q} onChange={(e) => setQ(e.target.value)} />
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input type="checkbox" checked={showDeleted} onChange={(e) => setShowDeleted(e.target.checked)} /> Hiện tổ chức đã xóa
        </label>
      </div>
      {error && <div className="mb-3"><Alert>{error}</Alert></div>}
      {data && <OrgTable orgs={data.items} onEdit={setEditing} onAction={act} />}
      <Modal
        open={creating}
        title="Tạo tổ chức"
        onClose={() => {
          setCreating(false);
          void reload();
        }}
      >
        <OrgCreateForm
          onDone={() => {
            setCreating(false);
            void reload();
          }}
        />
      </Modal>
      <Modal open={!!editing} title="Sửa tổ chức" onClose={() => setEditing(null)}>
        {editing && (
          <OrgEditForm
            org={editing}
            onDone={() => {
              setEditing(null);
              void reload();
            }}
          />
        )}
      </Modal>
    </>
  );
}
