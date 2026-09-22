import { useState } from "react";
import { toast } from "sonner";
import { useDiscoverAiModelsMutation } from "@/hooks/react-query/use-query-ai-model";
import { ApiError } from "@/lib/common/http";

/** Ask an Ollama server (default: the server's OLLAMA_URL) which models it has. */
export function useDiscoverModels() {
  const [url, setUrl] = useState("");
  const discover = useDiscoverAiModelsMutation();
  return {
    url,
    setUrl,
    busy: discover.isPending,
    found: discover.data ?? null,
    run: () => discover.mutate({ base_url: url || null }, { onError: (e) => toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra") }),
  };
}
