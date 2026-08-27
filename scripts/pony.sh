#!/usr/bin/env bash
#
#  PONY - Hackathon project launcher
#  ---------------------------------
#  Check, install, test and run the whole project from one tool.
#
#  Usage:
#    ./scripts/pony.sh            full pipeline: check -> setup -> install -> train -> test -> run
#    ./scripts/pony.sh check      verify the environment (python, node, .env)
#    ./scripts/pony.sh setup      create backend/.env from the example
#    ./scripts/pony.sh install    install backend + frontend dependencies
#    ./scripts/pony.sh train      train the ML model
#    ./scripts/pony.sh test       run backend pytest + frontend lint/test/build
#    ./scripts/pony.sh run        start backend (:8000) + frontend (:3000)
#    ./scripts/pony.sh run-api    start only the FastAPI backend
#    ./scripts/pony.sh run-web    start only the Next.js frontend
#    ./scripts/pony.sh help       this help
#

set -uo pipefail

# ─────────────────────────────────────────────────────────────
#  Colors & helpers
# ─────────────────────────────────────────────────────────────
BOLD="\e[1m"; DIM="\e[2m"; ITALIC="\e[3m"
CYAN="\e[38;5;45m"; PURPLE="\e[38;5;141m"; GREEN="\e[38;5;82m"
RED="\e[38;5;196m"; YELLOW="\e[38;5;226m"; GREY="\e[38;5;244m"; NC="\e[0m"

ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

banner() {
  printf "${CYAN}"
  cat <<'EOF'
  ██████╗  ██████╗ ███╗   ██╗██╗   ██╗
 ██╔═══██╗██╔═══██╗████╗  ██║╚██╗ ██╔╝
 ██║   ██║██║   ██║██╔██╗ ██║ ╚████╔╝
 ████████║██║   ██║██║╚██╗██║  ╚██╔╝
 ██║       ██████╔╝██║ ╚████║   ██║
 ██║       ╚═════╝ ╚═╝  ╚═══╝   ╚═╝
EOF
  printf "${NC}"
  printf "${PURPLE}${BOLD}  Hackathon AI Agent - launcher ${NC}${GREY}(check · install · test · run)${NC}\n\n"
}

line() { printf "${GREY}%80s${NC}\n" "" | tr ' ' '─'; }

section() {
  printf "\n${PURPLE}${BOLD}── $1 ${NC}${GREY}${2:-}${NC}\n"
}

ok()   { printf "${GREEN}  [ OK ] ${NC}%s\n" "$1"; }
fail() { printf "${RED}  [FAIL] ${NC}%s\n" "$1"; exit 1; }
warn() { printf "${YELLOW} [WARN] ${NC}%s\n" "$1"; }
info() { printf "${CYAN}  [...] ${NC}%s\n" "$1"; }

# ─────────────────────────────────────────────────────────────
#  Steps
# ─────────────────────────────────────────────────────────────
cmd() { command -v "$1" >/dev/null 2>&1; }

step_check() {
  section "ENVIRONNEMENT" "vérification des outils installés"

  local status=0
  cmd python3        && ok  "python3       $(python3 --version 2>&1 | awk '{print $2}')" || { fail "python3 absent"; }
  cmd node           && ok  "node          $(node -v)"                                 || { fail "node absent"; }
  cmd npm            && ok  "npm           $(npm -v)"                                  || { fail "npm absent"; }

  if [ -f "$BACKEND/.env" ]; then
    ok "backend/.env trouvé"
    if grep -q "your_api_key_here" "$BACKEND/.env" 2>/dev/null; then
      warn "GEMINI_API_KEY n'est pas encore configurée (voir docs/tutorials/setup_gemini.md)"
    else
      ok "GEMINI_API_KEY configurée"
    fi
  else
    warn "backend/.env manquant -> lancez: ./scripts/pony.sh setup"
  fi
  return $status
}

step_setup() {
  section "CONFIGURATION" "fichiers d'environnement"
  if [ -f "$BACKEND/.env" ]; then
    ok "backend/.env existe déjà"
  else
    cp "$BACKEND/.env.example" "$BACKEND/.env"
    warn "backend/.env créé depuis .env.example"
    warn "-> éditez-le et mettez votre GEMINI_API_KEY (docs/tutorials/setup_gemini.md)"
  fi
}

step_install() {
  section "INSTALLATION" "dépendances backend + frontend"

  if [ ! -d "$VENV" ]; then
    info "création de l'environnement virtuel python..."
    python3 -m venv "$VENV" || fail "impossible de créer le venv"
  else
    ok "venv python présent"
  fi

  info "installation des dépendances backend..."
  "$PIP" install -q -r "$BACKEND/requirements-dev.txt" >/dev/null 2>&1 \
    || fail "échec de l'installation backend"
  ok "dépendances backend installées"

  if [ ! -d "$FRONTEND/node_modules" ]; then
    info "installation des dépendances frontend (npm install)..."
    ( cd "$FRONTEND" && npm install --no-audit --no-fund >/dev/null 2>&1 ) \
      || fail "échec de l'installation frontend"
  else
    ok "node_modules présent"
  fi
  ok "dépendances frontend installées"
}

step_train() {
  section "MACHINE LEARNING" "entraînement du modèle"
  info "RandomForest vs LogisticRegression sur les profils ORIENT'IA..."
  ( cd "$BACKEND" && "$PY" -m services.ml_service )
  ok "modèle entraîné et sauvegardé (backend/ml_model.joblib)"
}

step_test() {
  section "TESTS" "backend + frontend"

  info "pytest (backend)..."
  ( cd "$BACKEND" && "$PY" -m pytest tests -q --no-header >/dev/null 2>&1 ) \
    && ok "tests backend réussis" || fail "des tests backend échouent"

  info "eslint (frontend)..."
  ( cd "$FRONTEND" && npm run lint --silent >/dev/null 2>&1 ) \
    && ok "lint frontend propre" || fail "lint frontend en erreur"

  info "vitest (frontend)..."
  ( cd "$FRONTEND" && npm test --silent >/dev/null 2>&1 ) \
    && ok "tests frontend réussis" || fail "des tests frontend échouent"

  info "build Next.js (typecheck + compilation)..."
  ( cd "$FRONTEND" && npm run build >/dev/null 2>&1 ) \
    && ok "build frontend OK" || fail "build frontend en erreur"
}

step_resetdb() {
  section "BASE DE DONNÉES" "réinitialisation SQLite"
  local db_path="$BACKEND/clinique.db"

  if [ -f "$BACKEND/.env" ] && grep -q "^DB_PATH=" "$BACKEND/.env"; then
    local configured="$(grep "^DB_PATH=" "$BACKEND/.env" | head -1 | cut -d= -f2)"
    [ -n "$configured" ] && db_path="$configured"
    [[ "$db_path" != /* ]] && db_path="$BACKEND/$db_path"
  fi

  if [ -f "$db_path" ]; then
    rm -f "$db_path"
    ok "base supprimée: $db_path"
  else
    info "aucune base à supprimer: $db_path"
  fi
  info "elle sera recréée automatiquement au prochain démarrage (tables + schéma)."
}

step_eval() {
  section "ÉVALUATION" "jeu de 34 cas (RAG + ML + LLM)"
  info "RAG + ML hors-ligne..."
  ( cd "$BACKEND" && "$PY" -m evaluation.run_evaluation )
  ok "rapport écrit (evaluation/rapport_evaluation.json)"
  warn "Ajoutez --llm pour mesurer la fidélité des réponses (appels Gemini, quota)."
}

CLEANED=0
cleanup() {
  [ "$CLEANED" -eq 1 ] && return
  CLEANED=1
  [ -n "${BACKEND_PID:-}" ] && kill -- -"$BACKEND_PID" 2>/dev/null
  [ -n "${FRONTEND_PID:-}" ] && kill -- -"$FRONTEND_PID" 2>/dev/null
  pkill -f "[u]vicorn main:app --port 8000" 2>/dev/null
  pkill -f "[n]ext dev" 2>/dev/null
  printf "\n${GREY}  serveurs arrêtés. À bientôt !${NC}\n"
}

step_run() {
  section "LANCEMENT" "backend :8000 · frontend :3000"
  info "le projet tourne. Ctrl+C pour tout arrêter."
  line

  setsid bash -c "cd '$BACKEND' && exec '$VENV/bin/uvicorn' main:app --port 8000" \
    >/dev/null 2>&1 &
  BACKEND_PID=$!
  setsid bash -c "cd '$FRONTEND' && exec npm run dev" >/dev/null 2>&1 &
  FRONTEND_PID=$!

  trap 'cleanup; exit 0' INT TERM
  trap cleanup EXIT

  printf "${GREEN}  API  -> http://localhost:8000  (docs: /docs)${NC}\n"
  printf "${GREEN}  Chat -> http://localhost:3000${NC}\n"
  line

  while true; do sleep 1; done
}

# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────
usage() {
  banner
  cat <<EOF
Usage: ./scripts/pony.sh [commande]

  (aucune)   pipeline complet: check → setup → install → train → test → run
  check      vérifie l'environnement
  setup      crée backend/.env
  install    installe les dépendances
  train      entraîne le modèle ML
  test       lance tous les tests (backend + frontend)
  eval       lance l'évaluation (RAG + ML ; --llm pour le LLM)
  resetdb    supprime la base SQLite (clinique.db), recréée au prochain démarrage
  run        démarre backend + frontend
  run-api    démarre seulement le backend
  run-web    démarre seulement le frontend
  help       affiche cette aide

Sur Windows, utilisez l'équivalent PowerShell:  .\scripts\pony.ps1  (ou .\pony.cmd)
EOF
}

main() {
  banner
  case "${1:-}" in
    check)     step_check ;;
    setup)     step_setup ;;
    install)   step_install ;;
    train)     step_train ;;
    test)      step_test ;;
    eval)      step_eval ;;
    resetdb)   step_resetdb ;;
    run)       step_run ;;
    run-api)   ( cd "$BACKEND" && "$VENV/bin/uvicorn" main:app --port 8000 --reload ) ;;
    run-web)   ( cd "$FRONTEND" && npm run dev ) ;;
    help|-h|--help) usage ;;
    "")
      step_check
      step_setup
      step_install
      step_train
      step_test
      step_run
      ;;
    *) echo "Commande inconnue: $1"; usage; exit 1 ;;
  esac
}

main "$@"
