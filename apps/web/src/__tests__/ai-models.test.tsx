import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { emptyDraft, ModelForm } from "@/components/ai/ModelForm";
import { ModelTable } from "@/components/ai/ModelTable";
import type { AiModel } from "@/lib/types";
import { mockFetch, route } from "./helpers";

const model = (o: Partial<AiModel>): AiModel => ({
  id: "m1", name: "Qwen", provider: "ollama", model: "qwen2.5:7b", base_url: "http://ollama:11434", capabilities: ["text"],
  is_free: true, enabled: true, system: false, has_key: false, editable: true, ...o,
});

afterEach(() => vi.unstubAllGlobals());

describe("ai models", () => {
  it("system models are read-only and badges show free/paid/key", () => {
    render(
      <ModelTable
        models={[model({ id: "s", name: "Sys", system: true, editable: false }), model({ id: "p", name: "GPT", provider: "openai", is_free: false, has_key: true })]}
        tests={{ p: { ok: true, latency_ms: 120 } }}
        onTest={() => {}} onEdit={() => {}} onToggle={() => {}} onDelete={() => {}}
      />,
    );
    const sys = screen.getByTestId("model-Sys");
    expect(sys).toHaveTextContent("Hệ thống");
    expect(within(sys).queryByRole("button", { name: "Sửa" })).toBeNull();
    const gpt = screen.getByTestId("model-GPT");
    expect(gpt).toHaveTextContent("Trả phí");
    expect(gpt).toHaveTextContent("Có khóa");
    expect(gpt).toHaveTextContent("OK · 120 ms");
  });

  it("creates a model and never echoes the key", async () => {
    const f = mockFetch(route("POST", "/api/ai-models", model({}), 201));
    const onDone = vi.fn();
    render(<ModelForm initial={emptyDraft({ name: "Qwen", model: "qwen2.5:7b", base_url: "http://ollama:11434" })} onDone={onDone} />);
    await userEvent.click(screen.getByLabelText(/Đọc ảnh/));
    await userEvent.click(screen.getByRole("button", { name: "Thêm model" }));
    await waitFor(() => expect(onDone).toHaveBeenCalled());
    const body = JSON.parse(String(f.mock.calls[0][1]?.body));
    expect(body).toMatchObject({ provider: "ollama", model: "qwen2.5:7b", capabilities: ["text", "vision"], api_key: null });
  });

  it("editing without a new key keeps the stored one", async () => {
    const f = mockFetch(route("PATCH", "/api/ai-models/m1", model({})));
    render(<ModelForm existing={model({ has_key: true })} initial={emptyDraft({ name: "Qwen", model: "q" })} onDone={() => {}} />);
    expect(screen.getByText(/Đã có khóa/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(f).toHaveBeenCalled());
    expect(JSON.parse(String(f.mock.calls[0][1]?.body))).not.toHaveProperty("api_key");
  });
});
