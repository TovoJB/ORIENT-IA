<#
  PONY - Hackathon project launcher (Windows / PowerShell)
  --------------------------------------------------------
  Même outil que scripts/pony.sh, mais pour Windows.

  Utilisation:
    .\scripts\pony.ps1             pipeline complet: check -> setup -> install -> train -> test -> run
    .\scripts\pony.ps1 check       vérifie l'environnement (python, node, .env)
    .\scripts\pony.ps1 setup       crée backend\.env
    .\scripts\pony.ps1 install     installe les dépendances
    .\scripts\pony.ps1 train       entraîne le modèle ML
    .\scripts\pony.ps1 test        lance tous les tests
    .\scripts\pony.ps1 run         démarre backend (:8000) + frontend (:3000)
    .\scripts\pony.ps1 run-api     démarre seulement le backend
    .\scripts\pony.ps1 run-web     démarre seulement le frontend
    .\scripts\pony.ps1 help        cette aide

  Si le lancement est bloqué par la politique d'exécution:
    powershell -ExecutionPolicy Bypass -File .\scripts\pony.ps1
  Ou lancez simplement: .\pony.cmd
#>

$ErrorActionPreference = "Stop"

# ── Couleurs (Windows Terminal prend en charge les codes ANSI) ──
$BOLD  = "$([char]27)[1m"
$CYAN  = "$([char]27)[38;5;45m"
$PURPLE= "$([char]27)[38;5;141m"
$GREEN = "$([char]27)[38;5;82m"
$RED   = "$([char]27)[38;5;196m"
$YELLOW= "$([char]27)[38;5;226m"
$GREY  = "$([char]27)[38;5;244m"
$NC    = "$([char]27)[0m"

$ROOT     = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BACKEND  = Join-Path $ROOT "backend"
$FRONTEND = Join-Path $ROOT "frontend"
$VENV     = Join-Path $BACKEND ".venv"
$PY       = Join-Path $VENV "Scripts\python.exe"
$PIP      = Join-Path $VENV "Scripts\pip.exe"

function Banner {
    Write-Output "${CYAN}"
    Write-Output "  ██████╗ ██████╗ ███╗   ██╗██╗   ██╗"
    Write-Output " ██╔═══██╗██╔═══██╗████╗  ██║╚██╗ ██╔╝"
    Write-Output " ██║   ██║██║   ██║██╔██╗ ██║ ╚████╔╝"
    Write-Output " ██║   ██║██║   ██║██║╚██╗██║  ╚██╔╝"
    Write-Output " ╚██████╔╝╚██████╔╝██║ ╚████║   ██║"
    Write-Output "  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝   ╚═╝"
    Write-Output "${NC}"
    Write-Output "${PURPLE}${BOLD}  Hackathon AI Agent - launcher ${NC}${GREY}(check · install · test · run)${NC}"
    Write-Output ""
}

function Section([string]$title, [string]$sub = "") {
    Write-Output ""
    Write-Output "${PURPLE}${BOLD}── $title ${NC}${GREY}$sub${NC}"
}

function Ok([string]$msg)   { Write-Output "${GREEN}  [ OK ] ${NC}$msg" }
function Fail([string]$msg) { Write-Output "${RED}  [FAIL] ${NC}$msg"; exit 1 }
function Warn([string]$msg) { Write-Output "${YELLOW} [WARN] ${NC}$msg" }
function Info([string]$msg) { Write-Output "${CYAN}  [...] ${NC}$msg" }
function Line { Write-Output $("-" * 70) }

# ─────────────────────────────────────────────────────────────
#  Étapes
# ─────────────────────────────────────────────────────────────
function Step-Check {
    Section "ENVIRONNEMENT" "vérification des outils installés"
    foreach ($tool in @("python", "node", "npm")) {
        if (Get-Command $tool -ErrorAction SilentlyContinue) {
            Ok "$tool trouvé"
        } else {
            Fail "$tool absent - installez-le (voir docs/tutorials/setup_gemini.md)"
        }
    }
    if (Test-Path (Join-Path $BACKEND ".env")) {
        Ok "backend\.env trouvé"
        if ((Get-Content (Join-Path $BACKEND ".env") -Raw) -match "your_api_key_here") {
            Warn "GEMINI_API_KEY n'est pas encore configurée (docs/tutorials/setup_gemini.md)"
        } else {
            Ok "GEMINI_API_KEY configurée"
        }
    } else {
        Warn "backend\.env manquant -> lancez: .\scripts\pony.ps1 setup"
    }
}

function Step-Setup {
    Section "CONFIGURATION" "fichiers d'environnement"
    if (Test-Path (Join-Path $BACKEND ".env")) {
        Ok "backend\.env existe déjà"
    } else {
        Copy-Item (Join-Path $BACKEND ".env.example") (Join-Path $BACKEND ".env")
        Warn "backend\.env créé depuis .env.example"
        Warn "-> éditez-le et mettez votre GEMINI_API_KEY (docs/tutorials/setup_gemini.md)"
    }
}

function Step-Install {
    Section "INSTALLATION" "dépendances backend + frontend"

    if (-not (Test-Path $PY)) {
        Info "création de l'environnement virtuel python..."
        python -m venv $VENV | Out-Null
        if (-not (Test-Path $PY)) { Fail "impossible de créer le venv" }
    } else {
        Ok "venv python présent"
    }

    Info "installation des dépendances backend..."
    & $PIP install -r (Join-Path $BACKEND "requirements-dev.txt") | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "échec de l'installation backend" }
    Ok "dépendances backend installées"

    if (-not (Test-Path (Join-Path $FRONTEND "node_modules"))) {
        Info "installation des dépendances frontend (npm install)..."
        Push-Location $FRONTEND
        try { npm install --no-audit --no-fund | Out-Null }
        finally { Pop-Location }
        if ($LASTEXITCODE -ne 0) { Fail "échec de l'installation frontend" }
    } else {
        Ok "node_modules présent"
    }
    Ok "dépendances frontend installées"
}

function Step-Train {
    Section "MACHINE LEARNING" "entraînement du modèle"
    Info "RandomForest vs LogisticRegression sur les profils ORIENT'IA..."
    Push-Location $BACKEND
    try { & $PY -m services.ml_service }
    finally { Pop-Location }
    Ok "modèle entraîné et sauvegardé (backend\ml_model.joblib)"
}

function Step-Test {
    Section "TESTS" "backend + frontend"

    Info "pytest (backend)..."
    Push-Location $BACKEND
    try { & $PY -m pytest tests -q --no-header | Out-Null } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Fail "des tests backend échouent" }
    Ok "tests backend réussis"

    Info "eslint (frontend)..."
    Push-Location $FRONTEND
    try { npm run lint --silent | Out-Null } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Fail "lint frontend en erreur" }
    Ok "lint frontend propre"

    Info "vitest (frontend)..."
    Push-Location $FRONTEND
    try { npm test --silent | Out-Null } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Fail "des tests frontend échouent" }
    Ok "tests frontend réussis"

    Info "build Next.js (typecheck + compilation)..."
    Push-Location $FRONTEND
    try { npm run build | Out-Null } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Fail "build frontend en erreur" }
    Ok "build frontend OK"
}


function Step-Eval {
    Section "ÉVALUATION" "jeu de 34 cas (RAG + ML + LLM)"
    Info "RAG + ML hors-ligne..."
    Push-Location $BACKEND
    try { & $PY -m evaluation.run_evaluation } finally { Pop-Location }
    Ok "rapport écrit (evaluation\rapport_evaluation.json)"
    Warn "Ajoutez --llm pour mesurer la fidélité des réponses (appels Gemini, quota)."
}

function Step-ResetDb {
    Section "BASE DE DONNÉES" "réinitialisation SQLite"
    $dbPath = Join-Path $BACKEND "clinique.db"

    $envFile = Join-Path $BACKEND ".env"
    if (Test-Path $envFile) {
        $line = Get-Content $envFile | Where-Object { $_ -match "^DB_PATH=" } | Select-Object -First 1
        if ($line) {
            $configured = ($line -split "=", 2)[1]
            if ($configured) {
                if ([System.IO.Path]::IsPathRooted($configured)) {
                    $dbPath = $configured
                } else {
                    $dbPath = Join-Path $BACKEND $configured
                }
            }
        }
    }

    if (Test-Path $dbPath) {
        Remove-Item $dbPath -Force
        Ok "base supprimée: $dbPath"
    } else {
        Info "aucune base à supprimer: $dbPath"
    }
    Info "elle sera recréée automatiquement au prochain démarrage (tables + schéma)."
}

function Step-Run {
    Section "LANCEMENT" "backend :8000 · frontend :3000"
    Info "le projet tourne. Ctrl+C pour tout arrêter."
    Line

    $api = Start-Process -FilePath $PY -ArgumentList "-m", "uvicorn", "main:app", "--port", "8000" `
        -WorkingDirectory $BACKEND -PassThru -NoNewWindow
    $web = Start-Process -FilePath "npm" -ArgumentList "run", "dev" `
        -WorkingDirectory $FRONTEND -PassThru -NoNewWindow

    Write-Output "${GREEN}  API  -> http://localhost:8000  (docs: /docs)${NC}"
    Write-Output "${GREEN}  Chat -> http://localhost:3000${NC}"
    Line

    try {
        Wait-Process -Id $api.Id, $web.Id -ErrorAction SilentlyContinue
    } finally {
        taskkill /PID $api.Id /T /F 2>$null | Out-Null
        taskkill /PID $web.Id /T /F 2>$null | Out-Null
        Write-Output ""
        Write-Output "${GREY}  serveurs arrêtés. À bientôt !${NC}"
    }
}

function Show-Help {
    Banner
    Write-Output "Usage: .\scripts\pony.ps1 [commande]"
    Write-Output ""
    Write-Output "  (aucune)   pipeline complet: check -> setup -> install -> train -> test -> run"
    Write-Output "  check      vérifie l'environnement"
    Write-Output "  setup      crée backend\.env"
    Write-Output "  install    installe les dépendances"
    Write-Output "  train      entraîne le modèle ML"
    Write-Output "  test       lance tous les tests (backend + frontend)"
    Write-Output "  eval       lance l'évaluation (RAG + ML ; --llm pour le LLM)"
    Write-Output "  resetdb    supprime la base SQLite (clinique.db), recréée au prochain démarrage"
    Write-Output "  run        démarre backend + frontend"
    Write-Output "  run-api    démarre seulement le backend"
    Write-Output "  run-web    démarre seulement le frontend"
    Write-Output "  help       affiche cette aide"
    Write-Output ""
    Write-Output "Astuce: si PowerShell bloque le script, lancez .\pony.cmd (contourne la restriction)."
}

# ─────────────────────────────────────────────────────────────
#  Point d'entrée
# ─────────────────────────────────────────────────────────────
Banner
$cmd = ""
if ($args.Count -gt 0) { $cmd = $args[0].ToLower() }

switch ($cmd) {
    "check"   { Step-Check }
    "setup"   { Step-Setup }
    "install" { Step-Install }
    "train"   { Step-Train }
    "test"    { Step-Test }
    "eval"    { Step-Eval }
    "resetdb" { Step-ResetDb }
    "run"     { Step-Run }
    "run-api" {
        Push-Location $BACKEND
        & $PY -m uvicorn main:app --port 8000 --reload
        Pop-Location
    }
    "run-web" {
        Push-Location $FRONTEND
        npm run dev
        Pop-Location
    }
    "help"    { Show-Help }
    "-h"      { Show-Help }
    "--help"  { Show-Help }
    "" {
        Step-Check
        Step-Setup
        Step-Install
        Step-Train
        Step-Test
        Step-Run
    }
    default {
        Write-Output "Commande inconnue: $cmd"
        Show-Help
        exit 1
    }
}
