# Frontend — Clinique AI (Next.js)

Interface de chat basée sur le template [square-ui](https://github.com/zerostaticthemes/square-ui/tree/master/templates-baseui/chat), branchée sur le backend FastAPI.

```bash
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                  # -> http://localhost:3000
```

### Structure

- `app/page.tsx` — layout principal (sidebar + zone de chat)
- `components/chat/` — ChatMain (état), ChatInputBox, ChatMessage, ChatConversationView, ChatWelcomeScreen, ChatSidebar
- `lib/api.ts` — client HTTP vers le backend (`/chat`, `/predict`)
- `store/chat-store.ts` — état global (Zustand) pour la sidebar

Le backend doit tourner sur `http://localhost:8000` (voir `../README.md`).
