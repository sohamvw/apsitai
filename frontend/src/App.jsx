import React, { useState, useEffect } from "react";
import ChatWidget from "./components/ChatWidget";

export default function App() {
  const [open,       setOpen]       = useState(false);
  const [showGreet,  setShowGreet]  = useState(false);
  const [pulse,      setPulse]      = useState(true);

  // Show greeting bubble after 3 seconds
  useEffect(() => {
    const t1 = setTimeout(() => setShowGreet(true),  3000);
    const t2 = setTimeout(() => setShowGreet(false), 9000);
    const t3 = setTimeout(() => setPulse(false),     12000);
    return () => [t1, t2, t3].forEach(clearTimeout);
  }, []);

  return (
    <>
      <style>{`
        @keyframes floatBtn {
          0%, 100% { transform: translateY(0); }
          50%       { transform: translateY(-5px); }
        }
        @keyframes pulseRing {
          0%   { box-shadow: 0 0 0 0   rgba(229,57,53, 0.5); }
          70%  { box-shadow: 0 0 0 14px rgba(229,57,53, 0); }
          100% { box-shadow: 0 0 0 0   rgba(229,57,53, 0); }
        }
        @keyframes greetIn {
          from { opacity: 0; transform: scale(0.85) translateY(8px); }
          to   { opacity: 1; transform: scale(1)    translateY(0); }
        }
        .fab { animation: floatBtn 3s ease-in-out infinite; }
        .fab.pulse { animation: floatBtn 3s ease-in-out infinite, pulseRing 2s ease-out infinite; }
      `}</style>

      {/* GREETING BUBBLE */}
      {showGreet && !open && (
        <div
          onClick={() => { setOpen(true); setShowGreet(false); }}
          style={{
            position:     "fixed",
            bottom:       "92px",
            right:        "85px",
            background:   "#fff",
            border:       "1.5px solid #e0e0e0",
            borderRadius: "14px 14px 4px 14px",
            padding:      "10px 14px",
            fontSize:     "13px",
            color:        "#333",
            boxShadow:    "0 4px 16px rgba(0,0,0,0.12)",
            cursor:       "pointer",
            zIndex:       9998,
            maxWidth:     "200px",
            animation:    "greetIn 0.3s ease",
            lineHeight:   1.4,
          }}
        >
          👋 Hey! Need help with admissions, fees, or courses?
        </div>
      )}

      {/* FLOATING ACTION BUTTON */}
      {!open && (
        <div
          className={`fab${pulse ? " pulse" : ""}`}
          onClick={() => { setOpen(true); setShowGreet(false); }}
          style={{
            position:     "fixed",
            bottom:       "24px",
            right:        "24px",
            width:        "58px",
            height:       "58px",
            borderRadius: "50%",
            background:   "linear-gradient(135deg, #c62828, #e53935)",
            color:        "#fff",
            display:      "flex",
            alignItems:   "center",
            justifyContent: "center",
            fontSize:     "26px",
            cursor:       "pointer",
            zIndex:       9999,
          }}
        >
          💬
        </div>
      )}

      {/* CHAT WIDGET */}
      {open && <ChatWidget close={() => setOpen(false)} />}
    </>
  );
}
