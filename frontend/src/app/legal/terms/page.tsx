import type { Metadata } from "next";
import { LegalPageTemplate } from "@/components/legal/legal-page-template";
import { legalContent, legalPages } from "@/content/legal";

export const metadata: Metadata = {
  title: `${legalPages.terms.title} | Le Frame CIOS`,
  description: "Terms of Use for Le Frame Inc. and authorized CIOS platform users.",
};

export default function TermsPage() {
  return <LegalPageTemplate title={legalPages.terms.title} content={legalContent.terms} />;
}
