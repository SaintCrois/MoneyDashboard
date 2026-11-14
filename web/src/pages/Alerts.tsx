import { Lock } from "lucide-react";

export function AlertsPage({ holdings }: { holdings: string[] }) {
  return (
    <>
      <div className="page-head">
        <div>
          <h1>แจ้งเตือน</h1>
          <p className="lede">รับแจ้งเตือนเมื่อมีข่าวที่อาจกระทบหุ้นที่ถืออยู่ การอ่านข่าวและผลกระทบยังใช้ได้ฟรีเหมือนเดิม</p>
        </div>
      </div>

      <div className="card lock">
        <span className="lock-tile">
          <Lock aria-hidden size={22} strokeWidth={1.75} />
        </span>
        <div>
          <h2>เชื่อมบัญชี Trinity เพื่อรับแจ้งเตือน</h2>
          <p>ฟีเจอร์นี้ยังไม่เปิดใช้ในต้นแบบ หน้านี้แสดงให้เห็นว่าจะทำงานอย่างไรเมื่อเปิดใช้</p>
          <button type="button" className="btn" disabled>
            เชื่อมบัญชี Trinity
          </button>
        </div>
      </div>

      <h2 className="list-title">หุ้นที่จะได้รับแจ้งเตือน</h2>
      {holdings.length === 0 ? (
        <p className="tickers-none">เพิ่มหุ้นในหน้าหุ้นที่ฉันถือก่อน</p>
      ) : (
        <ul className="card toggles">
          {holdings.map((t) => (
            <li key={t}>
              <strong>{t}</strong>
              <label className="switch">
                <input type="checkbox" disabled aria-label={`แจ้งเตือน ${t}`} />
                <span aria-hidden />
              </label>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
