import { useEffect, useRef } from "react";
import { Bell, Briefcase, Monitor, Newspaper, Smartphone } from "lucide-react";
import { LEVELS, type Level } from "./api";
import { useRoute, useStored } from "./hooks";
import { HoldingsPage } from "./pages/Holdings";
import { StockPage } from "./pages/Stock";
import { NewsPage } from "./pages/News";
import { AlertsPage } from "./pages/Alerts";

const DEFAULT_HOLDINGS = ["PTT", "KBANK", "IVL", "CPALL"];

const NAV = [
  { key: "", label: "หุ้นที่ฉันถือ", icon: Briefcase },
  { key: "news", label: "ข่าววันนี้", icon: Newspaper },
  { key: "alerts", label: "แจ้งเตือน", icon: Bell },
];

function LevelControl({ level, onChange }: { level: Level; onChange: (l: Level) => void }) {
  const current = LEVELS.find((l) => l.key === level)!;
  return (
    <fieldset className="level">
      <legend>ความเข้มของการจับคู่ข่าวกับหุ้น</legend>
      <div className="segmented" role="radiogroup">
        {LEVELS.map((l) => (
          <label key={l.key} className={l.key === level ? "is-on" : undefined}>
            <input type="radio" name="level" checked={l.key === level} onChange={() => onChange(l.key)} />
            {l.name}
          </label>
        ))}
      </div>
      <p className="level-rule">{current.rule}</p>
    </fieldset>
  );
}

function DeviceSwitch({ device, onChange }: { device: string; onChange: (d: string) => void }) {
  return (
    <div className="device-switch" role="group" aria-label="ขนาดหน้าจอที่แสดง">
      <button type="button" aria-pressed={device === "desktop"} onClick={() => onChange("desktop")}>
        <Monitor aria-hidden size={16} />
        จอคอม
      </button>
      <button type="button" aria-pressed={device === "phone"} onClick={() => onChange("phone")}>
        <Smartphone aria-hidden size={16} />
        มือถือ
      </button>
    </div>
  );
}

export function App() {
  const route = useRoute();
  const [level, setLevel] = useStored<Level>("whymove.level", "medium");
  const [holdings, setHoldings] = useStored<string[]>("whymove.holdings", DEFAULT_HOLDINGS);
  const [device, setDevice] = useStored<string>("whymove.device", "desktop");
  const mainRef = useRef<HTMLElement>(null);

  const section = route[0] ?? "";
  const navKey = section === "stock" ? "" : section;

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0 });
  }, [route.join("/")]);

  let page;
  if (section === "stock" && route[1]) {
    page = <StockPage ticker={route[1]} level={level} onLevel={setLevel} />;
  } else if (section === "news") {
    page = <NewsPage level={level} holdings={holdings} />;
  } else if (section === "alerts") {
    page = <AlertsPage holdings={holdings} />;
  } else {
    page = <HoldingsPage level={level} holdings={holdings} onHoldings={setHoldings} />;
  }

  return (
    <div className="stage" data-device={device}>
      <div className="app">
        <div className="shell">
          <header className="rail">
            <a className="wordmark" href="#/">
              Why<span>Move</span>
            </a>
            <nav aria-label="เมนูหลัก">
              {NAV.map(({ key, label, icon: Icon }) => (
                <a key={key} href={`#/${key}`} aria-current={navKey === key ? "page" : undefined}>
                  <Icon aria-hidden size={18} />
                  {label}
                </a>
              ))}
            </nav>
            <div className="rail-foot">
              <LevelControl level={level} onChange={setLevel} />
              <DeviceSwitch device={device} onChange={setDevice} />
            </div>
          </header>

          <header className="topbar">
            <a className="wordmark" href="#/">
              Why<span>Move</span>
            </a>
            <DeviceSwitch device={device} onChange={setDevice} />
          </header>

          <main className="main" ref={mainRef}>
            <div className="page">{page}</div>
            <div className="mobile-level">
              <LevelControl level={level} onChange={setLevel} />
            </div>
            <p className="disclaimer">
              ข้อมูลนี้เป็นการวิเคราะห์เพื่อประกอบความเข้าใจ ไม่ใช่คำแนะนำการลงทุน ระบบจับคู่ข่าวด้วยคำสำคัญ ยังไม่ได้ใช้ AI
            </p>
          </main>

          <nav className="tabbar" aria-label="เมนูหลัก">
            {NAV.map(({ key, label, icon: Icon }) => (
              <a key={key} href={`#/${key}`} aria-current={navKey === key ? "page" : undefined}>
                <Icon aria-hidden size={20} />
                {label}
              </a>
            ))}
          </nav>
        </div>
      </div>
    </div>
  );
}
