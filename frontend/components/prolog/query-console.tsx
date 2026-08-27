"use client";

import { useState } from "react";
import { PlayIcon, Loader2Icon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { PrologQueryResult } from "@/lib/api";

interface QueryConsoleProps {
  onRun: (requete: string) => Promise<PrologQueryResult>;
}

export function QueryConsole({ onRun }: QueryConsoleProps) {
  const [requete, setRequete] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<PrologQueryResult | null>(null);

  const run = async () => {
    if (!requete.trim() || running) return;
    setRunning(true);
    try {
      const res = await onRun(requete.trim());
      setResult(res);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-muted/40 p-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-xs font-semibold text-muted-foreground">?- </span>
        <Input
          value={requete}
          onChange={(e) => setRequete(e.target.value)}
          placeholder="ex : parcours(P), score_compatibilite(S, isaia, Sc)"
          onKeyDown={(e) => {
            if (e.key === "Enter") run();
          }}
          className="h-8 font-mono text-xs"
        />
        <Button size="sm" onClick={run} disabled={!requete.trim() || running}>
          {running ? <Loader2Icon className="size-3.5 animate-spin" /> : <PlayIcon className="size-3.5" />}
          Exécuter
        </Button>
      </div>

      {result && (
        <div className="space-y-1 font-mono text-xs">
          {result.erreur ? (
            <p className="rounded bg-destructive/10 px-2 py-1.5 text-destructive">{result.erreur}</p>
          ) : (
            <>
              <p className="text-muted-foreground">
                {result.resultats.length} résultat{result.resultats.length > 1 ? "s" : ""}
              </p>
              {result.resultats.length === 0 ? (
                <p className="text-muted-foreground">false.</p>
              ) : (
                result.resultats.map((row, i) => (
                  <p key={i} className="text-foreground">
                    {Object.entries(row).map(([k, v]) => `${k} = ${v}`).join(", ")}
                  </p>
                ))
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
