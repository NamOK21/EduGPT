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
  selectedFiles,
  handleFileChange,
  handleUploadConfirm,
  uploadStatus,
  uploadProgress,
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
            {messages.map((msg, i) => {
              const isUser = msg.role === "user";
              const time = new Date(msg.timestamp).toLocaleTimeString("vi-VN", {
                hour: "2-digit",
                minute: "2-digit",
              });

              return (
                <motion.div
                  key={i}
                  className={`chat-message ${isUser ? "user" : "assistant"}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <img
                    className="avatar-img"
                    src={isUser ? "/assets/user-avatar.png" : "/assets/bot-avatar.png"}
                    alt="avatar"
                  />
                  <div className="bubble-group">
                    <div className="message-content">{msg.content}</div>
                    <div className="message-meta">{time}</div>
                  </div>
                </motion.div>
              );
            })}

            {loading && (
              <motion.div
                key="typing"
                className="chat-message assistant"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <img className="avatar-img" src="/assets/bot-avatar.png" alt="avatar" />
                <div className="bubble-group">
                  <div className="message-content typing">{botTyping}</div>
                  <div className="message-meta">...</div>
                </div>
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
          <button onClick={() => handleSend()} disabled={loading}>📤 Gửi</button>
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

        <div className="upload-box">
          <h3>📎 Tải lên nhiều file (.pdf, .docx):</h3>
          <label className="custom-upload">
            + Chọn file
            <input type="file" accept=".pdf,.docx" multiple onChange={handleFileChange} disabled={loading} hidden />
          </label>

          {selectedFiles.length > 0 && (
            <div className="file-preview">
              {selectedFiles.map((file, idx) => (
                <div key={idx} className="file-chip">📄 {file.name}</div>
              ))}
              <button className="upload-confirm" onClick={handleUploadConfirm}>✅ OK - Xử lý</button>
            </div>
          )}

          {uploadProgress > 0 && uploadProgress < 100 && (
            <div className="progress-wrapper">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
              </div>
              <div className="progress-label">{uploadProgress}%</div>
            </div>
          )}

          {uploadStatus.total > 0 && (
            <div className="upload-summary">
              <p>✅ Đã xử lý {uploadStatus.successCount}/{uploadStatus.total} file</p>
              {uploadStatus.errors.length > 0 && (
                <p>❌ Lỗi: <span className="error-file-list">{uploadStatus.errors.join(", ")}</span></p>
              )}
            </div>
          )}
        </div>
      </div>

      <footer className="footer">
        <img src="/assets/sfb-logo.png" alt="SFB Logo" className="footer-logo" />
        <span>© {new Date().getFullYear()} EduGPT by SFB Technology. All rights reserved.</span>
      </footer>
    </>
  );
}

export default ChatUI;
