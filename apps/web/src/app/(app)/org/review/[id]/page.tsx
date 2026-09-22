"use client";

import { use } from "react";
import { ReviewDocumentPage } from "@/components/page-components/ReviewDocument/ReviewDocumentPage";

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <ReviewDocumentPage id={id} />;
}
