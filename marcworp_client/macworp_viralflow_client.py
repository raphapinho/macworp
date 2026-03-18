"""
macworp_viralflow_client.py
───────────────────────────
Cliente HTTP para o MacWorp se comunicar com a ViralFlow API.

Uso básico:
    from macworp_viralflow_client import ViralFlowClient, ViralFlowJobParams

    client = ViralFlowClient(
        base_url="http://viralflow-server:8000",
        api_key="chave-compartilhada",
    )

    job_params = ViralFlowJobParams(
        macworp_project_id="proj-123",
        macworp_run_id="run-456",
        in_dir="/data/fastq/amostras",
        out_dir="/data/resultados/run-456",
        virus="sars-cov2",
        callback_url="http://macworp-server:3001/api/viralflow/callback",
        callback_api_key="chave-do-macworp",
    )

    response = client.submit_job(job_params)
    print(response.job_id)   # Use para polling

    # Polling até concluir
    result = client.wait_for_job(response.job_id)
    print(result.output_files)
"""

from __future__ import annotations

import time
import httpx
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ──────────────────────────────────────────
# Modelos de dados (espelham a API)
# ──────────────────────────────────────────

class JobStatus(str, Enum):
    QUEUED    = "queued"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"
    CANCELLED = "cancelled"


@dataclass
class ViralFlowJobParams:
    """Parâmetros para submeter um job ao ViralFlow."""
    macworp_project_id: str
    macworp_run_id: str
    in_dir: str
    out_dir: str
    virus: str = "sars-cov2"
    depth: int = 25
    min_len: int = 75
    run_snpeff: bool = True
    write_mapped_reads: bool = True
    min_dp_intrahost: int = 100
    extra_params: Optional[Dict[str, Any]] = None
    callback_url: Optional[str] = None
    callback_api_key: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "macworp_project_id":  self.macworp_project_id,
            "macworp_run_id":      self.macworp_run_id,
            "in_dir":              self.in_dir,
            "out_dir":             self.out_dir,
            "virus":               self.virus,
            "depth":               self.depth,
            "min_len":             self.min_len,
            "run_snpeff":          self.run_snpeff,
            "write_mapped_reads":  self.write_mapped_reads,
            "min_dp_intrahost":    self.min_dp_intrahost,
            "extra_params":        self.extra_params,
            "callback_url":        self.callback_url,
            "callback_api_key":    self.callback_api_key,
        }


@dataclass
class OutputFile:
    name: str
    path: str
    size_bytes: Optional[int] = None
    description: Optional[str] = None


@dataclass
class JobSubmitResponse:
    job_id: str
    status: JobStatus
    message: str
    submitted_at: str


@dataclass
class JobStatusResponse:
    job_id: str
    macworp_project_id: str
    macworp_run_id: str
    status: JobStatus
    submitted_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress_message: Optional[str] = None


@dataclass
class JobResult:
    job_id: str
    macworp_project_id: str
    macworp_run_id: str
    status: JobStatus
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    exit_code: Optional[int] = None
    output_dir: Optional[str] = None
    output_files: List[OutputFile] = field(default_factory=list)
    nextflow_log: Optional[str] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


# ──────────────────────────────────────────
# Exceções
# ──────────────────────────────────────────

class ViralFlowAPIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"ViralFlow API error {status_code}: {detail}")


class ViralFlowJobFailed(Exception):
    """Levantada quando um job termina com status FAILED."""
    def __init__(self, result: JobResult):
        self.result = result
        super().__init__(
            f"Job {result.job_id} falhou: {result.error_message or 'sem detalhes'}"
        )


# ──────────────────────────────────────────
# Cliente
# ──────────────────────────────────────────

class ViralFlowClient:
    """
    Cliente síncrono para a ViralFlow API.
    Instancie uma vez e reutilize em toda a aplicação MacWorp.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        }
        self._timeout = timeout

    # ── Utilitários ──

    def _raise_for_status(self, response: httpx.Response):
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ViralFlowAPIError(response.status_code, detail)

    # ── Endpoints ──

    def health(self) -> dict:
        """Verifica se o servidor ViralFlow está acessível."""
        with httpx.Client(timeout=self._timeout) as client:
            r = client.get(f"{self.base_url}/health", headers=self._headers)
            self._raise_for_status(r)
            return r.json()

    def submit_job(self, params: ViralFlowJobParams) -> JobSubmitResponse:
        """
        Submete um job ao ViralFlow.
        Retorna imediatamente com job_id para polling.
        """
        with httpx.Client(timeout=self._timeout) as client:
            r = client.post(
                f"{self.base_url}/jobs",
                json=params.to_dict(),
                headers=self._headers,
            )
            self._raise_for_status(r)
            data = r.json()
            return JobSubmitResponse(
                job_id=data["job_id"],
                status=JobStatus(data["status"]),
                message=data["message"],
                submitted_at=data["submitted_at"],
            )

    def get_status(self, job_id: str) -> JobStatusResponse:
        """Retorna o status atual de um job."""
        with httpx.Client(timeout=self._timeout) as client:
            r = client.get(
                f"{self.base_url}/jobs/{job_id}",
                headers=self._headers,
            )
            self._raise_for_status(r)
            data = r.json()
            return JobStatusResponse(
                job_id=data["job_id"],
                macworp_project_id=data["macworp_project_id"],
                macworp_run_id=data["macworp_run_id"],
                status=JobStatus(data["status"]),
                submitted_at=data["submitted_at"],
                started_at=data.get("started_at"),
                finished_at=data.get("finished_at"),
                progress_message=data.get("progress_message"),
            )

    def get_results(self, job_id: str) -> JobResult:
        """Busca os resultados completos de um job concluído."""
        with httpx.Client(timeout=self._timeout) as client:
            r = client.get(
                f"{self.base_url}/jobs/{job_id}/results",
                headers=self._headers,
            )
            self._raise_for_status(r)
            data = r.json()

            output_files = [
                OutputFile(
                    name=f["name"],
                    path=f["path"],
                    size_bytes=f.get("size_bytes"),
                    description=f.get("description"),
                )
                for f in data.get("output_files", [])
            ]

            return JobResult(
                job_id=data["job_id"],
                macworp_project_id=data["macworp_project_id"],
                macworp_run_id=data["macworp_run_id"],
                status=JobStatus(data["status"]),
                started_at=data.get("started_at"),
                finished_at=data.get("finished_at"),
                duration_seconds=data.get("duration_seconds"),
                exit_code=data.get("exit_code"),
                output_dir=data.get("output_dir"),
                output_files=output_files,
                nextflow_log=data.get("nextflow_log"),
                error_message=data.get("error_message"),
                metrics=data.get("metrics"),
            )

    def cancel_job(self, job_id: str):
        """Cancela um job em execução."""
        with httpx.Client(timeout=self._timeout) as client:
            r = client.delete(
                f"{self.base_url}/jobs/{job_id}",
                headers=self._headers,
            )
            self._raise_for_status(r)

    def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 15.0,
        max_wait: Optional[float] = None,
        on_status_change=None,
    ) -> JobResult:
        """
        Faz polling até o job terminar e retorna os resultados.

        Args:
            job_id: ID do job a aguardar.
            poll_interval: Segundos entre cada checagem (padrão 15s).
            max_wait: Timeout total em segundos (None = sem limite).
            on_status_change: Callback(job_id, status) chamado a cada mudança.

        Returns:
            JobResult com os dados completos.

        Raises:
            ViralFlowJobFailed: Se o job terminar com status FAILED.
            TimeoutError: Se max_wait for excedido.
        """
        start = time.monotonic()
        last_status = None

        while True:
            status_resp = self.get_status(job_id)

            if status_resp.status != last_status:
                last_status = status_resp.status
                if on_status_change:
                    on_status_change(job_id, status_resp.status)

            if status_resp.status in (
                JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED
            ):
                result = self.get_results(job_id)
                if result.status == JobStatus.FAILED:
                    raise ViralFlowJobFailed(result)
                return result

            if max_wait and (time.monotonic() - start) > max_wait:
                raise TimeoutError(
                    f"Job {job_id} não concluiu em {max_wait}s."
                )

            time.sleep(poll_interval)
