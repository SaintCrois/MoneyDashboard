import { useState } from "react";
import { Check as CheckIcon } from "lucide-react";
import { api, formatDate, safeUrl, type Level } from "../api";
import { useLoad } from "../hooks";
import { ErrorState, Headline, Skeleton } from "./shared";

function Check({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <label className="check">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="check-box" aria-hidden>
        <CheckIcon size={13} strokeWidth={3} />
      </span>
      {label}
    </label>
  );
}

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
          <p className="lede">ข่าวล่าสุดจากสำนักข่าวไทยและต่างประเทศ ใต้แต่ละข่าวบอกว่าอาจเกี่ยวกับหุ้นตัวไหน</p>
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
                <div className="filters-top">
                  <div className="checks-row">
                    <Check checked={relatedOnly} onChange={setRelatedOnly} label="เฉพาะข่าวที่โยงกับหุ้นได้" />
                    <Check checked={mine} onChange={setMine} label="เฉพาะหุ้นที่ฉันถือ" />
                  </div>
                  <span className="status">{shown.length} ข่าว</span>
                </div>
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
              </div>

              {shown.length === 0 ? (
                <div className="notice">
                  <h2>ไม่มีข่าวตามที่กรองไว้</h2>
                  <p>
                    ลองเปลี่ยนหมวด หรือปรับการจับคู่ให้หลวมขึ้นใน{" "}
                    <a className="inline-link" href="#/settings">
                      ตั้งค่า
                    </a>
                  </p>
                </div>
              ) : (
                <ul className="card feed">
                  {shown.map(({ article, companies }) => {
                    const url = safeUrl(article.url);
                    return (
                      <li key={article.id}>
                        <h2>
                          <Headline title={article.title} url={url} />
                        </h2>
                        <p className="news-meta">
                          {article.source}
                          <span aria-hidden> / </span>
                          {formatDate(article.published_at)}
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
                          <p className="tickers-none">ยังโยงกับหุ้นในรายการไม่ได้</p>
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
