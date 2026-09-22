"use client";

import { use } from "react";
import { DocumentDetail } from "@/components/documents/DocumentDetail";

export default function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <DocumentDetail id={id} />;
}
