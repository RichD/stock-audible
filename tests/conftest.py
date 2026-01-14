"""Shared test fixtures for all tests."""
import pytest
import pandas as pd
from unittest.mock import MagicMock


@pytest.fixture
def app():
    """Create Flask app for testing."""
    # Import app here to avoid issues with module-level imports
    from app import app, socketio, stop_event
    import app as app_module

    # Configure app for testing
    app.config['TESTING'] = True

    # Reset global state before each test
    app_module.announcement_thread = None
    app_module.stop_event.clear()
    app_module.current_ticker = None
    app_module.current_interval = app.config.get('DEFAULT_INTERVAL', 300)

    yield app

    # Cleanup: stop any running threads
    if app_module.announcement_thread and app_module.announcement_thread.is_alive():
        app_module.stop_event.set()
        app_module.announcement_thread.join(timeout=2)


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    """SocketIO test client."""
    from app import socketio
    return socketio.test_client(app)


@pytest.fixture
def mock_yfinance(mocker):
    """Mock yfinance Ticker with successful response."""
    mock_ticker = MagicMock()
    mock_ticker.info = {
        'currentPrice': 150.25,
        'currency': 'USD'
    }
    mock_ticker.history.return_value = pd.DataFrame()

    mocker.patch('stock_service.yf.Ticker', return_value=mock_ticker)
    return mock_ticker


@pytest.fixture
def mock_yfinance_regular_market(mocker):
    """Mock yfinance Ticker with regularMarketPrice only."""
    mock_ticker = MagicMock()
    mock_ticker.info = {
        'regularMarketPrice': 250.50,
        'currency': 'USD'
    }
    mock_ticker.history.return_value = pd.DataFrame()

    mocker.patch('stock_service.yf.Ticker', return_value=mock_ticker)
    return mock_ticker


@pytest.fixture
def mock_yfinance_history_only(mocker):
    """Mock yfinance Ticker with history data only."""
    mock_ticker = MagicMock()
    mock_ticker.info = {'currency': 'USD'}

    # Create a DataFrame with Close prices
    hist_data = pd.DataFrame({
        'Close': [100.0, 105.0, 110.25]
    })
    mock_ticker.history.return_value = hist_data

    mocker.patch('stock_service.yf.Ticker', return_value=mock_ticker)
    return mock_ticker


@pytest.fixture
def mock_yfinance_empty(mocker):
    """Mock yfinance Ticker with no price data."""
    mock_ticker = MagicMock()
    mock_ticker.info = {}
    mock_ticker.history.return_value = pd.DataFrame()

    mocker.patch('stock_service.yf.Ticker', return_value=mock_ticker)
    return mock_ticker


@pytest.fixture
def mock_yfinance_failure(mocker):
    """Mock yfinance Ticker that raises an exception."""
    mock_ticker = MagicMock()
    mock_ticker.info.side_effect = Exception("API Error")

    mocker.patch('stock_service.yf.Ticker', return_value=mock_ticker)
    return mock_ticker


@pytest.fixture
def sample_stock_data():
    """Sample stock data for testing."""
    return {
        'ticker': 'AAPL',
        'price': 150.25,
        'currency': 'USD'
    }


@pytest.fixture
def sample_stock_data_multiple():
    """Multiple sample stock data for testing."""
    return [
        {'ticker': 'AAPL', 'price': 150.25, 'currency': 'USD'},
        {'ticker': 'MSFT', 'price': 350.50, 'currency': 'USD'},
        {'ticker': 'GOOGL', 'price': 2500.75, 'currency': 'USD'},
    ]


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)

    return _set_env
