"use client";

import { useState } from "react";
import {
  ChevronDownIcon,
  ChevronRightIcon,
  BrainCircuitIcon,
  GitBranchIcon,
  ListTreeIcon,
  ScaleIcon,
  TerminalIcon,
  Loader2Icon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { PrologTestResult } from "@/lib/api";

interface ReasoningPanelProps {
  result: PrologTestResult | null;
  loading: boolean;
}

function Section({
  title,
  icon,
  defaultOpen = true,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-muted/40">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:bg-muted/60"
      >
        {open ? (
          <ChevronDownIcon className="size-3.5" />
        ) : (
          <ChevronRightIcon className="size-3.5" />
        )}
        {icon}
        {title}
      </button>
      {open && <div className="space-y-2 px-3 py-2 text-xs">{children}</div>}
    </div>
  );
}

export function ReasoningPanel({ result, loading }: ReasoningPanelProps) {
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center py-16 text-sm text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin mr-2" />
        Évaluation du profil par les règles Prolog...
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex h-full items-center justify-center py-16 text-sm text-muted-foreground">
        Renseignez le profil étudiant à gauche pour voir le raisonnement.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2 rounded-lg border border-border bg-muted/40 px-3 py-2">
        <div className="flex items-center gap-2 text-xs">
          <BrainCircuitIcon className="size-4 text-primary" />
          <span className="font-semibold">Moteur de règles</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold",
              result.moteur === "swipl"
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground"
            )}
          >
            {result.moteur}
          </span>
          {result.force_prolog && (
            <span className="rounded-full bg-destructive/10 text-destructive px-2 py-0.5 text-[10px] font-semibold">
              prolog exclusif
            </span>
          )}
        </div>
      </div>

      {result.erreur_prolog && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {result.erreur_prolog}
        </p>
      )}

      {result.moteur === "fallback" && (
        <p className="rounded-lg bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
          SWI-Prolog n&apos;est pas utilisé : le raisonnement est simulé par le
          miroir Python des règles (aucune requête Prolog réelle).
        </p>
      )}

      <Section title="Faits assertés dans Prolog" icon={<TerminalIcon className="size-3.5" />}>
        <div className="space-y-0.5 font-mono">
          {result.faits.map((fact, i) => (
            <p key={i} className="text-foreground">
              assertz(({fact})).
            </p>
          ))}
          {result.faits.length === 0 && (
            <p className="text-muted-foreground">(aucun fait — profil vide)</p>
          )}
        </div>
      </Section>

      <Section
        title="Éligibilité — parcours_possibles/2"
        icon={<GitBranchIcon className="size-3.5" />}
      >
        {result.eligibilite.possibles.length === 0 ? (
          <p className="font-mono">(aucun parcours éligible)</p>
        ) : (
          <div className="space-y-1">
            {result.eligibilite.possibles.map((code) => {
              const score = result.scores.find((s) => s.parcours === code);
              const arguments_ = [
                score?.motifs.matieres.length && `matières : ${score.motifs.matieres.join(", ")}`,
                score?.motifs.competences.length && `compétences : ${score.motifs.competences.join(", ")}`,
                score?.motifs.interets.length && `intérêts : ${score.motifs.interets.join(", ")}`,
                score?.motifs.metier_alignee && "métier visé préparé ✓",
                score?.motifs.suggestions?.length && `suggestions : ${score.motifs.suggestions.join(", ")}`,
              ].filter(Boolean);
              return (
                <div
                  key={code}
                  className="rounded-md border border-border/60 bg-background px-2 py-1.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono font-semibold text-foreground">
                      ✓ {code}
                    </span>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      score {score?.score ?? 0}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    {arguments_.join(" · ") || "aucun motif de compatibilité"}
                  </p>
                </div>
              );
            })}
          </div>
        )}
        {result.eligibilite.bloques.length > 0 && (
          <div className="space-y-1">
            {result.eligibilite.bloques.map((b) => (
              <p key={b.parcours} className="text-muted-foreground">
                <span className="font-mono text-foreground">+ {b.parcours}</span>
                <span className="text-destructive"> ✗ </span>
                {b.raisons.join(" ; ")}
              </p>
            ))}
          </div>
        )}
      </Section>

      <Section
        title="Scores de compatibilité — score_compatibilite/3"
        icon={<ScaleIcon className="size-3.5" />}
      >
        <div className="space-y-2">
          {result.scores.length === 0 && (
            <p className="text-muted-foreground">(aucun parcours éligible)</p>
          )}
          {result.scores.map((score) => (
            <div key={score.parcours} className="rounded-lg border border-border/60 bg-background p-2">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono font-semibold">{score.parcours}</span>
                <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground">
                  {score.categorie}
                </span>
              </div>
              <div className="mt-1.5 flex items-center gap-2">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${Math.min(100, score.score * 10)}%` }}
                  />
                </div>
                <span className="font-mono text-muted-foreground">
                  {score.score} pt{score.score > 1 ? "s" : ""}
                </span>
              </div>
              {[
                score.motifs.matieres.length && `matières : ${score.motifs.matieres.join(", ")}`,
                score.motifs.competences.length && `compétences : ${score.motifs.competences.join(", ")}`,
                score.motifs.interets.length && `intérêts : ${score.motifs.interets.join(", ")}`,
                score.motifs.metier_alignee && "métier visé préparé ✓",
                score.motifs.suggestions?.length && `suggestions : ${score.motifs.suggestions.join(", ")}`,
              ]
                .filter(Boolean)
                .map((line) => (
                  <p key={line as string} className="mt-0.5 text-[11px] text-muted-foreground">
                    {line}
                  </p>
                ))}
            </div>
          ))}
        </div>
      </Section>

      <Section
        title={`Requêtes Prolog exécutées (${result.requetes.length})`}
        icon={<ListTreeIcon className="size-3.5" />}
        defaultOpen={result.requetes.length <= 8}
      >
        {result.requetes.length === 0 && (
          <p className="text-muted-foreground">(moteur de secours : aucune requête Prolog)</p>
        )}
        <div className="space-y-1.5">
          {result.requetes.map((query, i) => (
            <div key={i} className="font-mono">
              <p className="text-foreground">?- {query.requete}</p>
              {query.resultats.length === 0 ? (
                <p className="pl-3 text-muted-foreground">false.</p>
              ) : (
                query.resultats.map((row, j) => (
                  <p key={j} className="pl-3 text-muted-foreground">
                    {Object.entries(row).map(([k, v]) => `${k} = ${v}`).join(", ")}
                  </p>
                ))
              )}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
