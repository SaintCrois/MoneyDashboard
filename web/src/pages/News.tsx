import { useState } from "react";
import { api, formatDate, safeUrl, type Level } from "../api";
import { useLoad } from "../hooks";
import { ErrorState, Headline, Skeleton } from "./shared";

type Scope = "all" | "related" | "mine";

const SCOPES: { key: Scope; label: string }[] = [
  { key: "related", label: "โยงกับหุ้นได้" },
  { key: "mine", label: "หุ้นที่ฉันถือ" },
  { key: "all", label: "ทุกข่าว" },
];

export function NewsPage({ level, holdings }: { level: Level; holdings: string[] }) {
  const [state, reload] = useLoad(() => Promise.all([api.feed(level), api.groups()]), [level]);
  const [group, setGroup] = useState<string>("all");
  // One choice with three states: every news item, items linked to any stock, items linked to stocks I hold.
  const [scope, setScope] = useState<Scope>("related");

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
            const cs = scope === "mine" ? it.companies.filter((c) => holdings.includes(c.ticker)) : it.companies;
            if (scope !== "all" && cs.length === 0) return false;
            return group === "all" || cs.some((c) => c.groups.includes(group));
          });
          return (
            <>
              <div className="filters">
                <div className="filters-top">
                  <div className="segment" role="group" aria-label="ข่าวที่แสดง">
                    {SCOPES.map((s) => (
                      <button key={s.key} type="button" aria-pressed={scope === s.key} onClick={() => setScope(s.key)}>
                        {s.label}
                      </button>
                    ))}
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
