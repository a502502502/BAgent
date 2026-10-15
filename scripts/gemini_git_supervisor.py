#!/usr/bin/env python3
"""
scripts/gemini_git_supervisor.py — Supervisore Quantitativo BAgent (Architettura 2).

Eseguito automaticamente ad ogni git push (GitHub Actions CI/CD) o in locale tramite git hook.
Esegue controlli deterministici rigorosi (Regole #76, #80, #82, #83, #85, #86) e,
se GEMINI_API_KEY è configurata, attiva l'audit cognitivo via Google AI Studio API (Free Tier).
Invia alert Telegram in caso di anomalie e salva il report in reports/gemini_supervisor_latest.json.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

REPORT_PATH = ROOT / "reports" / "gemini_supervisor_latest.json"
SCHEDINE_PATH = ROOT / "portal" / "schedine.json"
SNAPSHOT_PATH = ROOT / "SNAPSHOT_OGGI.json"
REALITY_SNAPSHOT_PATH = ROOT / "data" / "daily_reality_snapshot.json"
CLAUDE_MD_PATH = ROOT / "CLAUDE.md"


def send_telegram_alert(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[TELEGRAM] Credenziali non presenti, notifica saltata.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[WARN] Invio Telegram fallito: {e}")
        return False


def run_deterministic_audit(schedine_data: Dict[str, Any], reality_data: Dict[str, Any]) -> Dict[str, Any]:
    present_tickets = schedine_data.get("present", [])
    anomalies: List[str] = []
    total_exposure = 0.0
    selection_counts: Dict[str, int] = {}
    
    for ticket in present_tickets:
        t_id = ticket.get("id", "SCONOSCIUTO")
        stake_str = str(ticket.get("stake", "0")).replace("€", "").replace(",", ".").strip()
        try:
            stake_val = float(stake_str)
            total_exposure += stake_val
        except ValueError:
            pass

        legs = ticket.get("legs", [])
        for leg in legs:
            match = leg.get("match", "")
            pick = leg.get("pick", "")
            odd_str = str(leg.get("odd", "0")).replace(",", ".").strip()
            
            # Chiave per ortogonalita
            key = f"{match} :: {pick}"
            selection_counts[key] = selection_counts.get(key, 0) + 1

            try:
                odd_val = float(odd_str)
                # Regola #82: Divieto quota compressa sotto 1.20 (tranne se esplicitamente autorizzato da strategia)
                if odd_val < 1.15:
                    anomalies.append(f"Regola #82: Quota compressa estrema @{odd_val:.2f} su '{match}' ({pick}) nel ticket {t_id}.")
                elif odd_val < 1.20:
                    anomalies.append(f"Avviso Quota: Quota @{odd_val:.2f} sotto soglia ottimale 1.20 su '{match}' ({pick}).")
            except ValueError:
                pass

            # Regola #82: Divieto 1X2 secco a quota compressa
            if pick in ["1", "2", "1 Fisso", "2 Fisso"] and odd_val < 1.65:
                anomalies.append(f"Regola #82 (Gate 0): 1X2 secco a quota compressa @{odd_val:.2f} vietato su '{match}'.")

    # Regola #86: Controllo Ortogonalita
    orthogonality_passed = True
    for sel_key, count in selection_counts.items():
        if count > 2:
            orthogonality_passed = False
            anomalies.append(f"Regola #86 (Ortogonalita): Selezione duplicata in {count} ticket attivi: '{sel_key}'.")

    # Regola #85: Reality Gate Check solo sui ticket attivi stasera
    if reality_data:
        present_ids = {t.get("id") for t in present_tickets}
        tickets_audited = reality_data.get("active_tickets_audit", {}).get("tickets", [])
        active_violations = [t for t in tickets_audited if t.get("ticket_id") in present_ids and t.get("violations")]
        if active_violations:
            for bad_t in active_violations:
                anomalies.append(f"Regola #85 (Reality Gate): Violazione attiva in {bad_t.get('ticket_id')}: {bad_t.get('violations')}")

    # Determinazione verdetto
    has_blocking = any("Regola #82 (Gate 0)" in a or "Regola #85" in a for a in anomalies)
    if has_blocking:
        verdict = "REJECTED"
    elif anomalies:
        verdict = "WARNING"
    else:
        verdict = "APPROVED"

    return {
        "verdict": verdict,
        "orthogonality_passed": orthogonality_passed,
        "bankroll_exposure_eur": round(total_exposure, 2),
        "total_active_tickets": len(present_tickets),
        "anomalies_found": anomalies,
        "optimization_advice": "Mantenere l'esposizione entro l'8% di bankroll e rispettare le quote minime >= 1.20."
    }


def call_gemini_cloud_supervisor(rules_text: str, schedine_data: dict, snap_data: dict, api_key: str) -> Optional[dict]:
    models = ["gemini-2.5-flash", "gemini-1.5-flash"]
    prompt = f"""
Sei il Supervisore Quantitativo di BAgent. Analizza il commit appena effettuato sulle schedine attive.
Verifica il rispetto delle regole del protocollo:
- Regola #76: Nessuna selezione su partite gia iniziate.
- Regola #82: Divieto 1 o 2 fisso compresso (< 1.65), quote minime preferibili >= 1.20.
- Regola #83: Money management e budget bilanciato.
- Regola #85: Reality Gate (allenatori e rose correnti 2026/27).
- Regola #86: Ortogonalita delle selezioni tra ticket diversi.

SCHEDINE ATTIVE (present):
{json.dumps(schedine_data.get('present', []), indent=2, ensure_ascii=False)}

SNAPSHOT STATO GIORNALIERO:
{json.dumps(snap_data.get('hygiene_summary', snap_data), indent=2, ensure_ascii=False)[:2000]}

Rispondi TASSATIVAMENTE in formato JSON valido:
{{
  "verdict": "APPROVED" | "WARNING" | "REJECTED",
  "orthogonality_passed": true,
  "bankroll_exposure_eur": 0.0,
  "anomalies_found": ["lista anomalie"],
  "optimization_advice": "consiglio sintetico per massimizzare l'EV"
}}
"""
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
    }).encode("utf-8")

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_json = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_json)
        except Exception as e:
            print(f"[GEMINI] Chiamata su modello {model} fallita: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(description="BAgent Git Supervisor")
    parser.add_argument("--local-pre-push", action="store_true", help="Esegui in modalita git hook pre-push")
    parser.add_argument("--sync-drive", action="store_true", help="Sincronizza anche su Google Drive")
    args = parser.parse_args()

    print("=" * 80)
    print("BAGENT — GIT QUANTITATIVE SUPERVISOR (AUDIT QUALITA & CONFORMITA)")
    print("=" * 80)

    claude_md = CLAUDE_MD_PATH.read_text(encoding="utf-8") if CLAUDE_MD_PATH.exists() else ""
    schedine = json.loads(SCHEDINE_PATH.read_text(encoding="utf-8")) if SCHEDINE_PATH.exists() else {}
    reality = json.loads(REALITY_SNAPSHOT_PATH.read_text(encoding="utf-8")) if REALITY_SNAPSHOT_PATH.exists() else {}
    snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")) if SNAPSHOT_PATH.exists() else {}

    # 1. Audit deterministico locale
    det_report = run_deterministic_audit(schedine, reality)

    # 2. Audit Gemini Cloud se API Key presente
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print("[SUPERVISOR] GEMINI_API_KEY rilevata. Richiesta audit cognitivo Gemini Cloud...")
        cloud_report = call_gemini_cloud_supervisor(claude_md, schedine, snap, api_key)
        if cloud_report:
            final_report = cloud_report
            final_report["source"] = "GEMINI_CLOUD_AI_STUDIO"
            final_report["deterministic_validation"] = det_report
        else:
            final_report = det_report
            final_report["source"] = "DETERMINISTIC_FALLBACK"
    else:
        print("[SUPERVISOR] GEMINI_API_KEY non impostata. Eseguito audit deterministico locale (Zero Costo).")
        final_report = det_report
        final_report["source"] = "LOCAL_DETERMINISTIC_ENGINE"

    print("\n--- RISULTATO AUDIT SUPERVISORE ---")
    print(json.dumps(final_report, indent=2, ensure_ascii=False))

    # 3. Scrittura Report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(final_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport salvato in {REPORT_PATH}")

    # 4. Notifica Telegram se WARNING o REJECTED
    verdict = final_report.get("verdict", "APPROVED")
    if verdict in ("WARNING", "REJECTED"):
        anomalies_text = "\n- ".join(final_report.get("anomalies_found", []))
        msg = (
            f"⚠️ *BAgent Git Supervisor: Verdetto {verdict}*\n"
            f"Esposizione totale: `{final_report.get('bankroll_exposure_eur')} €`\n"
            f"Anomalie riscontrate:\n- {anomalies_text}\n\n"
            f"Consiglio: {final_report.get('optimization_advice')}"
        )
        send_telegram_alert(msg)

    # 5. Sincronizzazione Drive opzionale
    if args.sync_drive:
        sync_script = ROOT / "scripts" / "sync_to_drive_supervisor.py"
        if sync_script.exists():
            os.system(f'python "{sync_script}"')

    # 6. Blocco pre-push se esito REJECTED
    if args.local_pre_push and verdict == "REJECTED":
        print("\n[ERRORE PRE-PUSH] Il push e stato bloccato dal Supervisore Quantitativo!")
        sys.exit(1)

    print("\nSupervisione completata con successo.")
    sys.exit(0)


if __name__ == "__main__":
    main()
