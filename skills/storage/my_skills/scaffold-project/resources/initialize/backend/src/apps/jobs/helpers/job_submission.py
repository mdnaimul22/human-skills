from __future__ import annotations
import asyncio
import hashlib
import json
import urllib.parse
from typing import Awaitable, Callable, Optional
from src.config import Settings, setup_logger
from src.helpers import get_redis
from src.schema import JobStatus
from .job_control import JobControl
from .job_journal import JobRecord
from .job_worker import JobWorker

logger = setup_logger(Settings.LOG_DIR / "jobs.log", name="jobs.submission")

def compute_canonical_job_hash(
    service_type: str,
    target: str,
    params: Optional[dict] = None,
) -> str:
    cleaned = target.strip()
    parsed = urllib.parse.urlparse(cleaned)
    if parsed.scheme and parsed.netloc:
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        query = sorted(urllib.parse.parse_qsl(parsed.query))
        encoded_query = f"?{urllib.parse.urlencode(query)}" if query else ""
        canonical_target = f"{parsed.scheme.lower()}://{netloc}{path}{encoded_query}"
    else:
        canonical_target = cleaned

    sorted_params = json.dumps(params or {}, sort_keys=True)
    raw = f"{service_type}|{canonical_target}|{sorted_params}"
    return hashlib.sha256(raw.encode()).hexdigest()

def resolve_stream_lane(tier: Optional[str] = None) -> str:
    clean_tier = (tier or "").lower().strip()
    if clean_tier in ("premium", "registered"):
        return f"jobs:stream:{clean_tier}"
    return "jobs:stream:guest"

class JobSubmission:
    def __init__(
        self,
        jobs_registry: dict[str, JobRecord],
        control: JobControl,
        worker: JobWorker,
    ) -> None:
        self._jobs = jobs_registry
        self.control = control
        self.worker = worker

    def find_duplicate(self, content_hash: str) -> Optional[JobRecord]:
        existing_id = self.control.dedup_index.get(content_hash)
        if existing_id:
            job = self._jobs.get(existing_id)
            if job and not job.is_terminal:
                logger.info(f"Job dedup hit: {content_hash[:16]}... -> {existing_id}")
                return job
            self.control.dedup_index.pop(content_hash, None)
        return None

    async def _resolve_owner_record(
        self,
        owner_id: str,
        service_type: str,
        client_ip: str,
        user_id: Optional[str],
        content_hash: str,
    ) -> JobRecord:
        async with self.control.lock:
            existing_job = self._jobs.get(owner_id)
            if existing_job and not existing_job.is_terminal:
                logger.info(f"Redis dedup hit: {content_hash[:16]}... -> {owner_id}")
                return existing_job

        redis = get_redis()
        cached = await redis.get_state(owner_id)
        owner_tier = "guest"
        proxy_job = JobRecord(owner_id, service_type, client_ip, user_id=user_id)
        if cached:
            try:
                parsed = json.loads(cached)
                owner_tier = str(parsed.get("tier", "guest"))
                proxy_job.status = JobStatus(parsed.get("status", "processing"))
                proxy_job.progress = int(parsed.get("progress", 0))
            except (json.JSONDecodeError, ValueError, KeyError):
                proxy_job.update(1, "Processing", JobStatus.PROCESSING)
        else:
            proxy_job.update(1, "Processing", JobStatus.PROCESSING)
        proxy_job.tier = owner_tier
        if proxy_job.metadata is None:
            proxy_job.metadata = {}
        proxy_job.metadata["tier"] = owner_tier

        async with self.control.lock:
            if owner_id in self._jobs:
                return self._jobs[owner_id]
            self._jobs[owner_id] = proxy_job
        return proxy_job

    async def submit(
        self,
        job_id: str,
        service_type: str,
        client_ip: str,
        executor: Callable[..., Awaitable[str]],
        *args,
        needs_encode: bool = False,
        workload_type: Optional[str] = None,
        user_id: Optional[str] = None,
        content_hash: Optional[str] = None,
        url: Optional[str] = None,
        params: Optional[dict] = None,
        tier: Optional[str] = None,
        timeout: float = 30.0,
        **kwargs,
    ) -> JobRecord:
        job = JobRecord(job_id, service_type, client_ip, user_id=user_id, tier=tier)

        effective_hash = content_hash
        if not effective_hash and url:
            effective_hash = compute_canonical_job_hash(service_type, url, params)

        if effective_hash:
            existing = self.find_duplicate(effective_hash)
            if existing:
                return existing
            redis = get_redis()
            if redis.is_available:
                acquired, owner_id = await redis.acquire_dedup(
                    f"job:dedup:{effective_hash}", job_id, ex=600
                )
                if not acquired and owner_id:
                    return await self._resolve_owner_record(
                        owner_id, service_type, client_ip, user_id, effective_hash
                    )

        self.control.check_capacity(client_ip, user_id=user_id, tier=tier)

        async with self.control.lock:
            if effective_hash and job_id not in self._jobs:
                existing = self.find_duplicate(effective_hash)
                if existing:
                    return existing
            self._jobs[job_id] = job
            self.control.record_active_job(client_ip, effective_hash, job_id, user_id=user_id)

        lane = resolve_stream_lane(tier)
        job.update(0, "Queued", JobStatus.QUEUED)
        logger.info(f"[{job_id}] Queued: {service_type} from {client_ip} (lane: {lane})")

        asyncio.create_task(
            self.worker.execute_job(
                job,
                executor,
                args,
                kwargs,
                needs_encode=needs_encode,
                content_hash=effective_hash,
                workload_type=workload_type,
                timeout=timeout,
            )
        )
        return job
