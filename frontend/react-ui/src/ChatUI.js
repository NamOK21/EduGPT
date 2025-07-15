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
  handleClearHistory,
  handleMoreSuggestions,
  loadingSuggestions,
  setSelectedFiles,
}) {
  return (
    <>
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
                  initial={{ opacity: 0, y: isUser ? 20 : -20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ type: "spring", stiffness: 300, damping: 20 }}
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
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
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

        {suggestions.length > 0 && (
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
                      animation: "spin 1s linear infinite",
                    }}
                  />
                ) : (
                  "🔁 Tôi muốn hỏi thêm"
                )}
              </motion.button>
            </div>
          </div>
        )}

        {/* UPLOAD FILE */}
        <div
          className="upload-dropzone"
          onDrop={(e) => {
            e.preventDefault();
            const droppedFiles = Array.from(e.dataTransfer.files);
            handleFileChange(droppedFiles);
          }}
          onDragOver={(e) => e.preventDefault()}
        >
          <label className="upload-label">
            📎 Kéo & thả file hoặc
            <input
              type="file"
              multiple
              hidden
              onChange={(e) => handleFileChange(Array.from(e.target.files))}
            />
            <span className="upload-button"> Chọn file</span>
          </label>

          {selectedFiles.length > 0 && (
            <div className="file-preview-list">
              {selectedFiles.map((file, idx) => (
                <div
                  key={idx}
                  className={`file-chip ${
                    uploadStatus.errors.includes(file.name)
                      ? "error"
                      : uploadStatus.successCount > 0
                      ? "success"
                      : ""
                  }`}
                >
                  📄 {file.name}
                  {uploadStatus.errors.includes(file.name) && " ❌"}
                  {!uploadStatus.errors.includes(file.name) &&
                    uploadStatus.successCount > 0 &&
                    " ✅"}
                </div>
              ))}
              <div className="upload-actions">
                <button onClick={handleUploadConfirm} className="upload-confirm">✅ Tải lên</button>
                <button onClick={() => setSelectedFiles([])} className="clear-btn">🗑️ Xoá</button>
              </div>
            </div>
          )}

          {uploadProgress > 0 && uploadProgress < 100 && (
            <div className="progress-wrapper">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <div className="progress-label">{uploadProgress}%</div>
            </div>
          )}
        </div>
      </div>

      <footer className="footer">
        <img src="/assets/tmplogo.jpg" alt="SFB Logo" className="footer-logo" />
        <span>© {new Date().getFullYear()}. All rights reserved.</span>
      </footer>
    </>
  );
}

export default ChatUI;
