import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import ChatUI from "./ChatUI";
import "./App.css";

const LOCAL_KEY = "edu-chat-history";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [botTyping, setBotTyping] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [darkMode, setDarkMode] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ total: 0, successCount: 0, errors: [] });
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const chatBoxRef = useRef(null);
  const [lastQuestion, setLastQuestion] = useState("");
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(LOCAL_KEY);
    if (stored) {
      try {
        setMessages(JSON.parse(stored));
      } catch (e) {
        console.error("❌ Lỗi đọc lịch sử:", e);
      }
    }
    setSuggestions([]);
  }, []);

  useEffect(() => {
    localStorage.setItem(LOCAL_KEY, JSON.stringify(messages));
    chatBoxRef.current?.scrollTo(0, chatBoxRef.current.scrollHeight);
  }, [messages]);

  useEffect(() => {
    document.body.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const handleSend = async (customInput) => {
    const inputValue = customInput ?? input;
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    const userMessage = {
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setLastQuestion(trimmed);
    setBotTyping("⏳ Đang trả lời...");

    try {
      const res = await axios.post("/ask", { question: trimmed });
      simulateTyping(res.data.answer || "❌ Không có phản hồi.");
      setSuggestions((res.data.related_questions || []).slice(0, 6));
    } catch {
      simulateTyping("❌ Lỗi kết nối đến máy chủ.");
    }

    setLoading(false);
  };

  const simulateTyping = (text) => {
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setBotTyping(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(interval);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: text,
            timestamp: new Date().toISOString(),
          },
        ]);
        setBotTyping("");
      }
    }, 15);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (files) => {
    setSelectedFiles(files);
    setUploadStatus({ total: 0, successCount: 0, errors: [] });
  };

  const handleUploadConfirm = async () => {
    if (selectedFiles.length === 0) return;
    setUploadStatus({ total: selectedFiles.length, successCount: 0, errors: [] });
    setUploadProgress(1);

    let successCount = 0;
    let errors = [];

    for (let i = 0; i < selectedFiles.length; i++) {
      const file = selectedFiles[i];
      const formData = new FormData();
      formData.append("file", file);

      try {
        await axios.post("http://localhost:5678/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (e) => {
            const percent = Math.round(((i + e.loaded / e.total) / selectedFiles.length) * 100);
            setUploadProgress(percent);
          },
        });
        successCount++;
      } catch {
        errors.push(file.name);
      }

      setUploadStatus({ total: selectedFiles.length, successCount, errors });
    }

    setUploadProgress(100);
    setTimeout(() => setUploadProgress(0), 1500);
    setSelectedFiles([]);
  };

  const handleClearHistory = () => {
    if (window.confirm("Bạn có chắc muốn xoá toàn bộ lịch sử trò chuyện?")) {
      setMessages([]);
      setSuggestions([]);
      setLastQuestion("");
      localStorage.removeItem(LOCAL_KEY);
    }
  };

  const handleMoreSuggestions = async () => {
    if (!lastQuestion) return;
  
    setSuggestions([]);
    setLoadingSuggestions(true);
  
    try {
      const res = await axios.post(
        "/related_questions",
        { question: lastQuestion },
        {
          headers: {
            "Content-Type": "application/json"
          }
        }
      );
      setSuggestions((res.data.related_questions || []).slice(0, 6));
    } catch (err) {
      console.error("❌ Lỗi gọi /related_questions:", err);
    } finally {
      setLoadingSuggestions(false);
    }
  };
  

  return (
    <ChatUI
      messages={messages}
      loading={loading}
      botTyping={botTyping}
      chatBoxRef={chatBoxRef}
      input={input}
      setInput={setInput}
      handleSend={handleSend}
      handleKeyDown={handleKeyDown}
      suggestions={suggestions}
      darkMode={darkMode}
      toggleDarkMode={() => setDarkMode(!darkMode)}
      selectedFiles={selectedFiles}
      handleFileChange={handleFileChange}
      handleUploadConfirm={handleUploadConfirm}
      uploadStatus={uploadStatus}
      uploadProgress={uploadProgress}
      handleClearHistory={handleClearHistory}
      handleMoreSuggestions={handleMoreSuggestions}
      loadingSuggestions={loadingSuggestions}
      setSelectedFiles={setSelectedFiles}
    />
  );
}

export default App;
