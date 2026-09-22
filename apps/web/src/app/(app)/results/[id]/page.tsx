"use client";

import { use } from "react";
import { AttemptResultPage } from "@/components/page-components/AttemptResult/AttemptResultPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <AttemptResultPage id={id} />;
}
