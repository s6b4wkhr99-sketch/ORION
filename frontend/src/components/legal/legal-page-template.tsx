import type { LegalPageContent } from "@/content/legal-types";

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .trim();
}

function renderContent(content: string | string[]) {
  if (typeof content === "string") {
    return <p className="leading-relaxed text-gray-700">{content}</p>;
  }
  return (
    <div className="space-y-3">
      {content.map((para, i) => (
        <p key={i} className="leading-relaxed text-gray-700">
          {para}
        </p>
      ))}
    </div>
  );
}

export function LegalPageTemplate({
  title,
  content,
}: {
  title: string;
  content: LegalPageContent;
}) {
  const sections = content.sections ?? [];

  return (
    <article className="mx-auto max-w-3xl">
      <header className="mb-8 border-b border-[var(--cios-border)] pb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">{title}</h1>
        {content.lastUpdated ? (
          <p className="mt-2 text-sm text-[var(--cios-secondary)]">Last updated: {content.lastUpdated}</p>
        ) : null}
      </header>

      <div className="space-y-10">
        {sections.map((section, i) => (
          <section key={i} id={slugify(section.title)} className="scroll-mt-6">
            <h2 className="mb-3 text-lg font-semibold text-gray-900">{section.title}</h2>
            {renderContent(section.content)}
          </section>
        ))}
      </div>
    </article>
  );
}
