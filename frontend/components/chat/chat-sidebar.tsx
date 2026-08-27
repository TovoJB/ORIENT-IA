"use client";

import { useEffect, useState } from "react";
import { SearchIcon, UsersIcon, GraduationCapIcon, UserRoundIcon, HistoryIcon, ChevronDownIcon, CheckIcon, EyeIcon, BrainCircuitIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Logo } from "@/components/ui/logo";
import { useChatStore } from "@/store/chat-store";
import { cn } from "@/lib/utils";
import { getInspection, setInspection, type InspectionState } from "@/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const teams = [
  { id: "personal", name: "Personnel", icon: UsersIcon },
  { id: "ispm", name: "ISPM", icon: GraduationCapIcon },
];

const SERIE_LABELS: Record<string, string> = {
  s: "Scientifique (C/D/S)", c: "Scientifique (C)", d: "Scientifique (D)",
  l: "Littéraire (A1/A2/L)", a1: "Littéraire (A1)", a2: "Littéraire (A2)",
  ose: "Économique (OSE)", autre: "Autre",
};

const MOYENNE_LABELS: Record<string, string> = {
  "1": "Moins de 10", "2": "10 à 12", "3": "12 à 14", "4": "14 à 16", "5": "16 à 20",
};

const METIER_LABELS: Record<string, string> = {
  data_scientist: "Data scientist", ingenieur_ml: "Ingénieur ML / IA",
  developpeur: "Développeur", developpeur_web: "Développeur web",
  chef_de_projet: "Chef de projet", commercial_export: "Commercial export",
  charge_affaires: "Chargé d'affaires", analyste_financier: "Analyste financier",
  comptable: "Comptable", juriste: "Juriste", economiste: "Économiste",
  agronome: "Agronome", environnementaliste: "Environnementaliste",
  gestionnaire_tourisme: "Gestionnaire tourisme", directeur_hotel: "Directeur d'hôtel",
  responsable_restauration: "Responsable restauration",
  technicien_superieur: "Technicien supérieur", horticulteur: "Horticulteur",
  ecoguide: "Éco-guide", charge_etudes: "Chargé d'études",
  ingenieur_genie_civil: "Ingénieur génie civil", controleur_qualite: "Contrôleur qualité",
  ingenieur_maintenance: "Ingénieur maintenance", technicien_agroalimentaire: "Technicien agroalimentaire",
};

const ENV_LABELS: Record<string, string> = {
  bureau: "Bureau / informatique", relationnel: "Relationnel / social",
  recherche: "Recherche / laboratoire", terrain: "Terrain", laboratoire: "Laboratoire",
};

const MULTI_LABELS: Record<string, string> = {
  matiere_mathematiques: "Mathématiques", matiere_physique: "Physique / électronique",
  matiere_informatique: "Informatique", matiere_svt: "SVT / biologie",
  matiere_francais: "Français / littérature", matiere_malagasy: "Malagasy",
  matiere_hg: "Histoire-Géo", matiere_ses: "SES / économie", matiere_arts: "Arts / dessin",
  competence_logique: "Logique / analyse", competence_programmation: "Programmation",
  competence_expression: "Expression", competence_manuelle: "Travail manuel",
  competence_relationnelle: "Relationnel", competence_creativite: "Créativité",
  competence_organisation: "Organisation", competence_esprit_critique: "Esprit critique",
  interet_technologie: "Technologie", interet_science: "Science / recherche",
  interet_art: "Art / design", interet_sante: "Santé", interet_entrepreneuriat: "Entrepreneuriat",
  interet_environnement: "Environnement", interet_social: "Social", interet_sport: "Sport",
  prerequis_bases_algo: "Bases en algorithmique", prerequis_anglais: "Niveau d'anglais",
  prerequis_maths_avancees: "Mathématiques avancées",
};

function buildProfileRows(profile: Record<string, string>): { label: string; value: string }[] {
  const rows: { label: string; value: string }[] = [];

  const serie = profile.serie_bac;
  if (serie) {
    const key = serie.toLowerCase();
    rows.push({ label: "Série de bac", value: SERIE_LABELS[key] ?? serie });
  }

  const moyenne = profile.moyenne_generale;
  if (moyenne) rows.push({ label: "Moyenne générale", value: MOYENNE_LABELS[moyenne] ?? moyenne });

  const NOTE_LABELS: Record<string, string> = {
    note_mathematiques: "Note en maths", note_spc: "Note en SPC",
    note_svt: "Note en SVT", note_francais: "Note en français",
    note_malagasy: "Note en malagasy", note_langue_vivante: "Note en LV",
    note_hg: "Note en histoire-géo", note_philosophie: "Note en philosophie",
    note_ses: "Note en SES",
  };
  const notes = Object.entries(profile)
    .filter(([key]) => key.startsWith("note_") && profile[key])
    .map(([key]) => ({ label: NOTE_LABELS[key] ?? key, value: `${profile[key]}/20` }));
  if (notes.length) rows.push({ label: "Notes au bac", value: notes.map((n) => `${n.label}: ${n.value}`).join(" · ") });

  const metier = profile.metier_vise;
  if (metier) {
    const key = metier.toLowerCase().replace(/\s+/g, "_");
    rows.push({ label: "Métier visé", value: METIER_LABELS[key] ?? metier });
  }

  const env = profile.environnement;
  if (env) rows.push({ label: "Environnement", value: ENV_LABELS[env.toLowerCase()] ?? env });

  const categories: Record<string, string> = {
    matiere_: "Matières préférées", competence_: "Compétences",
    interet_: "Centres d'intérêt", prerequis_: "Acquis (suggestions)",
  };
  for (const [prefix, label] of Object.entries(categories)) {
    const values = Object.entries(profile)
      .filter(([key, val]) => key.startsWith(prefix) && val === "1")
      .map(([key]) => MULTI_LABELS[key] ?? key);
    if (values.length) rows.push({ label, value: values.join(", ") });
  }

  return rows;
}

export function ChatSidebar() {
  const [selectedTeam, setSelectedTeam] = useState("personal");
  const currentProfile = useChatStore((s) => s.currentProfile);
  const currentTranscript = useChatStore((s) => s.currentTranscript);
  const [inspection, setInspectionState] = useState<InspectionState | null>(null);

  useEffect(() => {
    getInspection().then(setInspectionState).catch(() => {});
  }, []);

  const toggleInspection = async () => {
    if (!inspection) return;
    const next = await setInspection(!inspection.mode, inspection.force_prolog);
    setInspectionState(next);
  };

  const toggleForceProlog = async () => {
    if (!inspection) return;
    const next = await setInspection(inspection.mode, !inspection.force_prolog);
    setInspectionState(next);
  };

  const profileRows = buildProfileRows(currentProfile);

  return (
    <div className="flex h-full w-full flex-col bg-sidebar border-r border-sidebar-border">
      <div className="flex items-center justify-between p-3 border-b border-sidebar-border">
        <DropdownMenu>
          <DropdownMenuTrigger render={
            <Button variant="ghost" className="w-full justify-start gap-2.5 px-2 h-10">
              <Logo className="size-8" />
              <span className="bg-gradient-to-r from-emerald-400 via-teal-500 to-green-600 bg-clip-text text-transparent">ORIENT&apos;IA</span>
              <ChevronDownIcon className="size-3 ml-auto" />
            </Button>
          } />
          <DropdownMenuContent align="start" className="w-48">
            {teams.map((team) => {
              const TeamIcon = team.icon;
              const isSelected = selectedTeam === team.id;
              return (
                <DropdownMenuItem key={team.id} onClick={() => setSelectedTeam(team.id)} className="gap-2">
                  <TeamIcon className="size-4" />
                  <span className="flex-1">{team.name}</span>
                  {isSelected && <CheckIcon className="size-4" />}
                </DropdownMenuItem>
              );
            })}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="p-3">
        <div className="relative flex items-center">
          <SearchIcon className="absolute left-3 size-4 text-muted-foreground" />
          <Input placeholder="Rechercher" className="pl-9 h-[34px] bg-muted/50" />
        </div>
      </div>

      {/* Mode inspection (temps réel : raisonnement Prolog + probabilités ML) */}
      <div className="px-3 pb-3 space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Mode inspection
        </p>
        <div className="rounded-lg border border-border p-3 space-y-2">
          <button
            type="button"
            onClick={toggleInspection}
            className="w-full flex items-center justify-between gap-2 text-left"
          >
            <span className="flex items-center gap-2 text-xs">
              <EyeIcon className="size-4" />
              Afficher le raisonnement
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-semibold",
                inspection?.mode ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
              )}
            >
              {inspection?.mode ? "ON" : "OFF"}
            </span>
          </button>
          <button
            type="button"
            onClick={toggleForceProlog}
            className="w-full flex items-center justify-between gap-2 text-left"
            title="Désactive rules_fallback : utilise exclusivement SWI-Prolog"
          >
            <span className="flex items-center gap-2 text-xs">
              <BrainCircuitIcon className="size-4" />
              Prolog exclusif
            </span>
            <span
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-semibold",
                inspection?.force_prolog ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
              )}
            >
              {inspection?.force_prolog ? "ON" : "OFF"}
            </span>
          </button>
          {inspection && !inspection.swipl_disponible && (
            <p className="text-[10px] text-muted-foreground leading-tight">
              SWI-Prolog non détecté : « Prolog exclusif » renverra une erreur explicite
              (rules_fallback désactivée).
            </p>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar space-y-4 p-3">
        {/* Profil de l'étudiant (temps réel) */}
        <div className="rounded-lg border border-border p-3 space-y-2">
          <div className="flex items-center gap-2">
            <UserRoundIcon className="size-4 text-muted-foreground" />
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Profil de l&apos;étudiant
            </p>
          </div>
          {profileRows.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              Aucune information collectée pour l&apos;instant.
            </p>
          ) : (
            <dl className="space-y-1.5">
              {profileRows.map((row) => (
                <div key={row.label} className="text-xs">
                  <dt className="text-muted-foreground">{row.label}</dt>
                  <dd className="font-medium">{row.value}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>

        {/* Historique de la discussion en cours */}
        <div className="rounded-lg border border-border p-3 space-y-2">
          <div className="flex items-center gap-2">
            <HistoryIcon className="size-4 text-muted-foreground" />
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Historique
            </p>
          </div>
          {currentTranscript.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              La discussion apparaîtra ici.
            </p>
          ) : (
            <div className="space-y-1.5">
              {currentTranscript.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "rounded-md px-2 py-1.5 text-xs leading-relaxed",
                    message.sender === "user"
                      ? "bg-primary/10 text-primary-foreground/80"
                      : "bg-muted/60"
                  )}
                >
                  <span className="font-semibold">
                    {message.sender === "user" ? "Vous" : "ORIENT'IA"} :{" "}
                  </span>
                  <span className="text-muted-foreground">{message.content.slice(0, 80)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="p-4 border-t border-sidebar-border">
        <p className="text-xs text-muted-foreground leading-tight">
          Aide à la décision, pas une décision officielle d&apos;admission.
        </p>
      </div>
    </div>
  );
}
