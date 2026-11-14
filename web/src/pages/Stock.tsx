import { useState } from "react";
import { ArrowLeft, ArrowUpRight } from "lucide-react";
import { api, formatDate, industryLabel, LEVELS, safeUrl, shortName, type Level } from "../api";
import { useLoad } from "../hooks";
import { ErrorState, ImpactLabel, LinkType, Skeleton } from "./shared";

interface Props {
  ticker: string;
  level: Level;
  onLevel: (l: Level) => void;
}

export function StockPage({ ticker, level, onLevel }: Props) {
  const [state, reload] = useLoad(() => api.company(ticker, level), [ticker, level]);
  // News numbers cited by the scenario under the pointer or focus, and the one just jumped to.
  const [cited, setCited] = useState<number[]>([]);
  const [flash, setFlash] = useState<number | null>(null);

  function jumpTo(n: number) {
    document.getElementById(`news-${n}`)?.scrollIntoView({ block: "center", behavior: "smooth" });
    setFlash(n);
    window.setTimeout(() => setFlash((f) => (f === n ? null : f)), 1600);
  }

  return (
    <>
      <a className="back" href="#/">
        <ArrowLeft aria-hidden size={16} />
        หุ้นที่ฉันถือ
      </a>

      {state.status === "loading" && (
        <>
          <h1>ทำไม {ticker.toUpperCase()} ขยับ</h1>
          <Skeleton rows={6} />
        </>
      )}
      {state.status === "error" && (
        <>
          <h1>ทำไม {ticker.toUpperCase()} ขยับ</h1>
          <ErrorState onRetry={reload} />
        </>
      )}
      {state.status === "ready" &&
        (() => {
          const { company, items, scenarios, total, pool_size } = state.data;
          const looser = LEVELS[LEVELS.findIndex((l) => l.key === level) + 1];
          return (
            <>
              <div className="page-head">
                <div>
                  <h1>ทำไม {company.ticker} ขยับ</h1>
                  <p className="lede">
                    {shortName(company) !== company.ticker && `${shortName(company)} `}หมวด{industryLabel(company)}
                  </p>
                </div>
                <p className="count-line">
                  <strong>{total}</strong> ข่าวที่อาจเกี่ยวข้อง จากข่าวล่าสุด {pool_size} ชิ้น
                </p>
              </div>

              {items.length === 0 ? (
                <div className="notice">
                  <h2>ข้อมูลไม่เพียงพอ</h2>
                  <p>
                    ไม่พบข่าวที่เกี่ยวข้องกับ {company.ticker} ที่ระดับ{LEVELS.find((l) => l.key === level)!.name}{" "}
                    ระบบจะไม่สร้างผลกระทบขึ้นมาเอง
                  </p>
                  {looser && (
                    <button type="button" className="btn" onClick={() => onLevel(looser.key)}>
                      ลองระดับ{looser.name}
                    </button>
                  )}
                </div>
              ) : (
                <div className="stock">
                  <section className="interp" aria-labelledby="interp-h">
                    <h2 id="interp-h">การตีความของระบบ</h2>
                    <p className="section-note">
                      สถานการณ์ตัวอย่างตามหมวดธุรกิจของข่าวที่พบ ยังไม่ยืนยันว่าบริษัทได้รับผลกระทบจริง
                    </p>
                    {scenarios.length === 0 && (
                      <p className="scenario-empty">พบข่าวที่เอ่ยชื่อบริษัท แต่ข้อมูลยังไม่พอระบุทิศทางผลกระทบ</p>
                    )}
                    {scenarios.map((s) => (
                      <article
                        key={s.group}
                        className="scenario"
                        onMouseEnter={() => setCited(s.refs)}
                        onMouseLeave={() => setCited([])}
                        onFocus={() => setCited(s.refs)}
                        onBlur={() => setCited([])}
                      >
                        <header>
                          <h3>{s.label}</h3>
                          <ImpactLabel kind={s.kind} />
                        </header>
                        <p>{s.effect}</p>
                        <h4>สิ่งที่ควรตรวจสอบ</h4>
                        <ul className="checks">
                          {s.check.map((c) => (
                            <li key={c}>{c}</li>
                          ))}
                        </ul>
                        <div className="refs">
                          <span>อ้างอิงจากข่าว</span>
                          {s.refs.map((n) => (
                            <button key={n} type="button" onClick={() => jumpTo(n)} aria-label={`ไปที่ข่าวหมายเลข ${n}`}>
                              {n}
                            </button>
                          ))}
                        </div>
                      </article>
                    ))}
                  </section>

                  <section className="sources" aria-labelledby="sources-h">
                    <h2 id="sources-h">จากข่าว</h2>
                    <p className="section-note">แสดง {items.length} จาก {total} ข่าว เรียงตามความเกี่ยวข้อง</p>
                    <ol className="news">
                      {items.map(({ n, article, direct, reason }) => {
                        const url = safeUrl(article.url);
                        const cls = ["news-item", cited.includes(n) && "is-cited", flash === n && "is-flash"]
                          .filter(Boolean)
                          .join(" ");
                        return (
                          <li key={article.id} id={`news-${n}`} className={cls}>
                            <span className="news-n">{n}</span>
                            <div>
                              <h3>{article.title}</h3>
                              <p className="news-meta">
                                {article.source}
                                <span aria-hidden> / </span>
                                {formatDate(article.published_at)}
                              </p>
                              <div className="news-why">
                                <LinkType direct={direct} />
                                <span>{reason}</span>
                              </div>
                              {url && (
                                <a className="link" href={url} target="_blank" rel="noreferrer">
                                  อ่านข่าวต้นทาง
                                  <ArrowUpRight aria-hidden size={16} />
                                </a>
                              )}
                            </div>
                          </li>
                        );
                      })}
                    </ol>
                  </section>
                </div>
              )}
            </>
          );
        })()}
    </>
  );
}
