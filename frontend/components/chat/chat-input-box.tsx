import {
  PaperclipIcon,
  CircleDashedIcon,
  SparklesIcon,
  ChevronDownIcon,
  CheckIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Logo } from "@/components/ui/logo";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";



interface ChatInputBoxProps {
  message: string;
  onMessageChange: (value: string) => void;
  onSend: () => void;
  selectedModel: string;
  onModelChange: (modelId: string) => void;
  showTools?: boolean;
  placeholder?: string;
}

export function ChatInputBox({
  message,
  onMessageChange,
  onSend,
  selectedModel,
  onModelChange,
  showTools = true,
  placeholder = "Ecrire ici...",
}: ChatInputBoxProps) {
  return (
    <div className="rounded-2xl border border-border bg-secondary dark:bg-card p-1">
      <div className="rounded-xl border border-border dark:border-transparent bg-card dark:bg-secondary">
        <Textarea
          placeholder={placeholder}
          value={message}
          onChange={(e) => onMessageChange(e.target.value)}
          className="min-h-[120px] resize-none border-0 bg-transparent px-4 py-3 text-base placeholder:text-muted-foreground/60 focus-visible:ring-0 focus-visible:ring-offset-0"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
        />

        <div className="flex items-center justify-between px-4 py-3 border-t border-border/50">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon-sm"
              className="size-7 rounded-full border border-border dark:border-input bg-card dark:bg-secondary hover:bg-accent"
            >
              <PaperclipIcon className="size-4 text-muted-foreground" />
            </Button>
            {showTools && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1.5 h-7 rounded-full border border-border dark:border-input bg-card dark:bg-secondary hover:bg-accent px-3"
                >
                  <CircleDashedIcon className="size-4 text-muted-foreground" />
                  <span className="hidden sm:inline text-sm text-muted-foreground/70">
                    Orientation guidée
                  </span>
                </Button>
              </>
            )}
          </div>

          
        </div>
      </div>
    </div>
  );
}

