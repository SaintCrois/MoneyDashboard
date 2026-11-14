import { LEVELS, type Level } from "../api";

export function SettingsPage({ level, onLevel }: { level: Level; onLevel: (l: Level) => void }) {
  return (
    <>
      <div className="page-head">
        <div>
          <h1>ตั้งค่า</h1>
          <p className="lede">ตั้งครั้งเดียวใช้ได้ทุกหน้า และจำไว้ในเครื่องนี้</p>
        </div>
      </div>

      <section className="card setting" aria-labelledby="level-h">
        <div className="card-head">
          <h2 id="level-h">ความเข้มในการจับคู่ข่าวกับหุ้น</h2>
          <p>ยิ่งหลวมยิ่งเจอข่าวเยอะ แต่จะมีข่าวที่เกี่ยวแค่ทางอ้อมปนมาด้วย</p>
        </div>
        <div className="options" role="radiogroup" aria-labelledby="level-h">
          {LEVELS.map((l) => (
            <label key={l.key} className="option">
              <input type="radio" name="level" checked={l.key === level} onChange={() => onLevel(l.key)} />
              <span className="option-text">
                <strong>{l.name}</strong>
                <span>{l.rule}</span>
              </span>
            </label>
          ))}
        </div>
      </section>
    </>
  );
}
