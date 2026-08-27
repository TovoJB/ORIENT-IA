"use client";

import { GraduationCapIcon, StarIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface NotesState {
  note_mathematiques: number | null;
  note_spc: number | null;
  note_svt: number | null;
  note_francais: number | null;
  note_malagasy: number | null;
  note_langue_vivante: number | null;
  note_hg: number | null;
  note_philosophie: number | null;
  note_ses: number | null;
}

export const NOTE_FIELDS: { col: keyof NotesState; label: string }[] = [
  { col: "note_mathematiques", label: "Mathématiques" },
  { col: "note_spc", label: "Physique-Chimie (SPC)" },
  { col: "note_svt", label: "SVT / Biologie" },
  { col: "note_francais", label: "Français" },
  { col: "note_malagasy", label: "Malagasy" },
  { col: "note_langue_vivante", label: "Langue vivante" },
  { col: "note_hg", label: "Histoire-Géo" },
  { col: "note_philosophie", label: "Philosophie" },
  { col: "note_ses", label: "SES / Économie" },
];

// Les 3 matières de base par série de bac (notes /20 prises en compte en priorité)
const CORE_NOTES_PAR_SERIE: Record<string, (keyof NotesState)[]> = {
  c: ["note_mathematiques", "note_spc", "note_svt"],
  d: ["note_mathematiques", "note_spc", "note_svt"],
  s: ["note_mathematiques", "note_spc", "note_svt"],
  a1: ["note_malagasy", "note_francais", "note_philosophie"],
  a2: ["note_malagasy", "note_francais", "note_philosophie"],
  l: ["note_malagasy", "note_francais", "note_philosophie"],
  ose: ["note_ses", "note_mathematiques", "note_hg"],
};

const SERIE_LABELS: Record<string, string> = {
  c: "Scientifique C",
  d: "Scientifique D",
  s: "Scientifique S",
  a1: "Littéraire A1",
  a2: "Littéraire A2",
  l: "Littéraire L",
  ose: "Économique OSE",
};

export function coreNotesForSerie(serie: string): (keyof NotesState)[] {
  return CORE_NOTES_PAR_SERIE[serie.toLowerCase()] ?? [];
}

export function serieLabelFor(serie: string): string | null {
  return SERIE_LABELS[serie.toLowerCase()] ?? null;
}

export function emptyNotes(): NotesState {
  return {
    note_mathematiques: null,
    note_spc: null,
    note_svt: null,
    note_francais: null,
    note_malagasy: null,
    note_langue_vivante: null,
    note_hg: null,
    note_philosophie: null,
    note_ses: null,
  };
}

export function notesToProfile(notes: NotesState): Record<string, string> {
  const profil: Record<string, string> = {};
  for (const field of NOTE_FIELDS) {
    const value = notes[field.col];
    if (value !== null) profil[field.col] = String(value);
  }
  return profil;
}

interface NotesSliderProps {
  notes: NotesState;
  onChange: (notes: NotesState) => void;
  coreColumns?: (keyof NotesState)[];
  serieLabel?: string | null;
}

export function NotesSlider({
  notes,
  onChange,
  coreColumns = [],
  serieLabel = null,
}: NotesSliderProps) {
  const setNote = (col: keyof NotesState, value: number | null) => {
    onChange({ ...notes, [col]: value });
  };

  const coreSet = new Set(coreColumns);
  const orderedFields = [
    ...NOTE_FIELDS.filter((f) => coreSet.has(f.col)),
    ...NOTE_FIELDS.filter((f) => !coreSet.has(f.col)),
  ];

  return (
    <div className="space-y-3">
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        <GraduationCapIcon className="size-3.5" />
        Notes au bac — barre /20
      </p>
      {coreColumns.length > 0 && serieLabel && (
        <p className="rounded-lg bg-primary/10 px-2 py-1.5 text-[11px] leading-snug">
          Série <span className="font-semibold">{serieLabel}</span> : les{" "}
          <span className="font-semibold">3 matières de base</span> sont
          renseignées en priorité et prises en compte par le modèle.
        </p>
      )}
      <p className="text-[11px] text-muted-foreground">
        Cochez une note pour la renseigner, puis glissez la barre. Une note non
        cochée reste « non renseignée » (NaN, gérée par le modèle).
      </p>

      <div className="space-y-2.5">
        {orderedFields.map(({ col, label }) => {
          const active = notes[col] !== null;
          const value = notes[col] ?? 0;
          const isCore = coreSet.has(col);
          return (
            <div
              key={col}
              className={cn(
                "rounded-lg border p-2 transition-opacity",
                isCore
                  ? "border-primary/50 bg-primary/5"
                  : "border-border/60 bg-background",
                !active && "opacity-60"
              )}
            >
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  role="checkbox"
                  aria-checked={active}
                  onClick={() => setNote(col, active ? null : 10)}
                  className={cn(
                    "relative h-4 w-7 shrink-0 rounded-full transition-colors",
                    active ? "bg-primary" : "bg-muted"
                  )}
                  title={active ? "Retirer la note" : "Renseigner la note"}
                >
                  <span
                    className={cn(
                      "absolute top-0.5 size-3 rounded-full bg-white shadow transition-all",
                      active ? "left-3.5" : "left-0.5"
                    )}
                  />
                </button>
                <span className="flex-1 text-xs font-medium">{label}</span>
                {isCore && (
                  <span className="flex items-center gap-1 rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                    <StarIcon className="size-2.5" />
                    base série
                  </span>
                )}
                <span className="w-16 rounded-md border border-input px-1.5 py-0.5 text-center font-mono text-xs">
                  {active ? `${value}/20` : "—"}
                </span>
              </div>

              <input
                type="range"
                min={0}
                max={20}
                step={0.5}
                value={value}
                disabled={!active}
                onChange={(e) => setNote(col, Number(e.target.value))}
                className="mt-2 h-2 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary disabled:cursor-not-allowed"
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
