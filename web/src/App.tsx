import { useEffect, useRef } from "react";
import { Bell, Briefcase, Monitor, Newspaper, Settings, Smartphone } from "lucide-react";
import { type Level } from "./api";
import { useRoute, useStored } from "./hooks";
import { HoldingsPage } from "./pages/Holdings";
import { StockPage } from "./pages/Stock";
import { NewsPage } from "./pages/News";
import { AlertsPage } from "./pages/Alerts";
import { SettingsPage } from "./pages/Settings";

const DEFAULT_HOLDINGS = ["PTT", "KBANK", "IVL", "CPALL"];

const NAV = [
  { key: "", label: "หุ้นที่ถือ", icon: Briefcase },
  { key: "news", label: "ข่าววันนี้", icon: Newspaper },
  { key: "alerts", label: "แจ้งเตือน", icon: Bell },
  { key: "settings", label: "ตั้งค่า", icon: Settings },
];

/** Desktop or phone-width preview of the app, for the demo. */
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

function BrandMark() {
  return <img className="brand-mark" src="/whymove-mark.svg" alt="" />;
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
  } else if (section === "settings") {
    page = <SettingsPage level={level} onLevel={setLevel} />;
  } else {
    page = <HoldingsPage level={level} holdings={holdings} onHoldings={setHoldings} />;
  }

  return (
    <div className="stage" data-device={device}>
      <div className="app">
        <div className="shell">
          <nav className="rail" aria-label="เมนูหลัก">
            <a className="rail-logo" href="#/">
              <BrandMark />
              <span className="rail-name">WhyMove</span>
            </a>
            {NAV.map(({ key, label, icon: Icon }) => (
              <a key={key} className="rail-item" href={`#/${key}`} aria-current={navKey === key ? "page" : undefined}>
                <Icon aria-hidden size={20} strokeWidth={1.75} />
                {label}
              </a>
            ))}
            <div className="rail-foot">
              <DeviceSwitch device={device} onChange={setDevice} />
            </div>
          </nav>

          <header className="topbar">
            <a className="brand" href="#/">
              <BrandMark />
              WhyMove
            </a>
            <DeviceSwitch device={device} onChange={setDevice} />
          </header>

          <main className="main" ref={mainRef}>
            <div className="page">{page}</div>
            <p className="disclaimer">
              WhyMove ช่วยให้เห็นว่าข่าวเกี่ยวกับหุ้นยังไง ไม่ได้แนะนำให้ซื้อหรือขาย ตอนนี้ระบบจับคู่ข่าวจากคำที่อยู่ในข่าว ยังไม่ได้ใช้ AI
            </p>
          </main>

          <nav className="tabbar" aria-label="เมนูหลัก">
            {NAV.map(({ key, label, icon: Icon }) => (
              <a key={key} href={`#/${key}`} aria-current={navKey === key ? "page" : undefined}>
                <Icon aria-hidden size={20} strokeWidth={1.75} />
                {label}
              </a>
            ))}
          </nav>
        </div>
      </div>
    </div>
  );
}
