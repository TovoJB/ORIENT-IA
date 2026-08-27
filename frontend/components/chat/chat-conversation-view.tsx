import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { XIcon, Loader2Icon, CheckIcon, AwardIcon, CpuIcon, BookOpenIcon, AlertTriangleIcon, EyeIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatMessage } from "./chat-message";
import { InspectionPanel } from "./inspection-panel";
import type { Question, RecommendationResult, RecommendationItem } from "@/lib/api";

const PARCOURS_NAMES: Record<string, string> = {
  esii: "ESIIA — Électronique & Télécoms",
  isaia: "ISAIA — Informatique & Statistique",
  imticia: "IMTICIA — Multimédia & TIC",
  iggia: "IGGLIA — Gestion & Informatique",
  caa: "CAA — Commerce & Affaires",
  fic: "FIC — Finance & Comptabilité",
  dtja: "DTJA — Droit & Juridique",
  emp: "EMP — Économie & Management Public",
  iaa: "IAA — Industries Agroalimentaires",
  pip: "PIP — Productions & Études Florales",
  aee: "AEE — Agriculture & Environnement",
  emii: "EMII — Électromécanique & Industrialisation",
  gca: "GCA — Génie Civil & Architecture",
  icmp: "ICMP — Chimie & Sciences des Matériaux",
  tee: "TEE — Tourisme & Environnement",
  teh: "TEH — Tourisme & Hôtellerie",
};

const CATEGORY_STYLES: Record<string, { label: string; bg: string; text: string }> = {
  informatique: { label: "Informatique & Télécoms", bg: "bg-blue-500/10 dark:bg-blue-400/10 border-blue-500/20", text: "text-blue-600 dark:text-blue-400" },
  affaires: { label: "Techniques des Affaires", bg: "bg-emerald-500/10 dark:bg-emerald-400/10 border-emerald-500/20", text: "text-emerald-600 dark:text-emerald-400" },
  biotech: { label: "Biotech & Agronomie", bg: "bg-green-500/10 dark:bg-green-400/10 border-green-500/20", text: "text-green-600 dark:text-green-400" },
  genie: { label: "Génie Industriel & Civil", bg: "bg-orange-500/10 dark:bg-orange-400/10 border-orange-500/20", text: "text-orange-600 dark:text-orange-400" },
  tourisme: { label: "Tourisme & Hôtellerie", bg: "bg-purple-500/10 dark:bg-purple-400/10 border-purple-500/20", text: "text-purple-600 dark:text-purple-400" },
};

const MULTI_LABELS: Record<string, string> = {
  mathematiques: "Mathématiques",
  physique: "Physique",
  electronique: "Électronique",
  programmation: "Programmation",
  algorithmique: "Algorithmique",
  statistiques: "Statistiques",
  multimedia: "Multimédia",
  gestion: "Gestion",
  commerce: "Commerce",
  langues: "Langues",
  economie_internationale: "Économie internationale",
  finance: "Finance",
  comptabilite: "Comptabilité",
  economie: "Économie",
  droit_public: "Droit public",
  droit_prive: "Droit privé",
  micro_economie: "Micro-économie",
  macro_economie: "Macro-économie",
  agroalimentaire: "Agroalimentaire",
  biologie: "Biologie",
  chimie: "Chimie",
  etudes_flore: "Études florales",
  agriculture: "Agriculture",
  etudes_faune: "Études fauniques",
  agriculture_biologique: "Agriculture biologique",
  environnement: "Environnement",
  dessin: "Dessin",
  sciences: "Sciences",
  tourisme: "Tourisme",
  ecologie: "Écologie",
  hotelierie: "Hôtellerie",
  art_culinaire: "Art culinaire",
  competence_logique: "Logique / analyse",
  competence_programmation: "Programmation",
  competence_expression: "Expression",
  competence_manuelle: "Travail manuel",
  competence_relationnelle: "Relationnel",
  competence_creativite: "Créativité",
  competence_organisation: "Organisation",
  competence_esprit_critique: "Esprit critique",
  interet_technologie: "Technologie",
  interet_science: "Science / recherche",
  interet_art: "Art / design",
  interet_sante: "Santé",
  interet_entrepreneuriat: "Entrepreneuriat",
  interet_environnement: "Environnement",
  interet_social: "Social",
  interet_sport: "Sport",
  matiere_mathematiques: "Mathématiques",
  matiere_physique: "Physique / électronique",
  matiere_informatique: "Informatique",
  matiere_svt: "SVT / biologie",
  matiere_francais: "Français / littérature",
  matiere_malagasy: "Malagasy",
  matiere_hg: "Histoire-Géo",
  matiere_ses: "SES / économie",
  matiere_arts: "Arts / dessin",
};

function getLabel(key: string): string {
  const cleanKey = key.toLowerCase().trim();
  if (MULTI_LABELS[cleanKey]) return MULTI_LABELS[cleanKey];
  const stripped = cleanKey.replace(/^(matiere_|competence_|interet_|prerequis_)/, "");
  if (MULTI_LABELS[stripped]) return MULTI_LABELS[stripped];
  return key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, " ");
}

interface Message {
  id: string;
  content: string;
  sender: "user" | "ai";
  timestamp: Date;
}

interface ChatConversationViewProps {
  messages: Message[];
  message: string;
  isLoading: boolean;
  pendingQuestion: Question | null;
  selection: string[];
  recommendation: RecommendationResult | null;
  inputDisabled: boolean;
  onMessageChange: (value: string) => void;
  onSend: (content: string) => void;
  onReset: () => void;
  onSelectOption: (value: string) => void;
  onSingleSelect: (value: string) => void;
  onValidateAnswer: () => void;
}

export function ChatConversationView({
  messages,
  message,
  isLoading,
  pendingQuestion,
  selection,
  recommendation,
  inputDisabled,
  onMessageChange,
  onSend,
  onReset,
  onSelectOption,
  onSingleSelect,
  onValidateAnswer,
}: ChatConversationViewProps) {
  const [selectedDetail, setSelectedDetail] = useState<RecommendationItem | null>(null);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-8">
        <div className="max-w-[640px] mx-auto space-y-6">
          <div className="flex justify-end mb-2">
            <Button
              variant="secondary"
              size="icon-sm"
              onClick={onReset}
              className="size-8 rounded-full border"
            >
              <XIcon className="size-4" />
            </Button>
          </div>
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="flex gap-4 justify-start">
              <div className="rounded-2xl px-4 py-3 max-w-[80%] bg-secondary flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2Icon className="size-4 animate-spin" />
                Chargement...
              </div>
            </div>
          )}

          {recommendation && (
            <div className="rounded-2xl border border-border bg-card p-5 space-y-5 shadow-sm">
              <div className="flex items-center gap-2.5 pb-3 border-b border-border">
                <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                  <AwardIcon className="size-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Recommandations d&apos;Orientation</h3>
                  <p className="text-[10px] text-muted-foreground">
                    Classement généré selon vos préférences académiques et professionnelles.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {recommendation.classement.map((item, index) => {
                  const catStyle = CATEGORY_STYLES[item.categorie.toLowerCase()] || {
                    label: item.categorie,
                    bg: "bg-muted text-muted-foreground border-transparent",
                  };
                  return (
                    <div key={item.parcours} className="rounded-xl border border-border/80 bg-muted/20 hover:bg-muted/40 transition-colors p-4 space-y-3">
                      <div className="flex flex-wrap items-start justify-between gap-2 border-b border-border/40 pb-2">
                        <div className="space-y-0.5">
                          <span className="text-[9px] font-bold text-primary uppercase tracking-wider">
                            Recommandation #{index + 1}
                          </span>
                          <h4 className="text-xs sm:text-sm font-bold text-foreground flex items-center gap-1.5">
                            {PARCOURS_NAMES[item.parcours.toLowerCase()] ?? item.parcours.toUpperCase()}
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              className="size-5 rounded p-0 text-muted-foreground hover:text-foreground hover:bg-muted inline-flex items-center justify-center shrink-0"
                              onClick={() => setSelectedDetail(item)}
                              title="Voir les détails complets"
                            >
                              <EyeIcon className="size-3.5" />
                            </Button>
                          </h4>
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className={cn("text-[9px] font-semibold px-2 py-0.5 rounded-full border", catStyle.bg, catStyle.text)}>
                            {catStyle.label}
                          </span>
                          {item.proba_ml !== null && (
                            <span className="text-[9px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20">
                              ML: {(item.proba_ml * 100).toFixed(1)}%
                            </span>
                          )}
                          <span className="text-[9px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 px-2 py-0.5 rounded-full border border-purple-500/20">
                            Prolog: {item.score_regles} pts
                          </span>
                        </div>
                      </div>

                      {item.description && (
                        <p className="text-xs text-muted-foreground leading-relaxed font-normal">
                          {item.description.slice(0, 240)}...
                        </p>
                      )}

                      {/* Motifs de correspondance */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 pt-2 text-[10px] border-t border-border/30">
                        {item.motifs.matieres && item.motifs.matieres.length > 0 && (
                          <div className="flex items-start gap-1">
                            <span className="text-muted-foreground font-semibold shrink-0">📚 Matières :</span>
                            <span className="text-foreground truncate">{item.motifs.matieres.map(getLabel).join(", ")}</span>
                          </div>
                        )}
                        {item.motifs.competences && item.motifs.competences.length > 0 && (
                          <div className="flex items-start gap-1">
                            <span className="text-muted-foreground font-semibold shrink-0">⚡ Compétences :</span>
                            <span className="text-foreground truncate">{item.motifs.competences.map(getLabel).join(", ")}</span>
                          </div>
                        )}
                        {item.motifs.interets && item.motifs.interets.length > 0 && (
                          <div className="flex items-start gap-1">
                            <span className="text-muted-foreground font-semibold shrink-0">🎯 Intérêts :</span>
                            <span className="text-foreground truncate">{item.motifs.interets.map(getLabel).join(", ")}</span>
                          </div>
                        )}
                        {item.motifs.metier_alignee && (
                          <div className="flex items-start gap-1 sm:col-span-2">
                            <span className="text-emerald-600 dark:text-emerald-400 font-semibold shrink-0">💼 Métier :</span>
                            <span className="text-foreground">Ce parcours prépare directement au métier ciblé.</span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-border/60">
                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground bg-muted/60 px-2.5 py-1 rounded-lg border border-border/60">
                  <CpuIcon className="size-3.5 text-primary" />
                  <span>
                    {recommendation.ml_utilise
                      ? `Modèle ML : ${recommendation.ml.modele} (confiance: ${(recommendation.ml.confiance ?? 0).toFixed(3)})`
                      : "Modèle ML indisponible (recommandation par règles uniquement)"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground bg-muted/60 px-2.5 py-1 rounded-lg border border-border/60">
                  <BookOpenIcon className="size-3.5 text-primary" />
                  <span>
                    {recommendation.moteur_regles === "swipl"
                      ? "Moteur de règles : SWI-Prolog"
                      : "Moteur de règles : Python Fallback"}
                  </span>
                </div>
              </div>

              <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 dark:bg-yellow-500/10 p-3.5 flex items-start gap-3">
                <AlertTriangleIcon className="size-4 text-yellow-600 dark:text-yellow-400 mt-0.5 shrink-0 animate-bounce" style={{ animationDuration: "3s" }} />
                <div className="space-y-0.5">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-yellow-700 dark:text-yellow-400">
                    Avertissement de la commission pédagogique
                  </p>
                  <p className="text-[10px] leading-relaxed text-yellow-800/80 dark:text-yellow-300/80">
                    Cette recommandation est générée automatiquement à des fins d&apos;aide à la décision. Elle ne constitue en aucun cas une décision officielle d&apos;admission ou d&apos;éligibilité définitive à l&apos;ISPM.
                  </p>
                </div>
              </div>

              {recommendation.inspection && (
                <InspectionPanel data={recommendation.inspection} />
              )}
            </div>
          )}

          {pendingQuestion && (
            <div className="rounded-2xl border border-border bg-card p-4 space-y-3">
              <p className="text-sm font-medium">{pendingQuestion.question}</p>
              <div className="flex flex-wrap gap-2">
                {pendingQuestion.options.map((option) => {
                  const selected = selection.includes(option.value);
                  return (
                    <Button
                      key={option.value}
                      variant={selected ? "secondary" : "outline"}
                      className={cn("gap-2", selected && "border-primary")}
                      onClick={() =>
                        pendingQuestion.multiple
                          ? onSelectOption(option.value)
                          : onSingleSelect(option.value)
                      }
                    >
                      {selected && <CheckIcon className="size-4" />}
                      {option.label}
                    </Button>
                  );
                })}
              </div>
              {pendingQuestion.multiple && (
                <Button
                  size="sm"
                  disabled={selection.length === 0 || isLoading}
                  onClick={() => onValidateAnswer()}
                  className="h-7 px-4"
                >
                  Valider
                </Button>
              )}
            </div>
          )}
        </div>
      </div>

      {!pendingQuestion && (
        <div className="border-t border-border px-4 md:px-8 py-[17px]">
          <div className="max-w-[640px] mx-auto">
            <div className="rounded-2xl border border-border bg-secondary dark:bg-card p-1">
              <div className="rounded-xl border border-border dark:border-transparent bg-card dark:bg-secondary">
                <Textarea
                  placeholder={
                    inputDisabled ? "Répondez aux questions ci-dessus..." : "Posez votre question libre..."
                  }
                  value={message}
                  disabled={inputDisabled}
                  onChange={(e) => onMessageChange(e.target.value)}
                  className="min-h-[80px] resize-none border-0 bg-transparent px-4 py-3 text-base placeholder:text-muted-foreground/60 focus-visible:ring-0 focus-visible:ring-offset-0 disabled:opacity-60"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      if (message.trim() && !inputDisabled) {
                        onSend(message);
                      }
                    }
                  }}
                />

                <div className="flex items-center justify-end px-4 py-3 border-t border-border/50">
                  <Button
                    size="sm"
                    disabled={inputDisabled || !message.trim()}
                    onClick={() => {
                      if (message.trim()) {
                        onSend(message);
                      }
                    }}
                    className="h-7 px-4"
                  >
                    Envoyer
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedDetail && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl max-w-xl w-full max-h-[85vh] overflow-y-auto shadow-2xl p-6 relative flex flex-col space-y-4 animate-in fade-in zoom-in duration-200">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setSelectedDetail(null)}
              className="absolute top-4 right-4 size-8 rounded-full border"
            >
              <XIcon className="size-4" />
            </Button>
            
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-primary uppercase tracking-wider">
                Détails du parcours
              </span>
              <h3 className="text-lg font-bold text-foreground">
                {PARCOURS_NAMES[selectedDetail.parcours.toLowerCase()] ?? selectedDetail.parcours.toUpperCase()}
              </h3>
              <div className="flex flex-wrap gap-2 mt-1">
                <span className={cn("text-[10px] font-semibold px-2 py-0.5 rounded-full border", 
                  (CATEGORY_STYLES[selectedDetail.categorie.toLowerCase()] || { bg: "bg-muted text-muted-foreground border-transparent" }).bg,
                  (CATEGORY_STYLES[selectedDetail.categorie.toLowerCase()] || { text: "" }).text
                )}>
                  {(CATEGORY_STYLES[selectedDetail.categorie.toLowerCase()] || { label: selectedDetail.categorie }).label}
                </span>
                {selectedDetail.proba_ml !== null && (
                  <span className="text-[10px] font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20">
                    ML: {(selectedDetail.proba_ml * 100).toFixed(1)}%
                  </span>
                )}
                <span className="text-[10px] font-semibold bg-purple-500/10 text-purple-600 dark:text-purple-400 px-2 py-0.5 rounded-full border border-purple-500/20">
                  Prolog: {selectedDetail.score_regles} pts
                </span>
              </div>
            </div>

            <div className="border-t border-border/60 my-2" />

            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Description complète</h4>
              <p className="text-sm text-foreground leading-relaxed font-normal whitespace-pre-line">
                {selectedDetail.description}
              </p>
            </div>

            <div className="border-t border-border/60 my-2" />

            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Arguments de correspondance (Prolog)</h4>
              
              <div className="space-y-2.5 text-xs">
                {selectedDetail.motifs.matieres && selectedDetail.motifs.matieres.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-muted-foreground font-semibold">📚 Matières préférées correspondantes :</span>
                    <div className="flex flex-wrap gap-1.5 mt-0.5">
                      {selectedDetail.motifs.matieres.map(getLabel).map((lbl) => (
                        <span key={lbl} className="bg-secondary px-2 py-0.5 rounded text-foreground font-medium border">
                          {lbl}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedDetail.motifs.competences && selectedDetail.motifs.competences.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-muted-foreground font-semibold">⚡ Compétences validées :</span>
                    <div className="flex flex-wrap gap-1.5 mt-0.5">
                      {selectedDetail.motifs.competences.map(getLabel).map((lbl) => (
                        <span key={lbl} className="bg-secondary px-2 py-0.5 rounded text-foreground font-medium border">
                          {lbl}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedDetail.motifs.interets && selectedDetail.motifs.interets.length > 0 && (
                  <div className="space-y-1">
                    <span className="text-muted-foreground font-semibold">🎯 Centres d&apos;intérêt alignés :</span>
                    <div className="flex flex-wrap gap-1.5 mt-0.5">
                      {selectedDetail.motifs.interets.map(getLabel).map((lbl) => (
                        <span key={lbl} className="bg-secondary px-2 py-0.5 rounded text-foreground font-medium border">
                          {lbl}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedDetail.motifs.metier_alignee && (
                  <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 p-2.5 rounded-lg border border-emerald-500/20">
                    <span className="text-base shrink-0">💼</span>
                    <span>Ce parcours prépare directement au métier ciblé dans votre profil.</span>
                  </div>
                )}

                {selectedDetail.motifs.suggestions && selectedDetail.motifs.suggestions.length > 0 && (
                  <div className="space-y-1 pt-1">
                    <span className="text-muted-foreground font-semibold">💡 Conseils de préparation (prérequis suggérés) :</span>
                    <div className="flex flex-wrap gap-1.5 mt-0.5">
                      {selectedDetail.motifs.suggestions.map(getLabel).map((lbl) => (
                        <span key={lbl} className="bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 px-2 py-0.5 rounded border border-yellow-500/20 font-medium">
                          {lbl}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <Button onClick={() => setSelectedDetail(null)}>
                Fermer
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
