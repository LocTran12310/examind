import { useState } from "react";
import { ApiError } from "@/lib/common/http";
import { useClassOverviewQuery, useClassQuery, useRefreshClassOverview } from "@/hooks/react-query/use-query-class";

/** One class: header, learning overview and the personal-review dialog. */
export function useClassDetailPage(id: string) {
  const klass = useClassQuery(id);
  const { data: overview } = useClassOverviewQuery(id);
  const refreshOverview = useRefreshClassOverview(id);
  const [adaptive, setAdaptive] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  return {
    data: klass.data,
    error: klass.error ? (klass.error instanceof ApiError ? klass.error.message : "Không tải được dữ liệu") : null,
    overview,
    adaptive,
    setAdaptive,
    notice,
    assigned: (n: number) => {
      setAdaptive(false);
      setNotice(`Đã tạo ${n} đề ôn riêng cho học sinh.`);
      void refreshOverview();
    },
  };
}
