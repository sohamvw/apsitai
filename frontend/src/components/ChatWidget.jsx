import React, { useState, useEffect, useRef, useCallback } from "react";

const BACKEND_URL = "https://intelligent-art-production-a70f.up.railway.app";

// ── Session ID persisted in sessionStorage (like session cookie) ─────────
function getSessionId() {
  let sid = sessionStorage.getItem("apsit_session_id");
  if (!sid) {
    sid = "session_" + Math.random().toString(36).slice(2, 10) + "_" + Date.now();
    sessionStorage.setItem("apsit_session_id", sid);
  }
  return sid;
}

const SESSION_ID = getSessionId();

const QUICK_INTENTS = [
  { label: "Admissions",  query: "How do I apply for admission at APSIT?" },
  { label: "Fees",        query: "What are the fees at APSIT?" },
  { label: "Placements",  query: "What are the placement statistics at APSIT?" },
  { label: "Courses",     query: "What courses does APSIT offer?" },
  { label: "Facilities",  query: "What facilities are available at APSIT?" },
  { label: "Contact",     query: "What is the contact information for APSIT?" },
];

const LANGUAGES = [
  { value: "auto", label: "Auto" },
  { value: "en",   label: "English" },
  { value: "hi",   label: "हिंदी" },
  { value: "mr",   label: "मराठी" },
];

// ── Styles ────────────────────────────────────────────────────────────────
const S = {
  widget: {
    position: "fixed",
    bottom: "90px",
    right: "20px",
    width: "min(380px, calc(100vw - 32px))",
    maxHeight: "calc(100vh - 120px)",
    background: "#ffffff",
    borderRadius: "18px",
    boxShadow: "0 12px 40px rgba(0,0,0,0.18)",
    display: "flex",
    flexDirection: "column",
    zIndex: 9999,
    fontFamily: "'Segoe UI', Arial, sans-serif",
    overflow: "hidden",
    animation: "popIn 0.25s cubic-bezier(.34,1.56,.64,1)",
  },
  header: {
    background: "linear-gradient(135deg, #c62828, #e53935)",
    color: "#fff",
    padding: "14px 16px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexShrink: 0,
  },
  avatar: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    background: "rgba(255,255,255,0.25)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
    flexShrink: 0,
  },
  headerText: { flex: 1 },
  headerTitle: { fontWeight: 700, fontSize: "15px", lineHeight: 1.2 },
  headerSub:   { fontSize: "11px", opacity: 0.85 },
  closeBtn: {
    cursor: "pointer",
    fontSize: "18px",
    opacity: 0.85,
    background: "none",
    border: "none",
    color: "#fff",
    lineHeight: 1,
    padding: "4px",
  },
  moodleBar: {
    background: "#fff8e1",
    borderBottom: "1px solid #ffe082",
    padding: "7px 12px",
    fontSize: "11.5px",
    color: "#6d4c00",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    flexShrink: 0,
  },
  intentsRow: {
    padding: "8px 10px 4px",
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
    flexShrink: 0,
    borderBottom: "1px solid #f0f0f0",
  },
  intentBtn: {
    padding: "5px 11px",
    borderRadius: "20px",
    border: "1.5px solid #e53935",
    background: "#fff",
    color: "#c62828",
    fontSize: "12px",
    cursor: "pointer",
    fontWeight: 500,
    transition: "background 0.15s",
  },
  chat: {
    flex: 1,
    overflowY: "auto",
    padding: "14px 12px",
    background: "#f7f7f7",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    minHeight: "220px",
  },
  bubbleWrap: (role) => ({
    display: "flex",
    justifyContent: role === "user" ? "flex-end" : "flex-start",
    alignItems: "flex-end",
    gap: "6px",
  }),
  bubble: (role) => ({
    maxWidth: "82%",
    padding: "10px 13px",
    borderRadius: role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
    background: role === "user" ? "#e53935" : "#ffffff",
    color: role === "user" ? "#fff" : "#1a1a1a",
    fontSize: "13.5px",
    lineHeight: 1.55,
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  }),
  botIcon: {
    width: "26px",
    height: "26px",
    borderRadius: "50%",
    background: "#e53935",
    color: "#fff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "13px",
    flexShrink: 0,
    marginBottom: "2px",
  },
  imgWrap: {
    marginTop: "8px",
    borderRadius: "10px",
    overflow: "hidden",
    border: "1px solid #eee",
  },
  imgActions: {
    display: "flex",
    gap: "12px",
    padding: "6px 8px",
    background: "#f9f9f9",
    fontSize: "12px",
  },
  imgLink: {
    color: "#c62828",
    textDecoration: "none",
    fontWeight: 500,
  },
  pdfCard: {
    marginTop: "6px",
    padding: "8px 10px",
    background: "#fff3e0",
    borderRadius: "8px",
    border: "1px solid #ffcc80",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "12.5px",
  },
  videoCard: {
    marginTop: "6px",
    padding: "8px 10px",
    background: "#fce4ec",
    borderRadius: "8px",
    border: "1px solid #f48fb1",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "12.5px",
  },
  linkCard: {
    marginTop: "6px",
    padding: "8px 12px",
    background: "#e8f5e9",
    borderRadius: "8px",
    border: "1px solid #a5d6a7",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "12.5px",
    textDecoration: "none",
    color: "#1b5e20",
    fontWeight: 600,
    cursor: "pointer",
  },
  typing: {
    display: "flex",
    gap: "4px",
    padding: "10px 14px",
    background: "#fff",
    borderRadius: "18px 18px 18px 4px",
    width: "fit-content",
    boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
  },
  dot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    background: "#bbb",
    animation: "bounce 1.2s infinite",
  },
  inputRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "10px",
    borderTop: "1px solid #eee",
    background: "#fff",
    flexShrink: 0,
  },
  input: {
    flex: 1,
    padding: "9px 12px",
    borderRadius: "22px",
    border: "1.5px solid #ddd",
    fontSize: "13.5px",
    outline: "none",
    background: "#fafafa",
    resize: "none",
    fontFamily: "inherit",
    lineHeight: 1.4,
    maxHeight: "80px",
    overflowY: "auto",
  },
  sendBtn: {
    width: "38px",
    height: "38px",
    borderRadius: "50%",
    background: "#e53935",
    color: "#fff",
    border: "none",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    fontSize: "16px",
    flexShrink: 0,
  },
  clearBtn: {
    background: "none",
    border: "none",
    color: "#aaa",
    cursor: "pointer",
    fontSize: "16px",
    padding: "4px",
    lineHeight: 1,
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "4px 10px 8px",
    background: "#fff",
    flexShrink: 0,
  },
  langSelect: {
    fontSize: "12px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "3px 6px",
    background: "#fff",
    color: "#555",
    cursor: "pointer",
  },
  cacheTag: {
    fontSize: "10px",
    background: "#e8f5e9",
    color: "#388e3c",
    borderRadius: "4px",
    padding: "2px 5px",
    marginLeft: "4px",
  },
};

// ── Suggested intents based on last bot message ───────────────────────────
function extractSuggestedIntents(text) {
  const intents = [];
  if (/fee|cost|payment|challan/i.test(text))   intents.push({ label: "Fees breakdown",    query: "Tell me more about fee structure" });
  if (/admission|apply|eligibility/i.test(text)) intents.push({ label: "Admission process", query: "How does the admission process work?" });
  if (/placement|job|company|package/i.test(text)) intents.push({ label: "Top companies",  query: "Which companies visited APSIT for placements?" });
  if (/course|department|branch/i.test(text))    intents.push({ label: "Course details",   query: "What are the departments at APSIT?" });
  return intents.slice(0, 4);
}

// ── Main ChatWidget ───────────────────────────────────────────────────────
export default function ChatWidget({ close }) {
  const [messages,  setMessages]  = useState([
    {
      role: "bot",
      text: "👋 Hi! I'm the APSIT AI Assistant. Ask me anything about admissions, fees, courses, placements, or facilities!",
    }
  ]);
  const [query,     setQuery]     = useState("");
  const [loading,   setLoading]   = useState(false);
  const [language,  setLanguage]  = useState("auto");
  const [suggested, setSuggested] = useState([]);
  const [moodleMsg, setMoodleMsg] = useState("");

  const chatEndRef = useRef(null);
  const inputRef   = useRef(null);

  // auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // fetch Moodle teaser on open
  useEffect(() => {
    fetch(`${BACKEND_URL}/health`)
      .then(r => r.json())
      .then(d => {
        if (d.status === "running") {
          setMoodleMsg("📢 Check Moodle for latest announcements →");
        }
      })
      .catch(() => {});
  }, []);

  const sendQuery = useCallback(async (overrideQuery) => {
    const text = (overrideQuery || query).trim();
    if (!text || loading) return;

    setMessages(prev => [...prev, { role: "user", text }]);
    setQuery("");
    setSuggested([]);
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query:      text,
          session_id: SESSION_ID,
          language,
        }),
      });

      const data = await res.json();

      const botMsg = {
        role:       "bot",
        text:       data.answer || "Sorry, I couldn't find an answer.",
        images:     data.images  || [],
        pdfs:       data.pdfs    || [],
        videos:     data.videos  || [],
        links:      data.links   || [],
        from_cache: data.from_cache || false,
      };

      setMessages(prev => [...prev, botMsg]);
      setSuggested(extractSuggestedIntents(botMsg.text));

    } catch {
      setMessages(prev => [
        ...prev,
        { role: "bot", text: "❌ Server error. Please try again in a moment." },
      ]);
    }

    setLoading(false);
    inputRef.current?.focus();
  }, [query, language, loading]);

  const clearChat = () => {
    setMessages([{
      role: "bot",
      text: "Chat cleared! How can I help you?",
    }]);
    setSuggested([]);
    sessionStorage.removeItem("apsit_session_id");
  };

  return (
    <>
      {/* CSS animations */}
      <style>{`
        @keyframes popIn {
          from { opacity: 0; transform: scale(0.85) translateY(20px); }
          to   { opacity: 1; transform: scale(1)    translateY(0); }
        }
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30%            { transform: translateY(-6px); }
        }
        .intent-btn:hover { background: #ffebee !important; }
        .link-card:hover  { background: #c8e6c9 !important; }
        .send-btn:hover   { background: #c62828 !important; }
        ::-webkit-scrollbar        { width: 4px; }
        ::-webkit-scrollbar-thumb  { background: #ddd; border-radius: 4px; }
      `}</style>

      <div style={S.widget}>

        {/* HEADER */}
        <div style={S.header}>
          <div style={S.avatar}>🎓</div>
          <div style={S.headerText}>
            <div style={S.headerTitle}>APSIT Assistant</div>
            <div style={S.headerSub}>Always here to help · {SESSION_ID.slice(0,12)}</div>
          </div>
          <button style={S.closeBtn} onClick={close}>✕</button>
        </div>

        {/* MOODLE ANNOUNCEMENT BAR */}
        {moodleMsg && (
          <div style={S.moodleBar}>
            <span>📢</span>
            <a
              href="https://elearn.apsit.edu.in/moodle/"
              target="_blank"
              rel="noreferrer"
              style={{ color: "#6d4c00", fontSize: "11.5px" }}
            >
              {moodleMsg}
            </a>
          </div>
        )}

        {/* QUICK INTENT BUTTONS */}
        <div style={S.intentsRow}>
          {QUICK_INTENTS.map((qi, i) => (
            <button
              key={i}
              className="intent-btn"
              style={S.intentBtn}
              onClick={() => sendQuery(qi.query)}
            >
              {qi.label}
            </button>
          ))}
        </div>

        {/* CHAT AREA */}
        <div style={S.chat}>
          {messages.map((m, i) => (
            <div key={i} style={S.bubbleWrap(m.role)}>

              {m.role === "bot" && (
                <div style={S.botIcon}>A</div>
              )}

              <div>
                <div style={S.bubble(m.role)}>
                  {m.text}
                  {m.from_cache && <span style={S.cacheTag}>⚡ cached</span>}
                </div>

                {/* IMAGES */}
                {m.images?.map((img, idx) => (
                  <div key={idx} style={S.imgWrap}>
                    <img
                      src={img}
                      alt="APSIT"
                      style={{ width: "100%", display: "block" }}
                      loading="lazy"
                    />
                    <div style={S.imgActions}>
                      <a href={img} target="_blank" rel="noreferrer" style={S.imgLink}>🔍 Preview</a>
                      <a href={img} download style={S.imgLink}>⬇ Download</a>
                    </div>
                  </div>
                ))}

                {/* PDFs */}
                {m.pdfs?.map((pdf, idx) => (
                  <div key={idx} style={S.pdfCard}>
                    <span style={{ fontSize: "18px" }}>📄</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: "12px", marginBottom: "3px" }}>
                        {pdf.split("/").pop() || "Document"}
                      </div>
                      <div style={{ display: "flex", gap: "10px" }}>
                        <a href={pdf} target="_blank" rel="noreferrer"
                           style={{ color: "#e65100", fontSize: "11.5px", textDecoration: "none" }}>
                          👁 Preview
                        </a>
                        <a href={pdf} download
                           style={{ color: "#e65100", fontSize: "11.5px", textDecoration: "none" }}>
                          ⬇ Download
                        </a>
                      </div>
                    </div>
                  </div>
                ))}

                {/* VIDEOS */}
                {m.videos?.map((vid, idx) => (
                  <div key={idx} style={S.videoCard}>
                    <span style={{ fontSize: "18px" }}>▶️</span>
                    <a href={vid} target="_blank" rel="noreferrer"
                       style={{ color: "#880e4f", textDecoration: "none", fontSize: "12.5px", fontWeight: 600 }}>
                      Watch Video
                    </a>
                  </div>
                ))}

                {/* REDIRECT LINKS */}
                {m.links?.map((lnk, idx) => (
                  <a key={idx} href={lnk.url} target="_blank" rel="noreferrer"
                     className="link-card" style={S.linkCard}>
                    {lnk.label}
                  </a>
                ))}
              </div>
            </div>
          ))}

          {/* TYPING INDICATOR */}
          {loading && (
            <div style={S.bubbleWrap("bot")}>
              <div style={S.botIcon}>A</div>
              <div style={S.typing}>
                {[0, 0.2, 0.4].map((delay, i) => (
                  <div key={i} style={{
                    ...S.dot,
                    animationDelay: `${delay}s`,
                  }} />
                ))}
              </div>
            </div>
          )}

          {/* CONTEXTUAL SUGGESTIONS */}
          {suggested.length > 0 && !loading && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "4px" }}>
              {suggested.map((s, i) => (
                <button key={i} className="intent-btn" style={{ ...S.intentBtn, fontSize: "11px" }}
                        onClick={() => sendQuery(s.query)}>
                  {s.label}
                </button>
              ))}
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* INPUT ROW */}
        <div style={S.inputRow}>
          <textarea
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Ask about fees, courses, placements..."
            style={S.input}
            rows={1}
            onKeyDown={e => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendQuery();
              }
            }}
          />
          <button className="send-btn" style={S.sendBtn} onClick={() => sendQuery()}>
            ➤
          </button>
        </div>

        {/* TOOLBAR */}
        <div style={S.toolbar}>
          <span style={{ fontSize: "12px", color: "#aaa" }}>🌐</span>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            style={S.langSelect}
          >
            {LANGUAGES.map(l => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
          <span style={{ flex: 1 }} />
          <button
            style={S.clearBtn}
            title="Clear conversation"
            onClick={clearChat}
          >
            🗑
          </button>
        </div>

      </div>
    </>
  );
}
