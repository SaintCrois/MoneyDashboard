import { Lock } from "lucide-react";

export function AlertsPage({ holdings }: { holdings: string[] }) {
  return (
    <>
      <div className="page-head">
        <div>
          <h1>แจ้งเตือน</h1>
          <p className="lede">เตือนเมื่อมีข่าวที่อาจกระทบหุ้นที่ถืออยู่ ส่วนการอ่านข่าวกับผลกระทบยังใช้ฟรีเหมือนเดิม</p>
        </div>
      </div>

      <div className="card lock">
        <span className="lock-tile">
          <Lock aria-hidden size={22} strokeWidth={1.75} />
        </span>
        <div>
          <h2>เชื่อมบัญชี Trinity เพื่อรับแจ้งเตือน</h2>
          <p>เวอร์ชันทดลองนี้ยังกดใช้ไม่ได้ หน้านี้ให้ดูว่าพอเปิดใช้แล้วจะทำงานยังไง</p>
          <button type="button" className="btn" disabled>
            เชื่อมบัญชี Trinity
          </button>
        </div>
      </div>

      <h2 className="list-title">หุ้นที่จะแจ้งเตือน</h2>
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
