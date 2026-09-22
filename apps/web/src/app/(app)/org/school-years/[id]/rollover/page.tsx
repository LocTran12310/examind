"use client";

import { use } from "react";
import { RolloverWizard } from "@/components/years/RolloverWizard";

export default function RolloverPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <RolloverWizard yearId={id} />;
}
