import Link from "next/link";
import { SiteFooter } from "@/components/layout/site-footer";
import { LeFrameLogo } from "@/components/layout/le-frame-logo";

export default function LegalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--cios-background)]">
      <header className="border-b border-[var(--cios-border)] bg-white px-4 py-4 sm:px-6">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4">
          <LeFrameLogo height={36} link />
          <Link href="/login" className="text-sm text-[var(--orion-accent)] hover:underline">
            Back to sign in
          </Link>
        </div>
      </header>
      <main className="flex-1 px-4 py-8 sm:px-6">{children}</main>
      <div className="border-t border-[var(--cios-border)] bg-white">
        <SiteFooter />
      </div>
    </div>
  );
}
