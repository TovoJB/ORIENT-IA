"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChevronDownIcon,
  ChevronRightIcon,
  RefreshCcwIcon,
  UserRoundIcon,
  BoxesIcon,
  Loader2Icon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { exploreRandomForest, type RfExploreResult } from "@/lib/api";
import { PrologForm } from "@/components/prolog/prolog-form";
import {
  buildProfileFromForm,
  emptyForm,
  type ProfileForm,
} from "@/components/prolog/profile-form";
import { RfResultsPanel } from "./rf-results-panel";
import {
  coreNotesForSerie,
  emptyNotes,
  NotesSlider,
  notesToProfile,
  serieLabelFor,
  type NotesState,
} from "./notes-slider";

export function RfExplorer() {
  const [form, setForm] = useState<ProfileForm>(emptyForm());
  const [notes, setNotes] = useState<NotesState>(emptyNotes());
  const [profilOpen, setProfilOpen] = useState(true);
  const [result, setResult] = useState<RfExploreResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Renseigne automatiquement les 3 matières de base dès qu'une série est choisie
  const serie = String(form.serie_bac ?? "").toLowerCase();
  const coreColumns = coreNotesForSerie(serie);
  const serieLabel = serieLabelFor(serie);
  const lastSerieRef = useRef<string | null>(null);
  useEffect(() => {
    if (!serie || serie === lastSerieRef.current) return;
    lastSerieRef.current = serie;
    const core = coreNotesForSerie(serie);
    setNotes((prev) => {
      const next = { ...prev };
      let changed = false;
      for (const col of core) {
        if (next[col] === null) {
          next[col] = 10;
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, [serie]);

  const evaluate = useCallback(async (profil: Record<string, string>) => {
    setLoading(true);
    setError(null);
    try {
      const res = await exploreRandomForest(profil);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const profil = { ...buildProfileFromForm(form), ...notesToProfile(notes) };
    const handler = setTimeout(() => {
      evaluate(profil);
    }, 450);
    return () => clearTimeout(handler);
  }, [form, notes, evaluate]);

  const currentProfile = { ...buildProfileFromForm(form), ...notesToProfile(notes) };

  return (
    <div className="flex h-full flex-col gap-4 p-4 lg:p-6 lg:flex-row">
      {/* Panneau de gauche : modèle chargé + profil étudiant */}
      <div className="lg:w-[400px] lg:shrink-0 space-y-3">
        {/* Modèle chargé */}
        <div className="rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <BoxesIcon className="size-4 text-primary" />
            Modèle chargé
          </div>
          {!result && !loading && (
            <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2Icon className="size-3.5 animate-spin" />
              Chargement du modèle sauvegardé...
            </p>
          )}
          {result && (
            <dl className="mt-2 space-y-1 text-xs">
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Modèle</dt>
                <dd className="font-mono font-semibold uppercase">
                  {result.modele.nom ?? "—"}
                </dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Accuracy (test)</dt>
                <dd className="font-mono">
                  {result.modele.accuracy_test !== null
                    ? `${(result.modele.accuracy_test * 100).toFixed(1)}%`
                    : "—"}
                </dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Entraîné le</dt>
                <dd className="font-mono">{result.modele.trained_at ?? "—"}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-muted-foreground">Dataset</dt>
                <dd className="font-mono">{result.modele.dataset_path ?? "—"}</dd>
              </div>
            </dl>
          )}
        </div>

        {/* Profil étudiant */}
        <div className="rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setProfilOpen((v) => !v)}
              className="flex items-center gap-2 text-left"
            >
              {profilOpen ? (
                <ChevronDownIcon className="size-4 text-muted-foreground" />
              ) : (
                <ChevronRightIcon className="size-4 text-muted-foreground" />
              )}
              <UserRoundIcon className="size-4 text-muted-foreground" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Profil étudiant (prédiction)
              </span>
            </button>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => {
                setForm(emptyForm());
                setNotes(emptyNotes());
                lastSerieRef.current = null;
              }}
              title="Réinitialiser le profil"
            >
              <RefreshCcwIcon className="size-4" />
            </Button>
          </div>

          {profilOpen && (
            <div className="mt-3 space-y-5 overflow-y-auto lg:max-h-[calc(100vh-330px)] pr-1.5 no-scrollbar">
              <NotesSlider
                notes={notes}
                onChange={setNotes}
                coreColumns={coreColumns}
                serieLabel={serieLabel}
              />
              <div className="border-t border-border/60 pt-4">
                <PrologForm
                  form={form}
                  onChange={setForm}
                  excludeChamps={["note_mathematiques"]}
                />
              </div>
            </div>
          )}
        </div>

        <p className="text-[11px] text-muted-foreground">
          L&apos;interface utilise le modèle entraîné sauvegardé
          (backend/model/ml_model.joblib). La prédiction se met à jour à chaque
          modification du profil.
        </p>
      </div>

      {/* Panneau de droite : résultats */}
      <div className="flex-1 min-w-0 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <span className="relative flex size-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-60" />
              <span className="relative inline-flex size-2 rounded-full bg-primary" />
            </span>
            Résultats (temps réel)
          </div>
          <span className="hidden md:block max-w-[40%] truncate font-mono text-[10px] text-muted-foreground">
            {Object.keys(currentProfile).length > 0
              ? JSON.stringify(currentProfile)
              : "profil vide"}
          </span>
        </div>

        {error && (
          <p className={cn("rounded-lg px-3 py-2 text-xs", "bg-destructive/10 text-destructive")}>
            {error}
          </p>
        )}

        <div className="overflow-y-auto rounded-2xl border border-border bg-card p-4 lg:max-h-[calc(100vh-140px)]">
          <RfResultsPanel result={result} loading={loading} />
        </div>
      </div>
    </div>
  );
}
