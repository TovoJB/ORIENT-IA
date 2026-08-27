import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/logo";
import { cn } from "@/lib/utils";
import {
  ZapIcon,
  MessageCircleDashedIcon,
  WandSparklesIcon,
  BoxIcon,
} from "lucide-react";
import { ChatInputBox } from "./chat-input-box";

const chatModes = [
  { id: "fast", label: "Fast", icon: ZapIcon },
  { id: "in-depth", label: "In-depth", icon: MessageCircleDashedIcon },
  { id: "magic", label: "Magic AI", icon: WandSparklesIcon, pro: true },
  { id: "holistic", label: "Holistic", icon: BoxIcon },
];

interface ChatWelcomeScreenProps {
  message: string;
  onMessageChange: (value: string) => void;
  onSend: () => void;
  selectedMode: string;
  onModeChange: (modeId: string) => void;
  selectedModel: string;
  onModelChange: (modelId: string) => void;
}

export function ChatWelcomeScreen({
  message,
  onMessageChange,
  onSend,
  selectedMode,
  onModeChange,
  selectedModel,
  onModelChange,
}: ChatWelcomeScreenProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 md:px-8">
      <div className="absolute left-3 top-3 flex items-center gap-2">
        <img
          src="/download 1.png"
          alt="ISPM Logo"
          className="h-20 w-auto object-contain transition-opacity hover:opacity-80"
        />
      </div>
      <div className="w-full max-w-[640px] space-y-9 -mt-12">
        <div className="flex justify-center">
          <div className="flex items-center justify-center size-8 rounded-full">
            <Logo className="size-20" />
          </div>
        </div>

        <div className="space-y-4 text-center">
          <h1 className="text-3xl font-bold tracking-tight">
          Bonjour! Je suis{" "}
          <span className="bg-gradient-to-r from-emerald-400 via-teal-500 to-green-600 bg-clip-text text-transparent">
            ORIENT&apos;IA
          </span>
        </h1>
          <p className="text-2xl text-foreground">
             Votre assistant d'orientation à l'ISPM
          </p>
        </div>

        <ChatInputBox
          message={message}
          onMessageChange={onMessageChange}
          onSend={onSend}
          selectedModel={selectedModel}
          onModelChange={onModelChange}
          showTools={true}
        />

      </div>

      <div className="absolute bottom-6 text-center">
        <p className="text-sm text-muted-foreground">
          ORIENT&apos;IA est une aide à la décision, développé par Néocoders.
        </p>
      </div>
    </div>
  );
}

