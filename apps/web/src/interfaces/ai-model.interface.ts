export type Provider = "ollama" | "openai" | "anthropic";

export type ModelCapability = "text" | "vision";

export interface AiModel {
  id: string;
  name: string;
  provider: Provider;
  model: string;
  base_url: string | null;
  capabilities: ModelCapability[];
  is_free: boolean;
  enabled: boolean;
  system: boolean;
  has_key: boolean;
  editable: boolean;
}

/** A model an Ollama server offers (`POST /ai-models/discover`). */
export interface DiscoveredModel {
  model: string;
  parameter_size?: string;
  capabilities: ModelCapability[];
}

export interface DiscoverResult {
  base_url: string;
  models: DiscoveredModel[];
  error?: string;
}

/** Answer of `POST /ai-models/{id}/test`. */
export interface ModelTestResult {
  ok: boolean;
  latency_ms?: number | null;
  error?: string | null;
}

/** Test result per model id while the AI models page is open. */
export type ModelTestState = Record<string, ModelTestResult | "running">;

/** What the model form edits (the stored key is never sent back). */
export interface ModelDraft {
  name: string;
  provider: Provider;
  model: string;
  base_url: string;
  api_key: string;
  capabilities: ModelCapability[];
  is_free: boolean;
}
