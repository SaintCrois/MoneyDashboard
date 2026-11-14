export type Level = "strict" | "medium" | "loose";

export interface Company {
  id: number;
  ticker: string;
  name: string;
  industry_name: string | null;
  sector: string | null;
}

export interface Article {
  id: number;
  title: string;
  source: string;
  url: string;
  published_at: string | null;
  summary: string | null;
}

export interface CompanySummary {
  company: Company;
  count: number;
  direct_count: number;
  top: Article | null;
}

export interface InsightItem {
  n: number;
  article: Article;
  direct: boolean;
  groups: string[];
  terms: Record<string, string[]>;
  reason: string;
}

export interface Scenario {
  group: string;
  label: string;
  kind: "mixed" | "uncertain";
  effect: string;
  check: string[];
  refs: number[];
}

export interface CompanyInsight {
  company: Company;
  level: Level;
  pool_size: number;
  total: number;
  items: InsightItem[];
  scenarios: Scenario[];
  generated_at: string;
}

export interface FeedItem {
  article: Article;
  companies: { ticker: string; name: string; reason: string; direct: boolean; groups: string[] }[];
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  companies: (level: Level) =>
    get<{ level: Level; pool_size: number; companies: CompanySummary[] }>(`/api/insights/companies?level=${level}`),
  company: (ticker: string, level: Level) =>
    get<CompanyInsight>(`/api/insights/companies/${encodeURIComponent(ticker)}?level=${level}&limit=12`),
  feed: (level: Level) => get<{ items: FeedItem[] }>(`/api/insights/feed?level=${level}&limit=80`),
  groups: () => get<{ key: string; label: string }[]>(`/api/insights/groups`),
  async ingest(): Promise<{ ingested: number; skipped_duplicate: number; errors: number }> {
    const res = await fetch("/api/news/ingest", { method: "POST" });
    if (!res.ok) throw new Error(`${res.status}`);
    return res.json();
  },
};

export const LEVELS: { key: Level; name: string; rule: string }[] = [
  { key: "strict", name: "เข้ม", rule: "เอาเฉพาะข่าวที่เอ่ยชื่อย่อหุ้นหรือชื่อบริษัทตรง ๆ" },
  { key: "medium", name: "กลาง", rule: "เอ่ยชื่อ หรือมีคำเกี่ยวกับธุรกิจของบริษัทตั้งแต่ 2 คำขึ้นไป" },
  {
    key: "loose",
    name: "หลวม",
    rule: "เอ่ยชื่อ หรือมีคำที่เกี่ยวข้องแค่ 1 คำก็นับ รวมถึงคำเศรษฐกิจทั่วไปอย่างดอกเบี้ยหรือเงินเฟ้อ",
  },
];

const INDUSTRY_TH: Record<string, string> = {
  Energy: "พลังงาน",
  Tourism: "ท่องเที่ยวและการบิน",
  Petrochemicals: "ปิโตรเคมี",
  Financials: "ธนาคาร",
  Technology: "สื่อสารและเทคโนโลยี",
  Healthcare: "โรงพยาบาล",
  Consumer: "ค้าปลีก",
};

export function industryLabel(c: Company): string {
  return (c.industry_name && INDUSTRY_TH[c.industry_name]) || c.industry_name || "ไม่ระบุหมวด";
}

/** Lowercase industry key, used to pick the tile icon and tint. */
export function industryKey(c: Company): string {
  return (c.industry_name ?? "other").toLowerCase();
}

export function shortName(c: Company): string {
  return c.name.replace(/\s*Public Company Limited\s*$/i, "");
}

const dateFmt = new Intl.DateTimeFormat("th-TH", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export function formatDate(iso: string | null): string {
  if (!iso) return "ไม่ทราบวันที่";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "ไม่ทราบวันที่" : dateFmt.format(d);
}

export function safeUrl(url: string): string | null {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:" ? u.href : null;
  } catch {
    return null;
  }
}
