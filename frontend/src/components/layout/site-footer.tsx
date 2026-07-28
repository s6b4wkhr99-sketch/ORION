import Link from "next/link";
import { LEGAL_ENTITY_NAME, legalPages } from "@/content/legal";
import { LeFrameLogo } from "./le-frame-logo";

const COPYRIGHT_YEAR = new Date().getFullYear();

export function SiteFooter({ className }: { className?: string }) {
  return (
    <footer
      className={className}
      role="contentinfo"
      style={{ minHeight: "var(--footer-height)" }}
    >
      <div className="flex flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <div className="flex items-center gap-4">
          <LeFrameLogo height={40} link />
          <p className="text-xs text-[var(--cios-secondary)]">
            © {COPYRIGHT_YEAR} {LEGAL_ENTITY_NAME} All Rights Reserved.
          </p>
        </div>
        <nav
          aria-label="Legal"
          className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--cios-secondary)] sm:justify-end"
        >
          <Link href="/legal/privacy" className="hover:text-gray-900 hover:underline">
            {legalPages.privacy.title}
          </Link>
          <span aria-hidden className="text-[var(--cios-border)]">
            ·
          </span>
          <Link href="/legal/terms" className="hover:text-gray-900 hover:underline">
            {legalPages.terms.title}
          </Link>
          <span aria-hidden className="text-[var(--cios-border)]">
            ·
          </span>
          <Link href="/legal/legal" className="hover:text-gray-900 hover:underline">
            {legalPages.legal.title}
          </Link>
        </nav>
      </div>
    </footer>
  );
}
