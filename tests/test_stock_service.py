"""Tests for stock_service module."""
import pytest
from stock_service import StockService


@pytest.fixture
def stock_service():
    """Create StockService instance."""
    return StockService()


@pytest.mark.unit
def test_get_current_price_success_current_price(stock_service, mock_yfinance):
    """Test successful price fetch with currentPrice field."""
    result = stock_service.get_current_price('AAPL')

    assert result is not None
    assert result['ticker'] == 'AAPL'
    assert result['price'] == 150.25
    assert result['currency'] == 'USD'


@pytest.mark.unit
def test_get_current_price_success_regular_market_price(stock_service, mock_yfinance_regular_market):
    """Test successful price fetch with regularMarketPrice fallback."""
    result = stock_service.get_current_price('MSFT')

    assert result is not None
    assert result['ticker'] == 'MSFT'
    assert result['price'] == 250.50
    assert result['currency'] == 'USD'


@pytest.mark.unit
def test_get_current_price_success_from_history(stock_service, mock_yfinance_history_only):
    """Test successful price fetch from historical data."""
    result = stock_service.get_current_price('GOOGL')

    assert result is not None
    assert result['ticker'] == 'GOOGL'
    assert result['price'] == 110.25  # Last value from Close prices
    assert result['currency'] == 'USD'


@pytest.mark.unit
def test_get_current_price_empty_history(stock_service, mock_yfinance_empty):
    """Test get_current_price returns None when no data available."""
    result = stock_service.get_current_price('INVALID')

    assert result is None


@pytest.mark.unit
def test_get_current_price_api_exception(stock_service, mocker, capsys):
    """Test get_current_price returns None on API exception."""
    # Create a more complete mock that raises exception on .info access
    mock_ticker = mocker.MagicMock()
    type(mock_ticker).info = mocker.PropertyMock(side_effect=Exception("API Error"))

    mocker.patch('stock_service.yf.Ticker', return_value=mock_ticker)

    result = stock_service.get_current_price('FAIL')

    assert result is None

    # Verify error was printed
    captured = capsys.readouterr()
    assert 'Error fetching' in captured.out


@pytest.mark.unit
def test_get_current_price_ticker_case_insensitive(stock_service, mock_yfinance):
    """Test that ticker is normalized to uppercase."""
    result = stock_service.get_current_price('aapl')

    assert result is not None
    assert result['ticker'] == 'AAPL'


@pytest.mark.unit
def test_get_current_price_uppercase_ticker(stock_service, mock_yfinance):
    """Test that uppercase ticker is preserved."""
    result = stock_service.get_current_price('AAPL')

    assert result is not None
    assert result['ticker'] == 'AAPL'


@pytest.mark.unit
def test_get_current_price_mixed_case_ticker(stock_service, mock_yfinance):
    """Test that mixed case ticker is normalized to uppercase."""
    result = stock_service.get_current_price('AaPl')

    assert result is not None
    assert result['ticker'] == 'AAPL'


@pytest.mark.unit
def test_get_current_price_rounds_to_two_decimals(stock_service, mocker):
    """Test that price is rounded to 2 decimal places."""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        'currentPrice': 150.25678,
        'currency': 'USD'
    }
    import pandas as pd
    mock_ticker.history.return_value = pd.DataFrame()
    mocker.patch('stock_service.yf.Ticker', return_value=mock_ticker)

    result = stock_service.get_current_price('AAPL')

    assert result is not None
    assert result['price'] == 150.26


@pytest.mark.unit
def test_format_announcement_standard(stock_service):
    """Test format_announcement with standard multi-letter ticker."""
    data = {'ticker': 'AAPL', 'price': 150.25}
    result = stock_service.format_announcement(data)

    assert result == 'A A P L. 150.25'


@pytest.mark.unit
def test_format_announcement_multi_letter_ticker(stock_service):
    """Test format_announcement with different ticker."""
    data = {'ticker': 'MSFT', 'price': 350.50}
    result = stock_service.format_announcement(data)

    assert result == 'M S F T. 350.5'


@pytest.mark.unit
def test_format_announcement_single_letter(stock_service):
    """Test format_announcement with single letter ticker."""
    data = {'ticker': 'F', 'price': 12.34}
    result = stock_service.format_announcement(data)

    assert result == 'F. 12.34'


@pytest.mark.unit
def test_format_announcement_index_with_caret(stock_service):
    """Test format_announcement with index ticker (^GSPC)."""
    data = {'ticker': '^GSPC', 'price': 4500.00}
    result = stock_service.format_announcement(data)

    assert result == '^ G S P C. 4500.0'


@pytest.mark.unit
def test_format_announcement_long_ticker(stock_service):
    """Test format_announcement with longer ticker."""
    data = {'ticker': 'GOOGL', 'price': 2500.75}
    result = stock_service.format_announcement(data)

    assert result == 'G O O G L. 2500.75'


@pytest.mark.unit
def test_format_announcement_preserves_decimals(stock_service):
    """Test that format_announcement preserves decimal values."""
    data = {'ticker': 'AAPL', 'price': 150.1}
    result = stock_service.format_announcement(data)

    assert result == 'A A P L. 150.1'


@pytest.mark.unit
def test_format_announcement_integer_price(stock_service):
    """Test format_announcement with integer price."""
    data = {'ticker': 'AAPL', 'price': 150}
    result = stock_service.format_announcement(data)

    assert result == 'A A P L. 150'


@pytest.mark.unit
def test_format_announcement_with_currency_ignored(stock_service):
    """Test that currency in data doesn't affect announcement format."""
    data = {'ticker': 'AAPL', 'price': 150.25, 'currency': 'USD'}
    result = stock_service.format_announcement(data)

    assert result == 'A A P L. 150.25'
    assert 'USD' not in result
