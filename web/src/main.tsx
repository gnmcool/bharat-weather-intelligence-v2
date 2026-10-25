import { lazy, StrictMode, Suspense, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./design/index.css";

// The farmer site (#/kisan) is a separate, standalone page: no header, menus or expert detail.
const KisanApp = lazy(() => import("./kisan/KisanApp"));
const App = lazy(() => import("./app/App"));
const isKisan = () => /^#\/?kisan(\b|\/|\?|$)/.test(location.hash);

function Root() {
  const [kisan, setKisan] = useState(isKisan);
  useEffect(() => {
    const h = () => setKisan(isKisan());
    window.addEventListener("hashchange", h);
    return () => window.removeEventListener("hashchange", h);
  }, []);
  return kisan
    ? <Suspense fallback={<div style={{ minHeight: "100vh", background: "#f3f6f1" }} />}><KisanApp /></Suspense>
    : <Suspense fallback={null}><App /></Suspense>;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
