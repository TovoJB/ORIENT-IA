"use client";

import { Loader2Icon, ActivityIcon, TargetIcon, BarChart3Icon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RfExploreResult } from "@/lib/api";

interface RfResultsPanelProps {
  result: RfExploreResult | null;
  loading: boolean;
}

function MetricCard({
  label,
  value,
  unit = "%",
  good,
}: {
  label: string;
  value: number | null;
  unit?: string;
  good?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-background p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p
        className={cn(
          "mt-1 font-mono text-lg font-semibold",
          good !== undefined && (good ? "text-emerald-500" : "text-destructive")
        )}
      >
        {value === null || Number.isNaN(value) ? "—" : `${(value * (unit === "%" ? 100 : 1)).toFixed(unit === "%" ? 1 : 4)}${unit === "%" ? "" : unit}`}
      </p>
    </div>
  );
}

function Bar({
  label,
  value,
  max,
}: {
  label: string;
  value: number;
  max: number;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-40 shrink-0 truncate font-mono text-[11px] text-foreground">
        {label}
      </span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${max > 0 ? (value / max) * 100 : 0}%` }}
        />
      </div>
      <span className="w-12 shrink-0 text-right font-mono text-[10px] text-muted-foreground">
        {(value * 100).toFixed(2)}%
      </span>
    </div>
  );
}

export function RfResultsPanel({ result, loading }: RfResultsPanelProps) {
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center py-20 text-sm text-muted-foreground">
        <Loader2Icon className="size-4 animate-spin mr-2" />
        Entraînement du RandomForest...
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex h-full items-center justify-center py-20 text-sm text-muted-foreground">
        Modifiez les paramètres à gauche pour entraîner le modèle et voir les résultats.
      </div>
    );
  }

  const proba = Object.entries(result.prediction?.probabilities ?? {}).sort(
    (a, b) => b[1] - a[1]
  );
  const maxImportance = result.feature_importances[0]?.importance ?? 0;

  return (
    <div className="space-y-4">
      {/* Info entraînement */}
      <div className="rounded-lg border border-border/60 bg-muted/40 px-3 py-2">
        <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
          <span>
            {result.train.n_samples} profils · {result.train.n_features} features ·{" "}
            {result.train.n_classes} classes
          </span>
          <span className="font-mono">
            split {result.train.train_size} / {result.train.test_size} ·{" "}
            {result.train.duree_s}s
          </span>
        </div>
      </div>

      {/* Métriques */}
      <div>
        <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <ActivityIcon className="size-3.5" />
          Métriques sur le jeu de test
        </p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
          <MetricCard label="Accuracy" value={result.metriques.accuracy} />
          <MetricCard label="F1 (macro)" value={result.metriques.f1_macro} />
          <MetricCard label="Précision" value={result.metriques.precision_macro} />
          <MetricCard label="Rappel" value={result.metriques.recall_macro} />
          <MetricCard
            label="Log-loss"
            value={result.metriques.log_loss}
            unit=""
            good={result.metriques.log_loss === null || result.metriques.log_loss < 1.5}
          />
        </div>
      </div>

      {/* Importances */}
      <div>
        <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <BarChart3Icon className="size-3.5" />
          Importances des features (top 25)
        </p>
        <div className="space-y-1.5">
          {result.feature_importances.map((f) => (
            <Bar key={f.feature} label={f.feature} value={f.importance} max={maxImportance} />
          ))}
        </div>
      </div>

      {/* Prédiction */}
      {result.prediction && (
        <div>
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <TargetIcon className="size-3.5" />
            Prédiction pour le profil étudiant
          </p>
          <div className="rounded-lg border border-primary/40 bg-background p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold">
                {result.prediction.parcours.toUpperCase()}
              </span>
              <span className="font-mono text-xs text-muted-foreground">
                confiance {(result.prediction.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div className="space-y-1">
              {proba.map(([parcours, p]) => (
                <Bar key={parcours} label={parcours} value={p} max={1} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
