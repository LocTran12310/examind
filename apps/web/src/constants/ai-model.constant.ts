import type { Provider } from "@/interfaces/ai-model.interface";

export const PROVIDER_LABEL: Record<Provider, string> = {
  ollama: "Ollama (máy chủ riêng)",
  openai: "Tương thích OpenAI",
  anthropic: "Anthropic",
};

export const PROVIDER_OPTIONS = Object.entries(PROVIDER_LABEL).map(([value, label]) => ({ value, label }));

export const MODEL_ENABLED_OPTIONS = [
  { value: "true", label: "Đang bật" },
  { value: "false", label: "Đã tắt" },
];
