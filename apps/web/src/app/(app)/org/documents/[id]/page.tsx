"use client";

import { use } from "react";
import { DocumentDetailPage } from "@/components/page-components/DocumentDetail/DocumentDetailPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <DocumentDetailPage id={id} />;
}
