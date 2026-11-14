import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/anuphan";
import "@fontsource/mitr/500.css";
import "@fontsource/mitr/600.css";
import "./styles.css";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
