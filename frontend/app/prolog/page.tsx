"use client";

import Link from "next/link";
import { ArrowLeftIcon, BracesIcon, NetworkIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { PrologBench } from "@/components/prolog/prolog-bench";

export default function PrologPage() {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
        <div className="flex items-center gap-3">
          <Link href="/">
            <Button variant="ghost" size="icon-sm" title="Retour au chat ORIENT'IA">
              <ArrowLeftIcon className="size-5" />
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <BracesIcon className="size-5 text-primary" />
            <div className="leading-tight">
              <p className="text-sm font-semibold">Banc de test Prolog</p>
              <p className="text-[11px] text-muted-foreground">
                knowledge_base/orientia_rules.pl — raisonnement en temps réel
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/ml">
            <Button variant="outline" size="sm" className="gap-2">
              <NetworkIcon className="size-4" />
              Random Forest
            </Button>
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        <PrologBench />
      </main>
    </div>
  );
}
