import { ArrowUpDown, CircleHelp, Network, Target } from "lucide-react";

export function Skeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="skeleton" aria-busy="true" aria-label="กำลังโหลด">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton-row">
          <span style={{ width: "4.5rem" }} />
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
      <ArrowUpDown aria-hidden size={16} />
      ผลกระทบผสม
    </span>
  ) : (
    <span className="impact">
      <CircleHelp aria-hidden size={16} />
      ทิศทางยังไม่แน่ชัด
    </span>
  );
}
