import pytest
from src.config import Settings
from src.providers.llm import LLMProvider, ClientRotator


def test_client_rotator_initialization():
    rotator = ClientRotator()
    assert len(rotator.client_configs) == len(Settings.LLM_CLIENTS)
    available_models = rotator.get_available_models()
    assert len(available_models) >= 0


def test_client_rotator_model_selection():
    rotator = ClientRotator()
    available = rotator.get_available_models()
    if available:
        selected_model = available[0]
        config = rotator.get_next_client_config(model=selected_model)
        assert config.model == selected_model


@pytest.mark.asyncio
async def test_llm_realtime_connectivity():
    if not Settings.LLM_CLIENTS:
        pytest.skip("No LLM client configurations available in settings")

    llm = LLMProvider()
    working_model = None
    response_text = ""

    for client_cfg in llm.rotator.client_configs:
        try:
            response_text = await llm.process(
                messages=[{"role": "user", "content": "Respond with the word: pong"}],
                model=client_cfg.model,
            )
            working_model = client_cfg.model
            break
        except Exception:
            continue

    if not working_model:
        pytest.fail("All configured LLM models failed connectivity check")

    assert len(response_text.strip()) > 0


@pytest.mark.asyncio
async def test_llm_realtime_json_generation():
    if not Settings.LLM_CLIENTS:
        pytest.skip("No LLM client configurations available in settings")

    llm = LLMProvider()
    working_model = None
    payload: dict = {}

    for client_cfg in llm.rotator.client_configs:
        try:
            payload = await llm.generate_json(
                messages=[
                    {
                        "role": "user",
                        "content": 'Respond strictly with valid JSON without markdown wrapping: {"status": "ok", "message": "ready"}',
                    }
                ],
                model=client_cfg.model,
            )
            working_model = client_cfg.model
            break
        except Exception:
            continue

    if not working_model:
        pytest.fail("All configured LLM models failed JSON generation check")

    assert "status" in payload
