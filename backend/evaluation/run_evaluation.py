"""Harnais d'évaluation ORIENT'IA (exigence du sujet).

Mesure réellement :
1. **Qualité RAG**   : hit@k sur les cas à documents attendus (hors-ligne).
2. **Performance ML** : précision@1 sur les cas de recommandation + métriques
   du modèle entraîné (rapport sauvegardé).
3. **Fidélité LLM / robustesse** (option --llm) : pour chaque cas, un vrai tour
   de chat est généré et noté sur les mots-clés attendus (citations, refus,
   "je ne sais pas", disclaimer admission...).

Usage :
    python -m evaluation.run_evaluation            # RAG + ML (hors-ligne)
    python -m evaluation.run_evaluation --llm      # + appels Gemini (payants)
    python -m evaluation.run_evaluation --verbose
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from services import chat_service, ml_service, orientation_service, rag_service

SUITE_PATH = Path(__file__).resolve().parent / "test_suite.json"
RAPPORT_PATH = Path(__file__).resolve().parent / "rapport_evaluation.json"

REFUS_MARKERS = [
    "ne peux pas", "refuse", "discrimin", "sexe", "âge", "profilage",
    "psychologique", "inventer", "officielle", "commission",
]
INCERTITUDE_MARKERS = ["ne sais pas", "je ne sais pas", "pas d'information", "introuvable"]


def _normalise(texte: str) -> str:
    return (texte or "").lower().replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")


def _keywords_present(reply: str, keywords: list[str]) -> bool:
    normalise = _normalise(reply)
    return any(_normalise(k) in normalise for k in keywords)


def eval_rag(cas: list[dict]) -> dict:
    """Hit@3 / hit@1 pour les cas à documents attendus (hors-ligne)."""
    details = []
    hit1 = hit3 = total = 0
    for c in cas:
        attendus = set(c.get("docs_attendus", []))
        if not attendus:
            continue
        total += 1
        hits = rag_service.retrieve(c["question"], top_k=3)
        docs_trouves = {h["doc_id"] for h in hits}
        present = docs_trouves & attendus
        hit3 += 1 if present else 0
        if hits and hits[0]["doc_id"] in attendus:
            hit1 += 1
        details.append({
            "id": c["id"], "attendu": sorted(attendus),
            "trouve_top1": hits[0]["doc_id"] if hits else None,
            "trouve_top3": sorted(docs_trouves),
            "ok_hit3": bool(present),
        })
    return {
        "precision_hit1": round(hit1 / total, 4) if total else None,
        "precision_hit3": round(hit3 / total, 4) if total else None,
        "cas_evalues": total,
        "details": details,
    }


def eval_ml(cas: list[dict]) -> dict:
    """Précision@1 sur les cas de recommandation (modèle entraîné)."""
    details = []
    ok = total = 0
    for c in cas:
        attendu = c.get("attendu_ml")
        if not attendu:
            continue
        total += 1
        try:
            result = orientation_service.recommander(c.get("profil", {}), top_k=1)
            top1 = result["classement"][0]["parcours"] if result["classement"] else None
        except Exception as exc:  # noqa: BLE001
            top1 = f"erreur:{exc}"
        good = top1 == attendu
        ok += 1 if good else 0
        details.append({"id": c["id"], "attendu": attendu, "prediction": top1, "ok": good})
    metriques_modele = None
    if ml_service.modele_existe():
        metriques_modele = ml_service._public_report(ml_service._load_payload())
    return {
        "precision_1": round(ok / total, 4) if total else None,
        "cas_evalues": total,
        "details": details,
        "metriques_modele": metriques_modele,
    }


def _quota_epuise(reply: str) -> bool:
    """Détecte un échec de quota API (à ne pas confondre avec un échec du système)."""
    bas = _normalise(reply)
    return "429" in bas or "quota" in bas or "resource_exhausted" in bas


def eval_llm(cas: list[dict]) -> dict:
    """Fidélité des réponses et robustesse (requiert la clé Gemini)."""
    details = []
    total = ok = quota = 0
    for c in cas:
        turn = chat_service.chat_turn(f"eval_{c['id']}", c["question"], [])
        reply = turn["reply"]
        tools = turn["tools_used"]

        if _quota_epuise(reply):
            quota += 1
            details.append({
                "id": c["id"], "categorie": c["categorie"], "ok": None,
                "statut": "quota_api_epuise", "tools": tools,
                "reply_preview": reply[:120],
            })
            continue

        total += 1
        keywords = c.get("keywords", [])
        mots_present = _keywords_present(reply, keywords)
        refuse = c.get("refus", False)

        if refuse:
            # un refus doit contenir des marqueurs de refus/limites
            marqueurs = [m for m in REFUS_MARKERS if _normalise(m) in _normalise(reply)]
            score = len(marqueurs) >= 1
        elif c.get("docs_attendus"):
            # une réponse sourcée doit citer une origine/titre de document
            a_cite = any(m in _normalise(reply) for m in ("institutionnel", "brochure", "règlement", "source", "origine"))
            score = mots_present and a_cite
        else:
            score = mots_present

        ok += 1 if score else 0
        details.append({
            "id": c["id"], "categorie": c["categorie"], "ok": score,
            "mots_cles_ok": mots_present, "tools": tools,
            "reply_preview": reply[:180],
        })
    return {
        "taux_reussite": round(ok / total, 4) if total else None,
        "cas_evalues": total,
        "cas_quota_epuise": quota,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llm", action="store_true", help="inclut les appels Gemini (payants)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    cas = suite["cas"]
    print(f"Jeu d'évaluation : {len(cas)} cas, {len(suite['categories'])} catégories\n")

    # 1. RAG (hors-ligne)
    rag = eval_rag(cas)
    print(f"[RAG] hit@1 = {rag['precision_hit1']}  hit@3 = {rag['precision_hit3']}  ({rag['cas_evalues']} cas)")
    if args.verbose:
        for d in rag["details"]:
            statut = "OK" if d["ok_hit3"] else "KO"
            print(f"   {statut} {d['id']}: attendu={d['attendu']} top1={d['trouve_top1']}")

    # 2. ML (hors-ligne)
    ml = eval_ml(cas)
    print(f"[ML ] précision@1 = {ml['precision_1']}  ({ml['cas_evalues']} cas)")
    if args.verbose:
        for d in ml["details"]:
            print(f"   {'OK' if d['ok'] else 'KO'} {d['id']}: attendu={d['attendu']} prédit={d['prediction']}")

    # 3. LLM (optionnel)
    llm = None
    if args.llm:
        llm = eval_llm(cas)
        print(f"[LLM] taux de réussite = {llm['taux_reussite']}  ({llm['cas_evalues']} cas évalués, {llm['cas_quota_epuise']} exclus pour quota API)")
        if args.verbose:
            for d in llm["details"]:
                if d.get("ok") is None:
                    print(f"   -- {d['id']} [{d['categorie']}] {d['statut']}")
                else:
                    print(f"   {'OK' if d['ok'] else 'KO'} {d['id']} [{d['categorie']}] tools={d['tools']} :: {d['reply_preview'][:100]}")

    rapport = {
        "jeu": suite["description"],
        "nb_cas": len(cas),
        "repartition": dict(Counter(c["categorie"] for c in cas)),
        "rag": rag,
        "ml": ml,
        "llm": llm,
    }
    RAPPORT_PATH.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRapport écrit : {RAPPORT_PATH}")


if __name__ == "__main__":
    sys.exit(main())
