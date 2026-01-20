import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app/App";
import "./index.css";

const containerId = "root";
let container = document.getElementById(containerId);

// 컨테이너가 없으면 생성 (안전하게)
if (!container) {
  container = document.createElement("div");
  container.id = containerId;
  document.body.appendChild(container);
}

// React 18 방식으로 렌더링
const root = ReactDOM.createRoot(container);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
