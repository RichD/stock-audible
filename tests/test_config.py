"""Tests for config module."""
import pytest
import os
import importlib


@pytest.mark.unit
def test_default_config_values(mocker, monkeypatch):
    """Test that default values are used when env vars not set."""
    # Mock load_dotenv before importing config
    mocker.patch('dotenv.load_dotenv', return_value=None)

    # Remove any existing environment variables
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.delenv('FLASK_ENV', raising=False)
    monkeypatch.delenv('DEFAULT_INTERVAL', raising=False)

    # Reload config to pick up changes
    import config
    importlib.reload(config)

    assert config.Config.SECRET_KEY == 'dev-secret-key-change-in-production'
    assert config.Config.DEFAULT_INTERVAL == 300
    assert config.Config.DEBUG is False


@pytest.mark.unit
def test_config_from_environment(monkeypatch):
    """Test that config reads values from environment variables."""
    monkeypatch.setenv('SECRET_KEY', 'test-secret-key')
    monkeypatch.setenv('FLASK_ENV', 'development')
    monkeypatch.setenv('DEFAULT_INTERVAL', '60')

    # Reload config to pick up changes
    import config
    importlib.reload(config)

    assert config.Config.SECRET_KEY == 'test-secret-key'
    assert config.Config.DEFAULT_INTERVAL == 60
    assert config.Config.DEBUG is True


@pytest.mark.unit
def test_debug_mode_development(monkeypatch):
    """Test that DEBUG is True when FLASK_ENV is development."""
    monkeypatch.setenv('FLASK_ENV', 'development')

    # Reload config to pick up changes
    import config
    importlib.reload(config)

    assert config.Config.DEBUG is True


@pytest.mark.unit
def test_debug_mode_production(monkeypatch):
    """Test that DEBUG is False when FLASK_ENV is production."""
    monkeypatch.setenv('FLASK_ENV', 'production')

    # Reload config to pick up changes
    import config
    importlib.reload(config)

    assert config.Config.DEBUG is False


@pytest.mark.unit
def test_debug_mode_not_set(mocker, monkeypatch):
    """Test that DEBUG is False when FLASK_ENV is not set."""
    # Mock load_dotenv to prevent loading .env file
    mocker.patch('dotenv.load_dotenv', return_value=None)

    monkeypatch.delenv('FLASK_ENV', raising=False)

    # Reload config to pick up changes
    import config
    importlib.reload(config)

    assert config.Config.DEBUG is False


@pytest.mark.unit
def test_interval_type_conversion(monkeypatch):
    """Test that DEFAULT_INTERVAL is converted to integer."""
    monkeypatch.setenv('DEFAULT_INTERVAL', '120')

    # Reload config to pick up changes
    import config
    importlib.reload(config)

    assert config.Config.DEFAULT_INTERVAL == 120
    assert isinstance(config.Config.DEFAULT_INTERVAL, int)


@pytest.mark.unit
def test_custom_secret_key(monkeypatch):
    """Test that custom SECRET_KEY can be set."""
    custom_key = 'my-super-secret-production-key'
    monkeypatch.setenv('SECRET_KEY', custom_key)

    # Reload config to pick up changes
    import config
    importlib.reload(config)

    assert config.Config.SECRET_KEY == custom_key


@pytest.mark.unit
def test_interval_different_values(monkeypatch):
    """Test various interval values."""
    test_intervals = ['5', '30', '60', '300', '600']

    for interval_str in test_intervals:
        monkeypatch.setenv('DEFAULT_INTERVAL', interval_str)

        # Reload config to pick up changes
        import config
        importlib.reload(config)

        assert config.Config.DEFAULT_INTERVAL == int(interval_str)
