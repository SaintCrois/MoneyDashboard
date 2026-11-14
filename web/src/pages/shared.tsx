import {
  ArrowUpDown,
  ArrowUpRight,
  Building2,
  CircleHelp,
  FlaskConical,
  HeartPulse,
  Landmark,
  Network,
  Plane,
  RadioTower,
  ShoppingBasket,
  Target,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { industryKey, industryLabel, shortName, type Company } from "../api";

// Logos in public/logos, from each company's Wikipedia page. Logos with a symbol are cropped to it.
const LOGOS = new Set(["ADVANC", "AOT", "BDMS", "CPALL", "GULF", "IVL", "KBANK", "PTT", "PTTEP", "SCB"]);

const INDUSTRY_ICON: Record<string, LucideIcon> = {
  energy: Zap,
  tourism: Plane,
  petrochemicals: FlaskConical,
  financials: Landmark,
  technology: RadioTower,
  healthcare: HeartPulse,
  consumer: ShoppingBasket,
};

/**
 * The company's logo on a white tile, or a pastel tile with the industry's icon
 * when there is no logo file. Decorative: the ticker is always written next to it.
 */
export function CompanyTile({ company, large = false }: { company: Company; large?: boolean }) {
  const [failed, setFailed] = useState(false);
  const key = industryKey(company);
  const size = large ? " is-lg" : "";
  const title = `${shortName(company)} หมวด${industryLabel(company)}`;

  if (LOGOS.has(company.ticker) && !failed) {
    return (
      <span className={`ind-tile is-logo${size}`} title={title}>
        <img src={`/logos/${company.ticker}.svg`} alt="" onError={() => setFailed(true)} />
      </span>
    );
  }
  const Icon = INDUSTRY_ICON[key] ?? Building2;
  return (
    <span className={`ind-tile${size}`} data-industry={key} title={title}>
      <Icon aria-hidden size={large ? 26 : 20} strokeWidth={1.75} />
    </span>
  );
}

/** A news headline that opens the source. The arrow stays on the same line as the last word. */
export function Headline({ title, url }: { title: string; url: string | null }) {
  if (!url) return <>{title}</>;
  const cut = title.lastIndexOf(" ");
  return (
    <a className="headline" href={url} target="_blank" rel="noreferrer">
      {title.slice(0, cut + 1)}
      <span className="nowrap">
        {title.slice(cut + 1)}
        <ArrowUpRight aria-hidden size={15} />
      </span>
    </a>
  );
}

export function Skeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="card skeleton" aria-busy="true" aria-label="กำลังโหลด">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton-row">
          <span style={{ width: "2.75rem", height: "2.75rem", borderRadius: "12px" }} />
          <span style={{ width: `${62 - i * 7}%` }} />
        </div>
      ))}
    </div>
  );
}

export function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="notice" role="alert">
      <h2>โหลดข้อมูลไม่ได้</h2>
      <p>เช็กว่า FastAPI รันอยู่ที่พอร์ต 8000 แล้วกดลองใหม่</p>
      <button type="button" className="btn" onClick={onRetry}>
        ลองใหม่
      </button>
    </div>
  );
}

/** How a news item is linked to a company. Icon and text together, never colour alone. */
export function LinkType({ direct }: { direct: boolean }) {
  return direct ? (
    <span className="tag tag-direct">
      <Target aria-hidden size={14} />
      เอ่ยชื่อตรง ๆ
    </span>
  ) : (
    <span className="tag">
      <Network aria-hidden size={14} />
      เกี่ยวทางอ้อม
    </span>
  );
}

export function ImpactLabel({ kind }: { kind: "mixed" | "uncertain" }) {
  return kind === "mixed" ? (
    <span className="impact">
      <ArrowUpDown aria-hidden size={14} />
      มีทั้งบวกและลบ
    </span>
  ) : (
    <span className="impact">
      <CircleHelp aria-hidden size={14} />
      ยังบอกไม่ได้ว่าบวกหรือลบ
    </span>
  );
}
