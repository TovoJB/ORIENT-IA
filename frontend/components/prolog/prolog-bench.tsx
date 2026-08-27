"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCcwIcon, FlaskConicalIcon, Loader2Icon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { runPrologQuery, testProlog, type PrologQueryResult, type PrologTestResult } from "@/lib/api";
import { PrologForm } from "./prolog-form";
import { ReasoningPanel } from "./reasoning-panel";
import { QueryConsole } from "./query-console";
import { buildProfileFromForm, emptyForm, type ProfileForm } from "./profile-form";

export function PrologBench() {
  const [form, setForm] = useState<ProfileForm>(emptyForm);
  const [forceProlog, setForceProlog] = useState(false);
  const [result, setResult] = useState<PrologTestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const evaluate = useCallback(
    async (profil: Record<string, string>, force: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const res = await testProlog(profil, force);
        setResult(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const profile = buildProfileFromForm(form);

  useEffect(() => {
    const profil = buildProfileFromForm(form);
    const handler = setTimeout(() => {
      if (Object.keys(profil).length > 0) {
        evaluate(profil, forceProlog);
      } else {
        setResult(null);
      }
    }, 350);
    return () => clearTimeout(handler);
  }, [form, forceProlog, evaluate]);

  const runQuery = async (requete: string): Promise<PrologQueryResult> =>
    runPrologQuery(profile, requete);

  return (
    <div className="flex h-full flex-col gap-4 p-4 lg:p-6 lg:flex-row">
      {/* Formulaire profil étudiant */}
      <div className="lg:w-[380px] lg:shrink-0 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <FlaskConicalIcon className="size-4 text-primary" />
            Profil étudiant
          </div>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setForceProlog((v) => !v)}
              className={cn(
                "rounded-full border px-2.5 py-1 text-[10px] font-semibold transition-colors",
                forceProlog
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border bg-muted/40 text-muted-foreground"
              )}
              title="Désactive le miroir Python : force l'utilisation EXCLUSIVE de SWI-Prolog"
            >
              {forceProlog ? "SWI-Prolog exclusif" : "Mode auto"}
            </button>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => setForm(emptyForm())}
              title="Réinitialiser le formulaire"
            >
              <RefreshCcwIcon className="size-4" />
            </Button>
          </div>
        </div>

        <div className="overflow-y-auto rounded-2xl border border-border bg-card p-4 lg:max-h-[calc(100vh-140px)]">
          <PrologForm form={form} onChange={setForm} />
        </div>

        <p className="text-[11px] text-muted-foreground">
          Le raisonnement se met à jour automatiquement à chaque modification.
        </p>
      </div>

      {/* Panneau de raisonnement temps réel */}
      <div className="flex-1 min-w-0 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <span className="relative flex size-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
              <span className="relative inline-flex size-2 rounded-full bg-primary" />
            </span>
            Raisonnement Prolog (temps réel)
          </div>
          {profile && Object.keys(profile).length > 0 && (
            <span className="hidden md:block max-w-[40%] truncate font-mono text-[10px] text-muted-foreground">
              {JSON.stringify(profile)}
            </span>
          )}
        </div>

        {error && (
          <p className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">
            {error}
          </p>
        )}

        <div className="overflow-y-auto rounded-2xl border border-border bg-card p-4 lg:max-h-[calc(100vh-140px)]">
          <ReasoningPanel result={result} loading={loading} />
        </div>

        <div>
          <p className="mb-1.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {loading ? (
              <Loader2Icon className="size-3.5 animate-spin" />
            ) : (
              <span className="size-1.5 rounded-full bg-primary" />
            )}
            Console Prolog (requêtes libres)
          </p>
          <QueryConsole onRun={runQuery} />
        </div>
      </div>
    </div>
  );
}
