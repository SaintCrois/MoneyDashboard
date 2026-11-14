import {
  ArrowUpDown,
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
import { industryKey, industryLabel, type Company } from "../api";

const INDUSTRY_ICON: Record<string, LucideIcon> = {
  energy: Zap,
  tourism: Plane,
  petrochemicals: FlaskConical,
  financials: Landmark,
  technology: RadioTower,
  healthcare: HeartPulse,
  consumer: ShoppingBasket,
};

/** Pastel tile with the industry's icon. The industry name is in the title for pointer users. */
export function IndustryTile({ company, large = false }: { company: Company; large?: boolean }) {
  const key = industryKey(company);
  const Icon = INDUSTRY_ICON[key] ?? Building2;
  return (
    <span className={large ? "ind-tile is-lg" : "ind-tile"} data-industry={key} title={industryLabel(company)}>
      <Icon aria-hidden size={large ? 26 : 20} strokeWidth={1.75} />
    </span>
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
      <h2>เชื่อมต่อระบบหลังบ้านไม่ได้</h2>
      <p>ตรวจว่า FastAPI รันอยู่ที่พอร์ต 8000 แล้วลองอีกครั้ง</p>
      <button type="button" className="btn" onClick={onRetry}>
        ลองอีกครั้ง
      </button>
    </div>
  );
}

/** How a news item is linked to a company. Icon and text together, never colour alone. */
export function LinkType({ direct }: { direct: boolean }) {
  return direct ? (
    <span className="tag tag-direct">
      <Target aria-hidden size={14} />
      เอ่ยชื่อบริษัท
    </span>
  ) : (
    <span className="tag">
      <Network aria-hidden size={14} />
      เกี่ยวกับธุรกิจ
    </span>
  );
}

export function ImpactLabel({ kind }: { kind: "mixed" | "uncertain" }) {
  return kind === "mixed" ? (
    <span className="impact">
      <ArrowUpDown aria-hidden size={14} />
      ผลกระทบผสม
    </span>
  ) : (
    <span className="impact">
      <CircleHelp aria-hidden size={14} />
      ทิศทางยังไม่แน่ชัด
    </span>
  );
}
