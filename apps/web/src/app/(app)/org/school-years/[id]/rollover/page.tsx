"use client";

import { use } from "react";
import { RolloverPage } from "@/components/page-components/Rollover/RolloverPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <RolloverPage yearId={id} />;
}
