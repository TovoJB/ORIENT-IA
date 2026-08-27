import { cn } from "@/lib/utils";
import { Logo } from "@/components/ui/logo";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Fragment } from "react";

interface Message {
  id: string;
  content: string;
  sender: "user" | "ai";
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
}

// ---------------------------------------------------------------------------
// Rendu Markdown maison (sans dépendance externe) — gère :
//   - **gras** / *italique* / `code inline`
//   - ### H3 / ## H2 / # H1
//   - --- séparateur horizontal
//   - * item / - item / 1. item (listes)
//   - Sauts de ligne
// ---------------------------------------------------------------------------

function renderInline(text: string): React.ReactNode[] {
  // Motifs : `code` > **gras** > *italique*
  const parts: React.ReactNode[] = [];
  const re = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = re.exec(text)) !== null) {
    if (match.index > last) {
      parts.push(<Fragment key={key++}>{text.slice(last, match.index)}</Fragment>);
    }
    const token = match[0];
    if (token.startsWith("`") && token.endsWith("`")) {
      parts.push(
        <code key={key++} className="bg-muted/70 px-1 py-0.5 rounded text-[90%] font-mono">
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("**")) {
      parts.push(<strong key={key++} className="font-semibold">{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("*")) {
      parts.push(<em key={key++}>{token.slice(1, -1)}</em>);
    }
    last = match.index + token.length;
  }
  if (last < text.length) {
    parts.push(<Fragment key={key++}>{text.slice(last)}</Fragment>);
  }
  return parts;
}

function renderMarkdown(content: string): React.ReactNode {
  const lines = content.split("\n");
  const nodes: React.ReactNode[] = [];
  let listItems: React.ReactNode[] = [];
  let listType: "ul" | "ol" | null = null;
  let nodeKey = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    if (listType === "ol") {
      nodes.push(<ol key={nodeKey++} className="list-decimal list-outside ml-4 space-y-0.5 my-1">{listItems}</ol>);
    } else {
      nodes.push(<ul key={nodeKey++} className="list-disc list-outside ml-4 space-y-0.5 my-1">{listItems}</ul>);
    }
    listItems = [];
    listType = null;
  };

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const line = raw.trimEnd();

    // Separateur ---
    if (/^---+$/.test(line.trim())) {
      flushList();
      nodes.push(<hr key={nodeKey++} className="border-border/50 my-2" />);
      continue;
    }

    // Titres H1/H2/H3
    const hMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (hMatch) {
      flushList();
      const level = hMatch[1].length;
      const text = hMatch[2];
      const cls = level === 1
        ? "text-base font-bold mt-3 mb-1"
        : level === 2
        ? "text-sm font-bold mt-2 mb-1"
        : "text-xs font-semibold uppercase tracking-wide mt-2 mb-0.5 text-muted-foreground";
      nodes.push(
        <p key={nodeKey++} className={cls}>{renderInline(text)}</p>
      );
      continue;
    }

    // Liste non-ordonnée : * ou -
    const ulMatch = line.match(/^[*-]\s+(.+)$/);
    if (ulMatch) {
      if (listType === "ol") flushList();
      listType = "ul";
      listItems.push(
        <li key={nodeKey++} className="leading-relaxed">{renderInline(ulMatch[1])}</li>
      );
      continue;
    }

    // Liste ordonnée : 1. 2. …
    const olMatch = line.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      if (listType === "ul") flushList();
      listType = "ol";
      listItems.push(
        <li key={nodeKey++} className="leading-relaxed">{renderInline(olMatch[1])}</li>
      );
      continue;
    }

    // Ligne vide
    if (line.trim() === "") {
      flushList();
      nodes.push(<br key={nodeKey++} />);
      continue;
    }

    // Paragraphe normal
    flushList();
    nodes.push(
      <p key={nodeKey++} className="leading-relaxed">{renderInline(line)}</p>
    );
  }

  flushList();
  return <>{nodes}</>;
}

// ---------------------------------------------------------------------------

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div
      className={cn(
        "flex gap-4",
        message.sender === "user" ? "justify-end" : "justify-start"
      )}
    >
      {message.sender === "ai" && (
        <div className="shrink-0">
          <div className="size-8 rounded-full bg-secondary flex items-center justify-center">
            <Logo className="size-6" />
          </div>
        </div>
      )}

      <div
        className={cn(
          "rounded-2xl px-4 py-3 max-w-[80%] text-sm",
          message.sender === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-secondary"
        )}
      >
        {message.sender === "ai"
          ? renderMarkdown(message.content)
          : <p className="leading-relaxed">{message.content}</p>
        }
      </div>

      {message.sender === "user" && (
        <div className="shrink-0">
          <Avatar className="size-8">
            <AvatarImage src="/ln.png" alt="User" />
            <AvatarFallback>U</AvatarFallback>
          </Avatar>
        </div>
      )}
    </div>
  );
}
