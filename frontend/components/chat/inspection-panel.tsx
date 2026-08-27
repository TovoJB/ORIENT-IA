import { useState } from "react";
import { ChevronDownIcon, ChevronRightIcon, EyeIcon } from "lucide-react";
import type { InspectionData } from "@/lib/api";

interface InspectionPanelProps {
  data: InspectionData;
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="rounded-lg border border-border bg-muted/40 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-1.5 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:bg-muted/60"
      >
        {open ? <ChevronDownIcon className="size-3.5" /> : <ChevronRightIcon className="size-3.5" />}
        {title}
      </button>
      {open && <div className="px-3 py-2 space-y-2 text-xs">{children}</div>}
    </div>
  );
}

function KVs({ rows }: { rows: { label: string; value: string }[] }) {
  return (
    <dl className="space-y-1">
      {rows.map((r) => (
        <div key={r.label} className="flex justify-between gap-2">
          <dt className="text-muted-foreground">{r.label}</dt>
          <dd className="font-mono text-right">{r.value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function InspectionPanel({ data }: InspectionPanelProps) {
  const proba = Object.entries(data.ml.probabilites).sort((a, b) => b[1] - a[1]);

  return (
    <div className="rounded-2xl border border-primary/40 bg-card p-3 space-y-3">
      <div className="flex items-center gap-2">
        <EyeIcon className="size-4 text-primary" />
        <p className="text-sm font-semibold">Inspection — raisonnement du système</p>
      </div>

      <KVs
        rows={[
          { label: "Moteur de règles", value: data.moteur },
          { label: "Prolog exclusif", value: data.force_prolog ? "ON" : "OFF" },
        ]}
      />

      {data.erreur_prolog && (
        <p className="rounded bg-destructive/10 text-destructive px-2 py-1.5">
          {data.erreur_prolog}
        </p>
      )}

      <Section title="1. Filtrage Prolog (parcours éligibles)">
        <p className="font-mono">{data.filtrage.possibles.join(", ") || "(aucun)"}</p>
        {data.filtrage.bloques.length > 0 && (
          <div className="space-y-1">
            {data.filtrage.bloques.map((b) => (
              <p key={b.parcours} className="text-muted-foreground">
                <span className="font-mono text-foreground">{b.parcours}</span> — {b.raisons.join(" ; ")}
              </p>
            ))}
          </div>
        )}
      </Section>

      <Section title="2. Règles — score de compatibilité">
        <div className="space-y-1">
          {data.regles.map((r) => (
            <div key={r.parcours} className="flex items-start justify-between gap-2">
              <div>
                <p className="font-mono">{r.parcours}</p>
                <p className="text-muted-foreground">
                  {[
                    r.motifs.matieres.length && `matières: ${r.motifs.matieres.join(", ")}`,
                    r.motifs.competences.length && `compétences: ${r.motifs.competences.join(", ")}`,
                    r.motifs.interets.length && `intérêts: ${r.motifs.interets.join(", ")}`,
                    r.motifs.metier_alignee && "métier visé préparé",
                  ]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </div>
              <span className="font-mono font-semibold">{r.score}</span>
            </div>
          ))}
        </div>
      </Section>

      <Section title="3. Modèle ML (RandomForest) — probabilités">
        <p className="text-muted-foreground">
          Modèle : {data.ml.modele ?? "non entraîné"} · confiance : {data.ml.confiance ?? "-"}
        </p>
        {proba.map(([parcours, p]) => (
          <div key={parcours} className="flex items-center gap-2">
            <span className="font-mono w-16">{parcours}</span>
            <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-primary" style={{ width: `${Math.round(p * 100)}%` }} />
            </div>
            <span className="font-mono w-12 text-right">{(p * 100).toFixed(1)}%</span>
          </div>
        ))}
      </Section>

      <Section title="4. Décision (ML vs Prolog)">
        <p className="text-muted-foreground mb-1.5">{data.methodologie}</p>
        <div className="space-y-1">
          {data.fusion.map((f) => (
            <div key={f.parcours} className="flex justify-between gap-2 font-mono">
              <span>{f.parcours}</span>
              <span className="text-muted-foreground text-[10px]">
                ML: {f.proba_ml !== null ? `${(f.proba_ml * 100).toFixed(1)}%` : "-"} · Prolog: {f.score_regles_norm !== undefined ? Math.round(f.score_regles_norm * 10) : 0} = <span className="text-foreground font-semibold">Rang {4 - f.score_fusion}</span>
              </span>
            </div>
          ))}
        </div>
      </Section>

      {data.requetes_prolog.length > 0 && (
        <Section title="5. Requêtes Prolog exécutées">
          <div className="space-y-1.5">
            {data.requetes_prolog.map((q, i) => (
              <div key={i}>
                <p className="font-mono text-foreground">?- {q.requete}</p>
                {q.resultats.map((r, j) => (
                  <p key={j} className="font-mono text-muted-foreground pl-3">
                    {Object.entries(r).map(([k, v]) => `${k} = ${v}`).join(", ")}
                  </p>
                ))}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}
