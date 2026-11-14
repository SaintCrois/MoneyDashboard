import { useState } from "react";
import { ArrowLeft, Circle, Info } from "lucide-react";
import {
  api,
  formatDate,
  industryLabel,
  LEVELS,
  safeUrl,
  shortName,
  type InsightItem,
  type Level,
  type Scenario,
} from "../api";
import { useLoad } from "../hooks";
import { CompanyTile, ErrorState, Headline, ImpactLabel, LinkType, Skeleton } from "./shared";

interface Props {
  ticker: string;
  level: Level;
  onLevel: (l: Level) => void;
}

/**
 * One business angle. The left column is what the news says; the right column,
 * behind a rule, is the system's reading of it, kept visibly apart.
 */
function Angle({
  scenario,
  items,
  ticker,
  onJump,
}: {
  scenario: Scenario;
  items: InsightItem[];
  ticker: string;
  onJump: (n: number) => void;
}) {
  const cited = items.filter((it) => scenario.refs.includes(it.n));
  const lead = cited.slice(0, 2);
  const terms = [...new Set(cited.flatMap((it) => it.terms[scenario.group] ?? []))].slice(0, 6);
  const direct = cited.filter((it) => it.direct).length;

  return (
    <article className="card angle">
      <header className="angle-head">
        <h2>เรื่อง{scenario.label}</h2>
        <ImpactLabel kind={scenario.kind} />
      </header>

      <div className="angle-body">
        <div className="angle-facts">
          <section>
            <h3>เกิดอะไรขึ้น</h3>
            <ul className="lead-news">
              {lead.map((it) => (
                <li key={it.n}>
                  <button type="button" onClick={() => onJump(it.n)}>
                    {it.article.title}
                  </button>
                  <span>{it.article.source}</span>
                </li>
              ))}
            </ul>
            {cited.length > lead.length && <p className="more">อีก {cited.length - lead.length} ข่าวอยู่ในรายการด้านล่าง</p>}
          </section>

          <section>
            <h3>เกี่ยวกับ {ticker} ยังไง</h3>
            <p>
              {scenario.group === "economy"
                ? `ข่าว ${cited.length} ชิ้นนี้พูดถึงเศรษฐกิจโดยรวม เช่น ดอกเบี้ย เงินเฟ้อ หรือค่าเงิน`
                : `${ticker} ทำธุรกิจ${scenario.label} และข่าว ${cited.length} ชิ้นนี้มีคำเรื่อง${scenario.label}อยู่`}
              {direct > 0 && ` โดย ${direct} ชิ้นเอ่ยชื่อบริษัทตรง ๆ`}
            </p>
            {terms.length > 0 && (
              <ul className="terms" aria-label="คำที่พบในข่าว">
                {terms.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <div className="angle-read">
          <section>
            <h3>อาจกระทบยังไง</h3>
            <p>{scenario.effect}</p>
          </section>
          <section>
            <h3>ต้องเช็กอะไรต่อ</h3>
            <ul className="checks">
              {scenario.check.map((c) => (
                <li key={c}>
                  <Circle aria-hidden size={14} />
                  {c}
                </li>
              ))}
            </ul>
          </section>
          <p className="read-note">
            <Info aria-hidden size={14} />
            ส่วนนี้ระบบตีความจากคำในข่าว ยังไม่ได้ยืนยันว่าบริษัทได้รับผลกระทบจริง
          </p>
        </div>
      </div>
    </article>
  );
}

export function StockPage({ ticker, level, onLevel }: Props) {
  const [state, reload] = useLoad(() => api.company(ticker, level), [ticker, level]);
  // The news item just jumped to from an angle, marked briefly so the eye lands on it.
  const [flash, setFlash] = useState<number | null>(null);

  function jumpTo(n: number) {
    document.getElementById(`news-${n}`)?.scrollIntoView({ block: "center", behavior: "smooth" });
    setFlash(n);
    window.setTimeout(() => setFlash((f) => (f === n ? null : f)), 1600);
  }

  const title = <h1>ทำไม {ticker.toUpperCase()} ขยับ</h1>;

  return (
    <>
      <a className="back" href="#/">
        <ArrowLeft aria-hidden size={16} />
        หุ้นที่ฉันถือ
      </a>

      {state.status === "loading" && (
        <>
          <div className="page-head">{title}</div>
          <Skeleton rows={6} />
        </>
      )}
      {state.status === "error" && (
        <>
          <div className="page-head">{title}</div>
          <ErrorState onRetry={reload} />
        </>
      )}
      {state.status === "ready" &&
        (() => {
          const { company, items, scenarios, total, pool_size } = state.data;
          const looser = LEVELS[LEVELS.findIndex((l) => l.key === level) + 1];
          return (
            <>
              <div className="stock-head">
                <CompanyTile company={company} large />
                <div className="stock-title">
                  <h1>ทำไม {company.ticker} ขยับ</h1>
                  <p className="lede">
                    {shortName(company) !== company.ticker && `${shortName(company)} `}หมวด{industryLabel(company)}
                  </p>
                  <p className="lede">
                    เจอ {total} ข่าวที่อาจเกี่ยวข้อง จากข่าวล่าสุด {pool_size} ชิ้น
                  </p>
                </div>
              </div>

              {items.length === 0 ? (
                <div className="notice">
                  <h2>ข้อมูลยังไม่พอ</h2>
                  <p>
                    ยังไม่เจอข่าวที่เกี่ยวกับ {company.ticker} ในระดับ{LEVELS.find((l) => l.key === level)!.name}{" "}
                    เราเลยไม่เดาผลกระทบขึ้นมาเอง
                  </p>
                  {looser && (
                    <button type="button" className="btn" onClick={() => onLevel(looser.key)}>
                      ลองระดับ{looser.name}
                    </button>
                  )}
                </div>
              ) : (
                <>
                  {scenarios.length === 0 ? (
                    <div className="notice">
                      <h2>ข้อมูลยังไม่พอ</h2>
                      <p>มีข่าวที่เอ่ยชื่อบริษัท แต่ยังบอกไม่ได้ว่ากระทบธุรกิจด้านไหน อ่านข่าวเต็มได้จากรายการด้านล่าง</p>
                    </div>
                  ) : (
                    <div className="angles">
                      {scenarios.map((s) => (
                        <Angle key={s.group} scenario={s} items={items} ticker={company.ticker} onJump={jumpTo} />
                      ))}
                    </div>
                  )}

                  <section className="card sources" aria-labelledby="sources-h">
                    <div className="card-head">
                      <h2 id="sources-h">ข่าวที่ใช้อ้างอิง</h2>
                      <p>
                        {items.length} จาก {total} ข่าว เรียงจากเกี่ยวข้องมากไปน้อย กดหัวข่าวเพื่ออ่านฉบับเต็ม
                      </p>
                    </div>
                    <ol className="news">
                      {items.map(({ n, article, direct, reason }) => {
                        const url = safeUrl(article.url);
                        return (
                          <li key={article.id} id={`news-${n}`} className={flash === n ? "news-item is-flash" : "news-item"}>
                            <span className="news-n">{n}</span>
                            <div>
                              <h3>
                                <Headline title={article.title} url={url} />
                              </h3>
                              <p className="news-meta">
                                {article.source}
                                <span aria-hidden> / </span>
                                {formatDate(article.published_at)}
                              </p>
                              <div className="news-why">
                                <LinkType direct={direct} />
                                <span>{reason}</span>
                              </div>
                            </div>
                          </li>
                        );
                      })}
                    </ol>
                  </section>
                </>
              )}
            </>
          );
        })()}
    </>
  );
}
