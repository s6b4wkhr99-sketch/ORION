import type { Metadata } from "next";
import { LegalPageTemplate } from "@/components/legal/legal-page-template";
import { legalContent, legalPages } from "@/content/legal";

export const metadata: Metadata = {
  title: `${legalPages.privacy.title} | Le Frame CIOS`,
  description: "Privacy Policy for Le Frame Inc. and authorized CIOS platform users.",
};

export default function PrivacyPage() {
  return (
    <LegalPageTemplate title={legalPages.privacy.title} content={legalContent.privacy} />
  );
}
