import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ModelForm } from "@/components/page-components/AiModels/ModelForm/ModelForm";
import { emptyDraft } from "@/lib/page-libs/ai-models/model-draft";
import { MeProvider } from "@/hooks/common/use-me";
import AiModelsPage from "@/app/(app)/org/ai-models/page";
import type { AiModel } from "@/interfaces/ai-model.interface";
import { me, mockFetch, renderWithQuery as render, route, searchPage } from "./helpers";
import { setUrl } from "./router-mock";

vi.mock("next/navigation", async () => (await import("./router-mock")).routerMock);

const model = (o: Partial<AiModel>): AiModel => ({
  id: "m1", name: "Qwen", provider: "ollama", model: "qwen2.5:7b", base_url: "http://ollama:11434", capabilities: ["text"],
  is_free: true, enabled: true, system: false, has_key: false, editable: true, ...o,
});

afterEach(() => vi.unstubAllGlobals());

describe("ai models", () => {
  it("badges show system/free/paid/key and the toolbar tests the selected models", async () => {
    setUrl("/org/ai-models");
    mockFetch(
      route("POST", "/api/ai-models/search", searchPage([model({ id: "s", name: "Sys", system: true, editable: false }), model({ id: "p", name: "GPT", provider: "openai", is_free: false, has_key: true })])),
      route("POST", "/api/ai-models/p/test", { ok: true, latency_ms: 120 }),
    );
    const u = userEvent.setup();
    render(
      <MeProvider value={me("org_admin")}>
        <AiModelsPage />
      </MeProvider>,
    );
    const sys = (await screen.findByTestId("model-Sys")).closest("tr")!;
    expect(sys).toHaveTextContent("Hệ thống");
    const gpt = screen.getByTestId("model-GPT").closest("tr")!;
    expect(gpt).toHaveTextContent("Trả phí");
    expect(gpt).toHaveTextContent("Có khóa");
    await u.click(within(sys).getByRole("checkbox"));
    expect(screen.getByRole("button", { name: "Bật/Tắt" })).toBeDisabled(); // system models are read-only
    await u.click(within(sys).getByRole("checkbox"));
    await u.click(within(gpt).getByRole("checkbox"));
    await u.click(screen.getByRole("button", { name: "Kiểm tra" }));
    await waitFor(() => expect(gpt).toHaveTextContent("OK · 120 ms"));
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
