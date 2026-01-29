export default function DevHealth() {
  if (!Boolean(import.meta.env?.DEV)) return null;

  // 스크린샷용 임시 숨김 (제거 가능)
  const hideForScreenshot = true;
  if (hideForScreenshot) return null;

  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        right: 8,
        bottom: 8,
        zIndex: 9999,
        background: "rgba(49,130,246,0.1)",
        color: "#1e1e1e",
        padding: "6px 10px",
        borderRadius: 10,
        border: "1px solid rgba(49,130,246,0.3)",
        fontSize: "0.875rem",
        fontWeight: 500,
      }}
    >
      🔍 DEV Health Check
    </div>
  );
}
