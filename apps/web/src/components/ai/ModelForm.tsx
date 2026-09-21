"use client";

import { useState } from "react";
import { Alert, Button, Field, Input, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import { PROVIDER_LABEL, type AiModel, type Provider } from "@/lib/types";

export interface ModelDraft {
  name: string;
  provider: Provider;
  model: string;
  base_url: string;
  api_key: string;
  capabilities: ("text" | "vision")[];
  is_free: boolean;
}

export const emptyDraft = (p: Partial<ModelDraft> = {}): ModelDraft => ({
  name: "", provider: "ollama", model: "", base_url: "", api_key: "", capabilities: ["text"], is_free: true, ...p,
});

export function ModelForm({ initial, existing, onDone }: { initial: ModelDraft; existing?: AiModel; onDone: () => void }) {
  const [d, setD] = useState<ModelDraft>(initial);
  const m = useMutation();
  const set = <K extends keyof ModelDraft>(k: K, v: ModelDraft[K]) => setD((x) => ({ ...x, [k]: v }));
  const toggleCap = (c: "text" | "vision") =>
    set("capabilities", d.capabilities.includes(c) ? d.capabilities.filter((x) => x !== c) : [...d.capabilities, c]);

  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const body: Record<string, unknown> = { ...d, base_url: d.base_url || null };
        if (existing && !d.api_key) delete body.api_key; // keep the stored key
        if (!existing && !d.api_key) body.api_key = null;
        const r = await m.run(() => (existing ? api(`/ai-models/${existing.id}`, { method: "PATCH", body }) : api("/ai-models", { body })));
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <Alert>{m.message}</Alert>}
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Tên hiển thị" error={m.fields.name}>
          <Input value={d.name} onChange={(e) => set("name", e.target.value)} placeholder="Qwen 2.5 7B (máy chủ trung tâm)" required />
        </Field>
        <Field label="Nhà cung cấp" error={m.fields.provider}>
          <Select className="w-full" value={d.provider} onChange={(e) => set("provider", e.target.value as Provider)}>
            {Object.entries(PROVIDER_LABEL).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Tên model" error={m.fields.model} hint="Ví dụ qwen2.5:7b, gpt-4o-mini, claude-sonnet-5">
          <Input value={d.model} onChange={(e) => set("model", e.target.value)} required />
        </Field>
        <Field label="Base URL" error={m.fields.base_url} hint="Để trống để dùng mặc định của nhà cung cấp">
          <Input value={d.base_url} onChange={(e) => set("base_url", e.target.value)} placeholder="http://ollama:11434" />
        </Field>
        <Field label="Khóa API" error={m.fields.api_key} hint={existing?.has_key ? "Đã có khóa — để trống để giữ nguyên" : "Không cần với Ollama"}>
          <Input type="password" autoComplete="off" value={d.api_key} onChange={(e) => set("api_key", e.target.value)} />
        </Field>
        <div className="space-y-2 text-sm">
          <span className="font-medium text-gray-700">Khả năng</span>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={d.capabilities.includes("text")} onChange={() => toggleCap("text")} /> Văn bản (tách câu, gắn chuyên đề)
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={d.capabilities.includes("vision")} onChange={() => toggleCap("vision")} /> Đọc ảnh (OCR bằng AI)
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={d.is_free} onChange={(e) => set("is_free", e.target.checked)} /> Miễn phí (tự host)
          </label>
        </div>
      </div>
      <div className="flex justify-end">
        <Button variant="primary" type="submit" disabled={m.busy}>
          {existing ? "Lưu" : "Thêm model"}
        </Button>
      </div>
    </form>
  );
}
