import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import ChatUI from "./ChatUI";
import "./App.css";


const LOCAL_KEY = "edu-chat-history";
const SUGGESTED_QUESTIONS = [
  "Mục tiêu của chương trình giáo dục phổ thông là gì?",
  "Môn Tiếng Anh ở cấp trung học cơ sở dạy gì?",
  "Học sinh được đánh giá thế nào trong môn Giáo dục thể chất?",
  "Môn Toán ở tiểu học gồm những nội dung gì?",
  "Chương trình có chia giai đoạn giáo dục không?",
  "Các môn học bắt buộc và tự chọn gồm những gì?",
  "Giáo dục định hướng nghề nghiệp bắt đầu từ lớp mấy?",
  "Yêu cầu cần đạt trong môn Lịch sử là gì?",
  "Chương trình môn Địa lý giúp học sinh phát triển năng lực nào?",
  "Nội dung giáo dục của địa phương được dạy như thế nào?",
];

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [botTyping, setBotTyping] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [darkMode, setDarkMode] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const chatBoxRef = useRef(null);

  useEffect(() => {
    const stored = localStorage.getItem(LOCAL_KEY);
    if (stored) setMessages(JSON.parse(stored));
    setSuggestions([...SUGGESTED_QUESTIONS].sort(() => 0.5 - Math.random()).slice(0, 6));
  }, []);

  useEffect(() => {
    chatBoxRef.current?.scrollTo(0, chatBoxRef.current.scrollHeight);
    localStorage.setItem(LOCAL_KEY, JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    document.body.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const handleSend = async (customInput) => {
    const trimmed = (customInput ?? input).trim();
    if (!trimmed) return;
    const userMessage = {
      role: "user",
      content: trimmed,
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setBotTyping("⏳ Đang trả lời...");

    try {
      const res = await axios.post("http://localhost:5678/ask", { question: trimmed });
      simulateTyping(res.data.answer || "❌ Không có phản hồi.");
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
        setMessages((prev) => [...prev, 
          {
            role: "assistant",
            content: text,
            timestamp: new Date().toISOString()
          }
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

  const handleFileChange = (e) => {
    setSelectedFiles([...e.target.files]);
    setUploadStatus("");
  };

  const handleUploadConfirm = async () => {
    if (selectedFiles.length === 0) return;
    setUploadStatus("⏳ Đang xử lý các file...");
    for (let file of selectedFiles) {
      const formData = new FormData();
      formData.append("file", file);
      try {
        const res = await axios.post("http://localhost:5678/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setUploadStatus((prev) => prev + `\n📄 ${file.name}: ${res.data.message}`);
      } catch {
        setUploadStatus((prev) => prev + `\n❌ ${file.name}: Lỗi xử lý.`);
      }
    }
    setSelectedFiles([]);
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
    />
  );
}

export default App;