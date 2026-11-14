import { useState } from "react";
import { ChevronRight, Plus, RefreshCw, X } from "lucide-react";
import { api, formatDate, industryLabel, LEVELS, shortName, type Level } from "../api";
import { useLoad } from "../hooks";
import { ErrorState, CompanyTile, Skeleton } from "./shared";

interface Props {
  level: Level;
  holdings: string[];
  onHoldings: (h: string[]) => void;
}

export function HoldingsPage({ level, holdings, onHoldings }: Props) {
  const [state, reload] = useLoad(() => api.companies(level), [level]);
  const [refresh, setRefresh] = useState<{ busy: boolean; note: string }>({ busy: false, note: "" });

  async function pullNews() {
    setRefresh({ busy: true, note: "" });
    try {
      const r = await api.ingest();
      setRefresh({
        busy: false,
        note: r.ingested > 0 ? `เพิ่มข่าวใหม่ ${r.ingested} ชิ้น` : "ยังไม่มีข่าวใหม่จากแหล่งข่าว",
      });
      reload();
    } catch {
      setRefresh({ busy: false, note: "ดึงข่าวไม่สำเร็จ ลองอีกครั้งได้" });
    }
  }

  const levelName = LEVELS.find((l) => l.key === level)!.name;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>หุ้นที่ฉันถือ</h1>
          {state.status === "ready" && (
            <p className="lede">
              คัดจากข่าวล่าสุด {state.data.pool_size} ชิ้น จับคู่ที่ระดับ{levelName}
            </p>
          )}
        </div>
        <div className="head-actions">
          <span className="status" role="status">
            {refresh.note}
          </span>
          <button type="button" className="btn" onClick={pullNews} disabled={refresh.busy} aria-busy={refresh.busy}>
            <RefreshCw aria-hidden size={16} className={refresh.busy ? "spin" : undefined} />
            {refresh.busy ? "กำลังดึงข่าว" : "ดึงข่าวล่าสุด"}
          </button>
        </div>
      </div>

      {state.status === "loading" && <Skeleton />}
      {state.status === "error" && <ErrorState onRetry={reload} />}
      {state.status === "ready" &&
        (() => {
          const byTicker = new Map(state.data.companies.map((c) => [c.company.ticker, c]));
          const held = holdings.map((t) => byTicker.get(t)).filter((c) => c !== undefined);
          const rest = state.data.companies.filter((c) => !holdings.includes(c.company.ticker));
          return (
            <>
              {held.length === 0 ? (
                <div className="notice">
                  <h2>ยังไม่มีหุ้นในรายการ</h2>
                  <p>เลือกหุ้นที่ถืออยู่จากรายการด้านล่าง แล้วระบบจะคัดข่าวที่อาจเกี่ยวข้องให้</p>
                </div>
              ) : (
                <ul className="card holdings">
                  {held.map(({ company, count, direct_count, top }) => (
                    <li key={company.ticker}>
                      <a className="holding" href={`#/stock/${company.ticker}`}>
                        <CompanyTile company={company} />
                        <span className="holding-id">
                          <strong>{company.ticker}</strong>
                          <span>{shortName(company) !== company.ticker ? shortName(company) : industryLabel(company)}</span>
                        </span>
                        <span className="holding-news">
                          {top ? (
                            <>
                              <span className="holding-top">{top.title}</span>
                              <span className="holding-meta">
                                {top.source}
                                <span aria-hidden> / </span>
                                {formatDate(top.published_at)}
                              </span>
                            </>
                          ) : (
                            <span className="holding-meta">ไม่พบข่าวที่เกี่ยวข้องที่ระดับนี้ ลองปรับความเข้มให้หลวมลง</span>
                          )}
                        </span>
                        <span className="holding-count">
                          <strong>{count}</strong>
                          <span>ข่าวที่อาจเกี่ยวข้อง</span>
                          {direct_count > 0 && <em>เอ่ยชื่อบริษัท {direct_count}</em>}
                        </span>
                        <ChevronRight aria-hidden size={20} className="holding-go" />
                      </a>
                      <button
                        type="button"
                        className="icon-btn"
                        aria-label={`นำ ${company.ticker} ออกจากรายการ`}
                        onClick={() => onHoldings(holdings.filter((t) => t !== company.ticker))}
                      >
                        <X aria-hidden size={18} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              {rest.length > 0 && (
                <section className="add">
                  <h2>เพิ่มหุ้นที่ถืออยู่</h2>
                  <div className="add-list">
                    {rest.map(({ company }) => (
                      <button
                        key={company.ticker}
                        type="button"
                        className="chip-btn"
                        onClick={() => onHoldings([...holdings, company.ticker])}
                      >
                        <Plus aria-hidden size={16} />
                        <strong>{company.ticker}</strong>
                        {industryLabel(company)}
                      </button>
                    ))}
                  </div>
                </section>
              )}
            </>
          );
        })()}
    </>
  );
}
