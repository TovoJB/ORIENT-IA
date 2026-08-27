"use client";

import Link from "next/link";
import { ArrowLeftIcon, NetworkIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { RfExplorer } from "@/components/ml/rf-explorer";

export default function MlPage() {
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
            <NetworkIcon className="size-5 text-primary" />
            <div className="leading-tight">
              <p className="text-sm font-semibold">Explorateur Random Forest</p>
              <p className="text-[11px] text-muted-foreground">
                prédictions avec le modèle entraîné sauvegardé, en temps réel
              </p>
            </div>
          </div>
        </div>
        <ThemeToggle />
      </header>

      <main className="flex-1 overflow-hidden">
        <RfExplorer />
      </main>
    </div>
  );
}
