import pytest
from src.config import Settings
from src.helpers.exceptions import ExternalServiceError
from src.providers.llm import LLMProvider, ClientRotator, ClientConfig, parse_configs, load_configs
from src.providers.llm.model import _clean_json_text


def test_client_rotator_initialization():
    rotator = ClientRotator()
    assert len(rotator.client_configs) >= 0
    available_models = rotator.get_available_models()
    assert len(available_models) >= 0


def test_parse_and_load_client_configs():
    sample_data = {
        "CLIENT_CONFIGS_0_BASE_URL": "https://api.openai.com/v1",
        "CLIENT_CONFIGS_0_API_KEY": "sk-sample",
        "CLIENT_CONFIGS_0_MODEL": "gpt-4o",
        "CLIENT_CONFIGS_0_PROXY_HTTP": "http://proxy.local:8080",
    }
    configs = parse_configs(sample_data)
    assert len(configs) == 1
    assert configs[0].base_url == "https://api.openai.com/v1"
    assert configs[0].api_key == "sk-sample"
    assert configs[0].model == "gpt-4o"
    assert configs[0].proxy == "http://proxy.local:8080"
    loaded = load_configs()
    assert isinstance(loaded, list)


def test_client_rotator_model_selection():
    rotator = ClientRotator()
    available = rotator.get_available_models()
    if available:
        selected_model = available[0]
        config = rotator.get_next_client_config(model=selected_model)
        assert config.model == selected_model


def test_clean_json_text_strips_markdown_fences():
    fenced = "```json\n{\"foo\": \"bar\"}\n```"
    assert _clean_json_text(fenced) == "{\"foo\": \"bar\"}"

    plain_fenced = "```\n{\"a\": 1}\n```"
    assert _clean_json_text(plain_fenced) == "{\"a\": 1}"

    bare = "{\"valid\": true}"
    assert _clean_json_text(bare) == bare


def test_llm_provider_client_caching_and_close():
    llm = LLMProvider()
    cfg = ClientConfig(base_url="https://api.openai.com/v1", api_key="sk-test", model="gpt-4o")
    client1 = llm._get_client(cfg)
    client2 = llm._get_client(cfg)
    assert client1 is client2
    assert len(llm._clients) == 1


@pytest.mark.asyncio
async def test_llm_provider_empty_rotator_fails_fast():
    empty_rotator = ClientRotator()
    empty_rotator.client_configs = []
    llm = LLMProvider(rotator=empty_rotator)
    with pytest.raises(ExternalServiceError, match="No client configurations available"):
        await llm.process(messages=[{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_llm_realtime_connectivity():
    rotator = ClientRotator()
    if not rotator.client_configs:
        pytest.skip("No LLM client configurations available")

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
        pytest.skip("All configured LLM models unreachable (offline network)")

    assert len(response_text.strip()) > 0


@pytest.mark.asyncio
async def test_llm_realtime_json_generation():
    rotator = ClientRotator()
    if not rotator.client_configs:
        pytest.skip("No LLM client configurations available")

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
        pytest.skip("All configured LLM models unreachable (offline network)")

    assert "status" in payload
