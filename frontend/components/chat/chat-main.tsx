"use client";

import { useEffect, useState } from "react";
import { ChatWelcomeScreen } from "./chat-welcome-screen";
import { ChatConversationView } from "./chat-conversation-view";
import { useChatStore } from "@/store/chat-store";
import {
  sendChatTurn,
  type Question,
  type RecommendationResult,
} from "@/lib/api";

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

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [pendingQuestion, setPendingQuestion] = useState<Question | null>(null);
  const [selection, setSelection] = useState<string[]>([]);
  const [recommendation, setRecommendation] = useState<RecommendationResult | null>(null);
  const [profils, setProfils] = useState<Record<string, string>>({});

  // Synchronise profil + transcript vers le store (panneau gauche).
  const setCurrentProfile = useChatStore((s) => s.setCurrentProfile);
  const setCurrentTranscript = useChatStore((s) => s.setCurrentTranscript);
  const resetLiveSession = useChatStore((s) => s.resetLiveSession);

  useEffect(() => {
    setCurrentTranscript(messages);
  }, [messages, setCurrentTranscript]);

  useEffect(() => {
    if (conversationId) setCurrentProfile(profils);
  }, [conversationId, profils, setCurrentProfile]);

  const inputDisabled = isLoading || (pendingQuestion !== null && recommendation === null);

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

  const optionLabel = (value: string): string => {
    const option = pendingQuestion?.options.find((o) => o.value === value);
    return option ? option.label : value;
  };

  const applyTurn = (data: Awaited<ReturnType<typeof sendChatTurn>>) => {
    appendMessage(data.reply, "ai");
    setConversationId(data.conversation_id);
    setPendingQuestion(data.question);
    setRecommendation(data.recommendation);
    setSelection([]);
    if (data.profil) setProfils(data.profil);
  };

  const send = async (content: string) => {
    if (!content.trim() || isLoading) return;
    appendMessage(content, "user");
    setMessage("");
    setIsLoading(true);
    try {
      applyTurn(await sendChatTurn({ message: content, conversationId: conversationId ?? undefined }));
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

  const handleAnswer = async (explicitValue?: string[]) => {
    if (!pendingQuestion || isLoading) return;
    // Un éventuel argument non-tableau (ex: un événement de clic) est ignoré.
    const valeur = Array.isArray(explicitValue) ? explicitValue : selection;
    if (valeur.length === 0) return;

    appendMessage(
      valeur.map(optionLabel).join(", "),
      "user"
    );
    setSelection([]);
    setIsLoading(true);
    try {
      applyTurn(
        await sendChatTurn({
          answer: { champ: pendingQuestion.champ, valeur },
          conversationId: conversationId ?? undefined,
        })
      );
    } catch (error) {
      appendMessage(`Erreur: ${(error as Error).message}`, "ai");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleOption = (value: string) => {
    setSelection((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  };

  const selectSingle = (value: string) => {
    handleAnswer([value]);
  };

  const handleReset = () => {
    setIsConversationStarted(false);
    setMessages([]);
    setMessage("");
    setConversationId(null);
    setPendingQuestion(null);
    setRecommendation(null);
    setSelection([]);
    setProfils({});
    resetLiveSession();
  };

  if (isConversationStarted) {
    return (
      <ChatConversationView
        messages={messages}
        message={message}
        isLoading={isLoading}
        pendingQuestion={pendingQuestion}
        selection={selection}
        recommendation={recommendation}
        inputDisabled={inputDisabled}
        onMessageChange={setMessage}
        onSend={send}
        onReset={handleReset}
        onSelectOption={toggleOption}
        onSingleSelect={selectSingle}
        onValidateAnswer={handleAnswer}
      />
    );
  }

  return (
    <ChatWelcomeScreen
      message={message}
      onMessageChange={setMessage}
      onSend={handleFirstSend}
      selectedMode={selectedMode}
      onModeChange={setSelectedMode}
      selectedModel={selectedModel}
      onModelChange={setSelectedModel}
    />
  );
}
