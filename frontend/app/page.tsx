"use client";

import { useState } from "react";
import Link from "next/link";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ChatMain } from "@/components/chat/chat-main";
import { ThemeToggle } from "@/components/theme-toggle";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { GridPattern } from "@/components/ui/grid-pattern";
import { BracesIcon, MenuIcon, NetworkIcon } from "lucide-react";

export default function ChatPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="hidden md:block w-64 border-r border-border">
        <ChatSidebar />
      </div>

      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent
          side="left"
          className="w-64 p-0 border-none [&>button]:hidden"
        >
          <ChatSidebar />
        </SheetContent>
      </Sheet>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex md:hidden items-center justify-between border-b border-border px-4 h-14 bg-background z-20">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setSidebarOpen(true)}
          >
            <MenuIcon className="size-5" />
          </Button>

          <div className="flex items-center gap-2">
            <Link href="/ml">
              <Button variant="outline" size="icon-sm" title="Explorateur Random Forest">
                <NetworkIcon className="size-4" />
              </Button>
            </Link>
            <Link href="/prolog">
              <Button variant="outline" size="icon-sm" title="Banc de test Prolog">
                <BracesIcon className="size-4" />
              </Button>
            </Link>
            <ThemeToggle />
          </div>
        </div>

        <div className="hidden md:flex absolute top-4 right-4 gap-2 z-20">
          <Link href="/ml">
            <Button variant="outline" size="sm" className="gap-2">
              <NetworkIcon className="size-4" />
              Random Forest
            </Button>
          </Link>
          <Link href="/prolog">
            <Button variant="outline" size="sm" className="gap-2">
              <BracesIcon className="size-4" />
              Test Prolog
            </Button>
          </Link>
          <ThemeToggle />
        </div>

        <div className="flex-1 overflow-hidden relative">
          <GridPattern className="pointer-events-none" />

          <div className="relative z-10 h-full">
            <ChatMain />
          </div>
        </div>
      </div>
    </div>
  );
}
