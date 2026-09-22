"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/app/Panel";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { TAG_GROUP_LABEL, type Tag } from "@/lib/types";

const GROUPS = Object.keys(TAG_GROUP_LABEL) as Tag["group"][];

export function TagManager({ tags, onChange }: { tags: Tag[]; onChange: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [editing, setEditing] = useState<{ id: string; name: string } | null>(null);

  async function run(fn: () => Promise<unknown>) {
    setError(null);
    try {
      await fn();
      onChange();
      return true;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
      return false;
    }
  }

  return (
    <div className="space-y-4">
      {error && <FormAlert>{error}</FormAlert>}
      <div className="grid gap-4 md:grid-cols-2">
        {GROUPS.map((g) => (
          <Panel key={g} data-testid={`group-${g}`}>
            <h2 className="mb-3 font-medium">{TAG_GROUP_LABEL[g]}</h2>
            <ul className="mb-3 flex flex-wrap gap-2">
              {tags
                .filter((t) => t.group === g)
                .map((t) =>
                  editing?.id === t.id ? (
                    <li key={t.id}>
                      <form
                        className="flex gap-1"
                        onSubmit={async (e) => {
                          e.preventDefault();
                          if (await run(() => api(`/tags/${t.id}`, { method: "PATCH", body: { name: editing.name } }))) setEditing(null);
                        }}
                      >
                        <Input aria-label="Tên tag" className="h-8 w-40" autoFocus value={editing.name} onChange={(e) => setEditing({ id: t.id, name: e.target.value })} />
                        <Button variant="outline" size="sm" type="submit">
                          Lưu
                        </Button>
                      </form>
                    </li>
                  ) : (
                    <li key={t.id} className="flex items-center gap-1 rounded-full bg-muted py-0.5 pl-3 pr-1 text-sm">
                      <button type="button" onClick={() => setEditing({ id: t.id, name: t.name })} title="Đổi tên">
                        {t.name}
                      </button>
                      <button
                        type="button"
                        aria-label={`Xóa ${t.name}`}
                        className="rounded-full px-1.5 text-muted-foreground hover:bg-muted"
                        onClick={() => window.confirm(`Xóa tag "${t.name}"?`) && run(() => api(`/tags/${t.id}`, { method: "DELETE" }))}
                      >
                        ×
                      </button>
                    </li>
                  ),
                )}
            </ul>
            <form
              className="flex gap-2"
              onSubmit={async (e) => {
                e.preventDefault();
                const name = (drafts[g] ?? "").trim();
                if (name && (await run(() => api("/tags", { body: { group: g, name } })))) setDrafts((d) => ({ ...d, [g]: "" }));
              }}
            >
              <Input aria-label={`Tag mới – ${TAG_GROUP_LABEL[g]}`} placeholder="Tag mới" value={drafts[g] ?? ""} onChange={(e) => setDrafts((d) => ({ ...d, [g]: e.target.value }))} />
              <Button variant="outline" type="submit">Thêm</Button>
            </form>
          </Panel>
        ))}
      </div>
    </div>
  );
}
