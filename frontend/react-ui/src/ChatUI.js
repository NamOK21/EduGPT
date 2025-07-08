// =========================================
// IMPORT
// =========================================
import React from "react";
import { motion, AnimatePresence } from "framer-motion";

// =========================================
// COMPONENT CHÍNH CHATUI
// =========================================
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
  handleClearHistory,
  handleMoreSuggestions,
  loadingSuggestions

}) {
  return (
    <>
      {/* ========================================= */}
      {/* HEADER */}
      {/* ========================================= */}
      <div className="app-container">
        <header className="header">
          <h1 className="header">
            <img src="/assets/dang.png" alt="Đảng" className="header-icon" />
            AI ASSISTANT FOR THE COMMUNIST PARTY OF VIETNAM
          </h1>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button className="theme-toggle" onClick={toggleDarkMode}>
              {darkMode ? "🌙 Tối" : "🌞 Sáng"}
            </button>
            <button className="clear-history-btn" onClick={handleClearHistory}>
              🗑️ Xoá lịch sử
            </button>
          </div>
        </header>

        {/* ========================================= */}
        {/* KHUNG CHAT */}
        {/* ========================================= */}
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

        {/* ========================================= */}
        {/* INPUT CHAT */}
        {/* ========================================= */}
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

        {/* ========================================= */}
        {/* GỢI Ý CÂU HỎI */}
        {/* ========================================= */}
        {suggestions.length > 0 && (
          <div className="suggested-container">
          {suggestions.length > 0 && (
            <>
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
            </>
          )}
        
          <div style={{ textAlign: "center", marginTop: "10px" }}>
            <motion.button
              className="suggested-btn refresh-btn"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleMoreSuggestions}
              disabled={loadingSuggestions}
            >
              {loadingSuggestions ? (
                <span
                  style={{
                    display: "inline-block",
                    width: "18px",
                    height: "18px",
                    border: "2px solid #ccc",
                    borderTop: "2px solid #333",
                    borderRadius: "50%",
                    animation: "spin 1s linear infinite"
                  }}
                />
              ) : (
                "🔁 Tôi muốn hỏi thêm"
              )}
            </motion.button>
          </div>
        </div>
        
        
        )}

        {/* ========================================= */}
        {/* UPLOAD FILE */}
        {/* ========================================= */}
        <div className="upload-box">
          <h3>📎 Tải lên nhiều file (.pdf, .docx):</h3>
          <label className="custom-upload">
            + Chọn file
            <input
              type="file"
              accept=".pdf,.docx,.lsty"
              multiple
              onChange={handleFileChange}
              disabled={loading}
              hidden
            />
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

      {/* ========================================= */}
      {/* FOOTER */}
      {/* ========================================= */}
      <footer className="footer">
        <img src="/assets/tmplogo.jpg" alt="SFB Logo" className="footer-logo" />
        <span>© {new Date().getFullYear()} EduGPT by SFB Technology. All rights reserved.</span>
      </footer>
    </>
  );
}

export default ChatUI;
