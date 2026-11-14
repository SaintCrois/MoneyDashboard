import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Google Sans (OFL), bundled so the app needs no internet for its font. One variable file per script, weights 400 to 700.
import "@fontsource-variable/google-sans/wght.css";
import "./styles.css";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
