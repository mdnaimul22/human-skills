import pytest
from src.apps.jobs.helpers.job_control import JobControl
from src.helpers import ExternalServiceError, RateLimitError
from src.apps.system import SystemManager

@pytest.fixture(autouse=True)
def clean_system() -> None:
    SystemManager.reset_instance()
    yield
    SystemManager.reset_instance()

@pytest.mark.asyncio
async def test_job_control_acquire_and_release_resource_token() -> None:
    control = JobControl(SystemManager.get_instance())
    assert control.active_tokens == 0

    lease = await control.acquire_resource_token(workload_type="encode", job_id="job_ctrl_1", timeout=5.0)
    assert lease is not None
    assert lease.workload_type == "encode"
    assert control.active_tokens == 1

    await control.release_resource_token("job_ctrl_1")
    assert control.active_tokens == 0

@pytest.mark.asyncio
async def test_job_control_reap_expired_tokens() -> None:
    control = JobControl(SystemManager.get_instance())
    lease = await control.acquire_resource_token(workload_type="download", job_id="job_exp_1", timeout=5.0)
    assert lease is not None
    assert control.active_tokens == 1

    control._active_tokens["job_exp_1"] = 0.0
    reaped = await control.reap_expired_tokens(ttl=1.0)
    assert "job_exp_1" in reaped
    assert control.active_tokens == 0

def test_job_control_check_capacity_ip_limit() -> None:
    control = JobControl(SystemManager.get_instance())
    client_ip = "192.168.1.100"
    control.ip_active[client_ip] = 50

    with pytest.raises(RateLimitError):
        control.check_capacity(client_ip)

@pytest.mark.asyncio
async def test_job_control_registration_and_release_lifecycle() -> None:
    control = JobControl(SystemManager.get_instance())
    client_ip = "10.0.0.1"
    user_id = "usr_123"
    content_hash = "hash_abc"
    job_id = "job_reg_1"

    await control.register_submission(client_ip, content_hash, job_id, user_id=user_id)
    assert control.ip_active[client_ip] == 1
    assert control.user_active[user_id] == 1
    assert control.dedup_index[content_hash] == job_id

    await control.release_job(client_ip, content_hash, job_id=job_id, user_id=user_id)
    assert control.ip_active[client_ip] == 0
    assert control.user_active[user_id] == 0
    assert content_hash not in control.dedup_index

def test_job_control_strictly_requires_system_manager() -> None:
    with pytest.raises(ExternalServiceError):
        JobControl(None)
