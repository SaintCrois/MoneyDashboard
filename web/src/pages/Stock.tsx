import { useState } from "react";
import { ArrowLeft, ArrowUpRight } from "lucide-react";
import {
  api,
  formatDate,
  industryLabel,
  LEVELS,
  safeUrl,
  shortName,
  stampDate,
  type InsightItem,
  type Level,
  type Scenario,
} from "../api";
import { useLoad } from "../hooks";
import { ErrorState, ImpactLabel, LinkType, Skeleton } from "./shared";

interface Props {
  ticker: string;
  level: Level;
  onLevel: (l: Level) => void;
}

/**
 * One business angle told as a four-cut photo strip:
 * what happened, how it touches the business, both sides, what to check.
 * Cuts 1 and 2 are facts from the news; cuts 3 and 4 are the system's reading.
 */
function Strip({
  scenario,
  items,
  ticker,
  onCite,
  onJump,
}: {
  scenario: Scenario;
  items: InsightItem[];
  ticker: string;
  onCite: (refs: number[]) => void;
  onJump: (n: number) => void;
}) {
  const cited = items.filter((it) => scenario.refs.includes(it.n));
  const lead = cited.slice(0, 2);
  const terms = [...new Set(cited.flatMap((it) => it.terms[scenario.group] ?? []))].slice(0, 6);
  const direct = cited.filter((it) => it.direct).length;

  return (
    <article
      className="strip"
      onMouseEnter={() => onCite(scenario.refs)}
      onMouseLeave={() => onCite([])}
      onFocus={() => onCite(scenario.refs)}
      onBlur={() => onCite([])}
    >
      <header className="strip-head">
        <h2>มุม{scenario.label}</h2>
        <ImpactLabel kind={scenario.kind} />
      </header>

      <ol className="cuts">
        <li className="cut cut-a">
          <span className="cut-n">1</span>
          <h3>เกิดอะไรขึ้น</h3>
          <ul className="cut-news">
            {lead.map((it) => (
              <li key={it.n}>
                <button type="button" onClick={() => onJump(it.n)}>
                  {it.article.title}
                </button>
                <span>{it.article.source}</span>
              </li>
            ))}
          </ul>
          {cited.length > lead.length && <p className="cut-more">และอีก {cited.length - lead.length} ข่าวด้านล่าง</p>}
        </li>

        <li className="cut cut-b">
          <span className="cut-n">2</span>
          <h3>เกี่ยวกับ {ticker} ยังไง</h3>
          <p>
            ข่าว {cited.length} ชิ้นมีคำในหมวด{scenario.label} ซึ่งเป็นธุรกิจของบริษัท
            {direct > 0 && ` และมี ${direct} ชิ้นที่เอ่ยชื่อบริษัทตรง ๆ`}
          </p>
          {terms.length > 0 && (
            <ul className="terms" aria-label="คำที่พบในข่าว">
              {terms.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          )}
        </li>

        <li className="cut cut-a">
          <span className="cut-n">3</span>
          <h3>ผลได้ทั้งสองด้าน</h3>
          <p>{scenario.effect}</p>
        </li>

        <li className="cut cut-b">
          <span className="cut-n">4</span>
          <h3>ต้องเช็กอะไรต่อ</h3>
          <ul className="checks">
            {scenario.check.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </li>
      </ol>

      <footer className="strip-foot">
        <span>ช่อง 1 และ 2 มาจากข่าว ช่อง 3 และ 4 เป็นการตีความของระบบ ยังไม่ยืนยันว่าบริษัทได้รับผลกระทบจริง</span>
        <span className="stamp">{stampDate()}</span>
      </footer>
    </article>
  );
}

export function StockPage({ ticker, level, onLevel }: Props) {
  const [state, reload] = useLoad(() => api.company(ticker, level), [ticker, level]);
  // News numbers cited by the strip under the pointer or focus, and the one just jumped to.
  const [cited, setCited] = useState<number[]>([]);
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
          {title}
          <Skeleton rows={6} />
        </>
      )}
      {state.status === "error" && (
        <>
          {title}
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
                <>
                  {scenarios.length === 0 ? (
                    <div className="notice">
                      <h2>ข้อมูลไม่เพียงพอ</h2>
                      <p>พบข่าวที่เอ่ยชื่อบริษัท แต่ยังไม่พอระบุว่ากระทบธุรกิจด้านไหน อ่านข่าวต้นทางได้จากรายการด้านล่าง</p>
                    </div>
                  ) : (
                    <div className="strips">
                      {scenarios.map((s) => (
                        <Strip
                          key={s.group}
                          scenario={s}
                          items={items}
                          ticker={company.ticker}
                          onCite={setCited}
                          onJump={jumpTo}
                        />
                      ))}
                    </div>
                  )}

                  <section className="sources" aria-labelledby="sources-h">
                    <h2 id="sources-h">ข่าวที่ใช้อ้างอิง</h2>
                    <p className="section-note">
                      แสดง {items.length} จาก {total} ข่าว เรียงตามความเกี่ยวข้อง
                    </p>
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
                </>
              )}
            </>
          );
        })()}
    </>
  );
}
