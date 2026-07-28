import type { Metadata } from "next";
import { LegalPageTemplate } from "@/components/legal/legal-page-template";
import { legalContent, legalPages } from "@/content/legal";

export const metadata: Metadata = {
  title: `${legalPages.legal.title} | Le Frame CIOS`,
  description: "Legal Notice for Le Frame Inc. and authorized CIOS platform users.",
};

export default function LegalNoticePage() {
  return <LegalPageTemplate title={legalPages.legal.title} content={legalContent.legal} />;
}
