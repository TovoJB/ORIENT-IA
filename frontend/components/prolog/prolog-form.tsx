"use client";

import { CheckIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { FORM_FIELDS, type ProfileForm } from "./profile-form";

interface PrologFormProps {
  form: ProfileForm;
  onChange: (form: ProfileForm) => void;
  excludeChamps?: string[];
}

export function PrologForm({ form, onChange, excludeChamps = [] }: PrologFormProps) {
  const setValue = (champ: string, value: string | string[]) => {
    onChange({ ...form, [champ]: value });
  };

  return (
    <div className="space-y-5">
      {FORM_FIELDS.filter((field) => !excludeChamps.includes(field.champ)).map((field) => {
        const current = form[field.champ] ?? (field.multiple ? [] : "");

        if (!field.multiple) {
          return (
            <div key={field.champ} className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {field.label}
              </label>
              <select
                value={String(current)}
                onChange={(e) => setValue(field.champ, e.target.value)}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-all focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="">— Choisir —</option>
                {field.options.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          );
        }

        const selected = (current as string[]) ?? [];
        const toggle = (value: string) => {
          setValue(
            field.champ,
            selected.includes(value)
              ? selected.filter((v) => v !== value)
              : [...selected, value]
          );
        };

        return (
          <div key={field.champ} className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {field.label}
            </label>
            <div className="flex flex-wrap gap-1.5">
              {field.options.map((option) => {
                const isSelected = selected.includes(option.value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => toggle(option.value)}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs transition-all",
                      isSelected
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-input bg-transparent hover:bg-accent"
                    )}
                  >
                    {isSelected && <CheckIcon className="size-3" />}
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
