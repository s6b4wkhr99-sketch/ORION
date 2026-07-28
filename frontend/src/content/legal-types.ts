export interface LegalSection {
  title: string;
  content: string | string[];
}

export interface LegalPageContent {
  body?: string;
  sections?: LegalSection[];
  lastUpdated?: string;
}
