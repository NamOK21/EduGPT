// src/components/ChatUI.js
import React from "react";
import { motion, AnimatePresence } from "framer-motion";

function ChatUI({
  messages,
  loading,
  botTyping,
  chatBoxRef,
  input,
  setInput,
  handleSend,
  handleKeyDown,
  suggestions,
  darkMode,
  toggleDarkMode,
}) {
  return (
    <>
      <div className="app-container">
        <header className="header">
          <h1>🎓 Trợ lý giáo dục</h1>
          <button className="theme-toggle" onClick={toggleDarkMode}>
            {darkMode ? "🌞 Sáng" : "🌙 Tối"}
          </button>
        </header>

        <div className="chat-box" ref={chatBoxRef}>
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`chat-message ${msg.role}`}
              >
                <div className="avatar">
                  {msg.role === "user" ? "🧑‍🎓" : "🤖"}
                </div>
                <div className="message-content">{msg.content}</div>
              </motion.div>
            ))}
            {loading && (
              <motion.div
                key="typing"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="chat-message assistant"
              >
                <div className="avatar">🤖</div>
                <div className="message-content typing">{botTyping}</div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="input-area">
          <textarea
            placeholder="Nhập câu hỏi..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
          />
          <button onClick={() => handleSend()} disabled={loading}>
            📤 Gửi
          </button>
        </div>

        <div className="suggested-container">
          <h3>💡 Câu hỏi gợi ý:</h3>
          <div className="suggested-grid">
            {suggestions.map((q, idx) => (
              <motion.button
                key={idx}
                className="suggested-btn"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleSend(q)}
                disabled={loading}
              >
                {q}
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      <footer className="footer">
        <img src="../assets/sfb-logo.png" alt="SFB Logo" className="footer-logo"/>
        <span>
          © {new Date().getFullYear()} EduGPT by SFB Technology. All rights
          reserved.
        </span>
      </footer>
    </>
  );
}

export default ChatUI;
