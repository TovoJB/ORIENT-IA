"use client";

import { GraduationCapIcon } from "lucide-react";
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
}

export function NotesSlider({ notes, onChange }: NotesSliderProps) {
  const setNote = (col: keyof NotesState, value: number | null) => {
    onChange({ ...notes, [col]: value });
  };

  return (
    <div className="space-y-3">
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        <GraduationCapIcon className="size-3.5" />
        Notes au bac — barre /20
      </p>
      <p className="text-[11px] text-muted-foreground">
        Cochez une note pour la renseigner, puis glissez la barre. Une note non
        cochée reste « non renseignée » (NaN, gérée par le modèle).
      </p>

      <div className="space-y-2.5">
        {NOTE_FIELDS.map(({ col, label }) => {
          const active = notes[col] !== null;
          const value = notes[col] ?? 0;
          return (
            <div
              key={col}
              className={cn(
                "rounded-lg border border-border/60 bg-background p-2 transition-opacity",
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
