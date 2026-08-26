"use client";

import { useState } from "react";
import { ChatWelcomeScreen } from "./chat-welcome-screen";
import { ChatConversationView } from "./chat-conversation-view";
import { sendChatMessage, sendPrediction } from "@/lib/api";

interface Message {
  id: string;
  content: string;
  sender: "user" | "ai";
  timestamp: Date;
}

export function ChatMain() {
  const [message, setMessage] = useState("");
  const [selectedMode, setSelectedMode] = useState("fast");
  const [selectedModel, setSelectedModel] = useState("gemini");
  const [isConversationStarted, setIsConversationStarted] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const appendMessage = (content: string, sender: "user" | "ai") => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${sender}-${Date.now()}-${Math.random()}`,
        content,
        sender,
        timestamp: new Date(),
      },
    ]);
  };

  const send = async (content: string) => {
    if (!content.trim() || isLoading) return;

    appendMessage(content, "user");
    setMessage("");
    setIsLoading(true);

    try {
      const reply = await sendChatMessage(content);
      appendMessage(reply, "ai");
    } catch (error) {
      appendMessage(`Erreur: ${(error as Error).message}`, "ai");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFirstSend = () => {
    if (!message.trim()) return;
    setIsConversationStarted(true);
    send(message);
  };

  const handlePredict = async () => {
    if (isLoading) return;
    setIsLoading(true);

    try {
      const result = await sendPrediction([5.1, 3.5, 1.4, 0.2]);
      const text = [
        `ML prediction: ${result.class_name}`,
        `Probabilities: ${result.probabilities
          .map((p) => `${(p * 100).toFixed(1)}%`)
          .join(", ")}`,
      ].join("\n");
      appendMessage(text, "ai");
    } catch (error) {
      appendMessage(`Erreur ML: ${(error as Error).message}`, "ai");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setIsConversationStarted(false);
    setMessages([]);
    setMessage("");
  };

  if (isConversationStarted) {
    return (
      <ChatConversationView
        messages={messages}
        message={message}
        isLoading={isLoading}
        onMessageChange={setMessage}
        onSend={send}
        onReset={handleReset}
        onPredict={handlePredict}
      />
    );
  }

  return (
    <ChatWelcomeScreen
      message={message}
      onMessageChange={setMessage}
      onSend={handleFirstSend}
      onPredict={handlePredict}
      selectedMode={selectedMode}
      onModeChange={setSelectedMode}
      selectedModel={selectedModel}
      onModelChange={setSelectedModel}
    />
  );
}
