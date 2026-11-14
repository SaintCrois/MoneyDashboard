import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { api, formatDate, safeUrl, type Level } from "../api";
import { useLoad } from "../hooks";
import { ErrorState, Skeleton } from "./shared";

export function NewsPage({ level, holdings }: { level: Level; holdings: string[] }) {
  const [state, reload] = useLoad(() => Promise.all([api.feed(level), api.groups()]), [level]);
  const [group, setGroup] = useState<string>("all");
  const [mine, setMine] = useState(false);
  const [relatedOnly, setRelatedOnly] = useState(true);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>ข่าววันนี้</h1>
          <p className="lede">ข่าวล่าสุดจากแหล่งข่าวไทยและต่างประเทศ พร้อมหุ้นที่อาจเกี่ยวข้อง</p>
        </div>
      </div>

      {state.status === "loading" && <Skeleton rows={6} />}
      {state.status === "error" && <ErrorState onRetry={reload} />}
      {state.status === "ready" &&
        (() => {
          const [feed, groups] = state.data;
          const shown = feed.items.filter((it) => {
            const cs = mine ? it.companies.filter((c) => holdings.includes(c.ticker)) : it.companies;
            if ((mine || relatedOnly) && cs.length === 0) return false;
            return group === "all" || cs.some((c) => c.groups.includes(group));
          });
          return (
            <>
              <div className="filters">
                <div className="filter-chips" role="group" aria-label="กรองตามหมวดธุรกิจ">
                  <button type="button" aria-pressed={group === "all"} onClick={() => setGroup("all")}>
                    ทุกหมวด
                  </button>
                  {groups.map((g) => (
                    <button key={g.key} type="button" aria-pressed={group === g.key} onClick={() => setGroup(g.key)}>
                      {g.label}
                    </button>
                  ))}
                </div>
                <div className="checks-row">
                  <label className="check">
                    <input type="checkbox" checked={relatedOnly} onChange={(e) => setRelatedOnly(e.target.checked)} />
                    เฉพาะข่าวที่มีหุ้นเกี่ยวข้อง
                  </label>
                  <label className="check">
                    <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} />
                    เฉพาะหุ้นที่ฉันถือ
                  </label>
                </div>
              </div>

              {shown.length === 0 ? (
                <div className="notice">
                  <h2>ไม่มีข่าวตรงกับตัวกรองนี้</h2>
                  <p>ลองเลือกหมวดอื่น หรือปรับความเข้มของการจับคู่ให้หลวมลง</p>
                </div>
              ) : (
                <ul className="card feed">
                  {shown.map(({ article, companies }) => {
                    const url = safeUrl(article.url);
                    return (
                      <li key={article.id}>
                        <h2>{article.title}</h2>
                        <p className="news-meta">
                          {article.source}
                          <span aria-hidden> / </span>
                          {formatDate(article.published_at)}
                          {url && (
                            <a className="link" href={url} target="_blank" rel="noreferrer">
                              อ่านข่าวต้นทาง
                              <ArrowUpRight aria-hidden size={14} />
                            </a>
                          )}
                        </p>
                        {companies.length > 0 ? (
                          <div className="tickers">
                            <span>อาจเกี่ยวข้องกับ</span>
                            {companies.map((c) => (
                              <a
                                key={c.ticker}
                                href={`#/stock/${c.ticker}`}
                                className={holdings.includes(c.ticker) ? "is-held" : undefined}
                                title={c.reason}
                              >
                                {c.ticker}
                              </a>
                            ))}
                          </div>
                        ) : (
                          <p className="tickers-none">ยังไม่พบหุ้นในรายการที่เกี่ยวข้อง</p>
                        )}
                      </li>
                    );
                  })}
                </ul>
              )}
            </>
          );
        })()}
    </>
  );
}
