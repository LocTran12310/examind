"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PROVIDER_OPTIONS } from "@/constants/ai-model.constant";
import { useModelForm } from "@/hooks/page-hooks/ai-models/use-model-form";
import type { AiModel, ModelDraft, Provider } from "@/interfaces/ai-model.interface";

export function ModelForm({ initial, existing, onDone }: { initial: ModelDraft; existing?: AiModel; onDone: () => void }) {
  const { draft: d, set, toggleCap, busy, fields, message, submit } = useModelForm(initial, existing, onDone);
  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      {message && !Object.keys(fields).length && <FormAlert>{message}</FormAlert>}
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField label="Tên hiển thị" error={fields.name}>
          <Input value={d.name} onChange={(e) => set("name", e.target.value)} placeholder="Qwen 2.5 7B (máy chủ trung tâm)" required />
        </FormField>
        <FormField label="Nhà cung cấp" error={fields.provider}>
          {(f) => <OptionSelect {...f} value={d.provider} onValueChange={(v) => set("provider", v as Provider)} options={PROVIDER_OPTIONS} />}
        </FormField>
        <FormField label="Tên model" error={fields.model} hint="Ví dụ qwen2.5:7b, gpt-4o-mini, claude-sonnet-5">
          <Input value={d.model} onChange={(e) => set("model", e.target.value)} required />
        </FormField>
        <FormField label="Base URL" error={fields.base_url} hint="Để trống để dùng mặc định của nhà cung cấp">
          <Input value={d.base_url} onChange={(e) => set("base_url", e.target.value)} placeholder="http://ollama:11434" />
        </FormField>
        <FormField label="Khóa API" error={fields.api_key} hint={existing?.has_key ? "Đã có khóa — để trống để giữ nguyên" : "Không cần với Ollama"}>
          <Input type="password" autoComplete="off" value={d.api_key} onChange={(e) => set("api_key", e.target.value)} />
        </FormField>
        <div className="space-y-2 text-sm">
          <span className="font-medium text-foreground/80">Khả năng</span>
          <Label className="font-normal">
            <Checkbox checked={d.capabilities.includes("text")} onCheckedChange={() => toggleCap("text")} /> Văn bản (tách câu, gắn chuyên đề)
          </Label>
          <Label className="font-normal">
            <Checkbox checked={d.capabilities.includes("vision")} onCheckedChange={() => toggleCap("vision")} /> Đọc ảnh (OCR bằng AI)
          </Label>
          <Label className="font-normal">
            <Checkbox checked={d.is_free} onCheckedChange={(v) => set("is_free", v === true)} /> Miễn phí (tự host)
          </Label>
        </div>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={busy}>
          {existing ? "Lưu" : "Thêm model"}
        </Button>
      </div>
    </form>
  );
}
