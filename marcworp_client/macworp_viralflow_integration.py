"""
macworp_viralflow_integration.py
─────────────────────────────────
Exemplo de como integrar o cliente ViralFlow no backend MacWorp.

Inclui:
  1. Endpoint de callback (recebe notificação do ViralFlow ao término)
  2. Exemplo de submissão de job
  3. Exemplo de polling manual
"""

# ──────────────────────────────────────────────────────────────────────────────
# 1. Endpoint de callback — adicione ao backend Flask/FastAPI do MacWorp
# ──────────────────────────────────────────────────────────────────────────────

# === Se o MacWorp usa Flask: ===
#
# from flask import Blueprint, request, jsonify, abort
# from macworp_viralflow_client import JobResult, JobStatus
#
# viralflow_bp = Blueprint("viralflow", __name__, url_prefix="/api/viralflow")
#
# @viralflow_bp.route("/callback", methods=["POST"])
# def viralflow_callback():
#     api_key = request.headers.get("X-Api-Key")
#     if api_key != current_app.config["VIRALFLOW_CALLBACK_KEY"]:
#         abort(401)
#
#     data = request.get_json()
#     job_id          = data["job_id"]
#     macworp_run_id  = data["macworp_run_id"]
#     status          = data["status"]
#     output_files    = data.get("output_files", [])
#     error_message   = data.get("error_message")
#
#     # Atualize seu banco de dados MacWorp aqui
#     run = Run.query.get(macworp_run_id)
#     if run:
#         run.viralflow_status = status
#         run.viralflow_results = data
#         db.session.commit()
#
#     return jsonify({"received": True}), 200


# === Se o MacWorp usa FastAPI: ===
#
# from fastapi import APIRouter, Header, HTTPException
# from macworp_viralflow_client import JobResult, JobStatus
#
# router = APIRouter(prefix="/api/viralflow")
#
# @router.post("/callback")
# async def viralflow_callback(result: dict, x_api_key: str = Header(...)):
#     if x_api_key != settings.VIRALFLOW_CALLBACK_KEY:
#         raise HTTPException(status_code=401)
#
#     run_id = result["macworp_run_id"]
#     status = result["status"]
#     # ... salve no banco ...
#     return {"received": True}


# ──────────────────────────────────────────────────────────────────────────────
# 2. Exemplo de submissão de job pelo MacWorp
# ──────────────────────────────────────────────────────────────────────────────

from macworp_viralflow_client import (
    ViralFlowClient,
    ViralFlowJobParams,
    ViralFlowAPIError,
    ViralFlowJobFailed,
    JobStatus,
)

# Instancie o cliente uma vez (idealmente como singleton/injeção de dependência)
viralflow = ViralFlowClient(
    base_url="http://viralflow-server:8000",   # URL do servidor ViralFlow
    api_key="troque-por-uma-chave-forte-aqui", # Mesma API_KEY do .env do ViralFlow
)


def submit_viralflow_analysis(
    project_id: str,
    run_id: str,
    fastq_dir: str,
    output_dir: str,
    virus: str = "sars-cov2",
) -> str:
    """
    Submete uma análise ViralFlow e retorna o job_id.
    Chame esta função quando o usuário iniciar um workflow no MacWorp.
    """
    params = ViralFlowJobParams(
        macworp_project_id=project_id,
        macworp_run_id=run_id,
        in_dir=fastq_dir,
        out_dir=output_dir,
        virus=virus,
        # Callback: ViralFlow notificará o MacWorp ao terminar
        callback_url="http://macworp-server:3001/api/viralflow/callback",
        callback_api_key="chave-do-macworp",
    )

    response = viralflow.submit_job(params)
    print(f"[ViralFlow] Job submetido: {response.job_id} (status: {response.status})")

    # Salve response.job_id no banco do MacWorp para referência futura
    return response.job_id


def check_job(job_id: str) -> JobStatus:
    """Verifica o status de um job (para polling periódico pelo MacWorp)."""
    status_resp = viralflow.get_status(job_id)
    return status_resp.status


def fetch_results(job_id: str):
    """Busca e processa os resultados de um job concluído."""
    try:
        result = viralflow.get_results(job_id)
        print(f"[ViralFlow] Job {job_id} concluído em {result.duration_seconds:.1f}s")
        print(f"  Arquivos gerados: {len(result.output_files)}")
        for f in result.output_files:
            print(f"    - {f.name} ({f.size_bytes} bytes) — {f.description}")
        return result
    except ViralFlowAPIError as e:
        print(f"[ViralFlow] Erro ao buscar resultados: {e}")
        raise


# ──────────────────────────────────────────────────────────────────────────────
# 3. Exemplo completo com polling (sem callback)
# ──────────────────────────────────────────────────────────────────────────────

def run_analysis_synchronously(project_id: str, run_id: str, fastq_dir: str):
    """
    Submete e aguarda o resultado de forma síncrona.
    Útil para scripts/testes — em produção prefira o callback assíncrono.
    """
    params = ViralFlowJobParams(
        macworp_project_id=project_id,
        macworp_run_id=run_id,
        in_dir=fastq_dir,
        out_dir=f"/data/results/{run_id}",
        virus="sars-cov2",
    )

    # Submete
    submission = viralflow.submit_job(params)
    print(f"Job {submission.job_id} submetido.")

    # Aguarda com polling a cada 30s, notificando mudanças de status
    def on_status_change(job_id, status):
        print(f"  → Status: {status}")

    try:
        result = viralflow.wait_for_job(
            submission.job_id,
            poll_interval=30.0,
            on_status_change=on_status_change,
        )
        print(f"Análise concluída! {len(result.output_files)} arquivos gerados.")
        return result

    except ViralFlowJobFailed as e:
        print(f"Pipeline falhou: {e.result.error_message}")
        print(f"Log:\n{e.result.nextflow_log}")
        raise
