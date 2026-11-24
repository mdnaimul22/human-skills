from src.config.settings import Settings


def test_settings_default_values_and_paths() -> None:
    assert Settings.PROJECT_NAME == "MyProject"
    assert type(Settings).model_fields["API_PORT"].default == 8000
    assert Settings.LOG_DIR.exists()
    assert Settings.DATA_DIR.exists()


def test_settings_environment_properties() -> None:
    settings_cls = type(Settings)
    prod_instance = settings_cls(APP_ENV="production")
    assert prod_instance.is_production is True
    assert prod_instance.is_development is False

    dev_instance = settings_cls(APP_ENV="development")
    assert dev_instance.is_production is False
    assert dev_instance.is_development is True


def test_settings_obfuscated_env_file_paths() -> None:
    env_files = Settings.model_config.get("env_file", ())
    as_strs = [str(f) for f in env_files]
    assert all("/env/" in f for f in as_strs)
    assert any("env/.1e2n3v3" in f for f in as_strs)
    assert any("env/.1y2s3t4e5m" in f for f in as_strs)
    assert any("env/.1g2i3t4s5y6n7c" in f for f in as_strs)
    assert any("env/.1m2o3d4e5l3s" in f for f in as_strs)
    assert any("env/.1t2u3n4n5e6l7" in f for f in as_strs)
    assert any("env/.1p2r3o4x5y6" in f for f in as_strs)
    assert not any(f.endswith("/.env") for f in as_strs)
    assert not any(f.endswith("/.models") for f in as_strs)
