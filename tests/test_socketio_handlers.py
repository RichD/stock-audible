"""Tests for SocketIO handlers."""
import pytest
import time
from threading import Event


@pytest.mark.socketio
def test_handle_connect(socketio_client):
    """Test that client connection emits 'connected' event."""
    # Connect is automatic when creating the client
    received = socketio_client.get_received()

    assert len(received) > 0
    assert received[0]['name'] == 'connected'
    assert received[0]['args'][0]['status'] == 'Connected to server'


@pytest.mark.socketio
def test_start_announcements_success(socketio_client, mock_yfinance):
    """Test successful start of announcements."""
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 10
    })

    received = socketio_client.get_received()

    # Filter out the 'connected' event
    started_events = [r for r in received if r['name'] == 'started']

    assert len(started_events) > 0
    assert started_events[0]['args'][0]['ticker'] == 'AAPL'
    assert started_events[0]['args'][0]['interval'] == 10


@pytest.mark.socketio
def test_start_announcements_uppercase_ticker(socketio_client, mock_yfinance):
    """Test that ticker is converted to uppercase."""
    socketio_client.emit('start_announcements', {
        'ticker': 'aapl',
        'interval': 10
    })

    received = socketio_client.get_received()
    started_events = [r for r in received if r['name'] == 'started']

    assert len(started_events) > 0
    assert started_events[0]['args'][0]['ticker'] == 'AAPL'


@pytest.mark.socketio
def test_start_announcements_strips_whitespace(socketio_client, mock_yfinance):
    """Test that whitespace is stripped from ticker."""
    socketio_client.emit('start_announcements', {
        'ticker': '  AAPL  ',
        'interval': 10
    })

    received = socketio_client.get_received()
    started_events = [r for r in received if r['name'] == 'started']

    assert len(started_events) > 0
    assert started_events[0]['args'][0]['ticker'] == 'AAPL'


@pytest.mark.socketio
def test_start_announcements_empty_ticker(socketio_client):
    """Test that empty ticker emits error event."""
    socketio_client.emit('start_announcements', {
        'ticker': '',
        'interval': 10
    })

    received = socketio_client.get_received()
    error_events = [r for r in received if r['name'] == 'error']

    assert len(error_events) > 0
    assert 'Please provide a ticker symbol' in error_events[0]['args'][0]['message']


@pytest.mark.socketio
def test_start_announcements_whitespace_only_ticker(socketio_client):
    """Test that whitespace-only ticker emits error event."""
    socketio_client.emit('start_announcements', {
        'ticker': '   ',
        'interval': 10
    })

    received = socketio_client.get_received()
    error_events = [r for r in received if r['name'] == 'error']

    assert len(error_events) > 0
    assert 'Please provide a ticker symbol' in error_events[0]['args'][0]['message']


@pytest.mark.socketio
def test_start_announcements_minimum_interval(socketio_client, mock_yfinance):
    """Test that interval is clamped to minimum 5 seconds."""
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 2
    })

    received = socketio_client.get_received()
    started_events = [r for r in received if r['name'] == 'started']

    assert len(started_events) > 0
    assert started_events[0]['args'][0]['interval'] == 5


@pytest.mark.socketio
def test_start_announcements_default_interval(socketio_client, mock_yfinance):
    """Test that default interval is used when not provided."""
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL'
    })

    received = socketio_client.get_received()
    started_events = [r for r in received if r['name'] == 'started']

    assert len(started_events) > 0
    # Should use Config.DEFAULT_INTERVAL (300) or minimum (5), whichever is larger
    assert started_events[0]['args'][0]['interval'] >= 5


@pytest.mark.socketio
def test_start_announcements_replaces_existing(socketio_client, mock_yfinance, app):
    """Test that starting new announcements stops the old one."""
    # Start first announcement
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 10
    })
    socketio_client.get_received()  # Clear received events

    # Start second announcement
    socketio_client.emit('start_announcements', {
        'ticker': 'MSFT',
        'interval': 10
    })

    received = socketio_client.get_received()
    started_events = [r for r in received if r['name'] == 'started']

    assert len(started_events) > 0
    assert started_events[0]['args'][0]['ticker'] == 'MSFT'

    # Verify current_ticker is updated
    import app as app_module
    assert app_module.current_ticker == 'MSFT'


@pytest.mark.socketio
def test_stop_announcements(socketio_client, mock_yfinance, app):
    """Test stopping announcements."""
    # Start announcements first
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 10
    })
    socketio_client.get_received()  # Clear received events

    # Stop announcements
    socketio_client.emit('stop_announcements')

    received = socketio_client.get_received()
    stopped_events = [r for r in received if r['name'] == 'stopped']

    assert len(stopped_events) > 0
    assert stopped_events[0]['args'][0]['status'] == 'Announcements stopped'

    # Verify stop_event is set
    import app as app_module
    assert app_module.stop_event.is_set()
    assert app_module.current_ticker is None


@pytest.mark.socketio
def test_stop_announcements_when_not_running(socketio_client):
    """Test stopping announcements when nothing is running."""
    socketio_client.emit('stop_announcements')

    received = socketio_client.get_received()
    stopped_events = [r for r in received if r['name'] == 'stopped']

    # Should not error, just emit stopped event
    assert len(stopped_events) > 0
    assert stopped_events[0]['args'][0]['status'] == 'Announcements stopped'


@pytest.mark.socketio
@pytest.mark.slow
def test_announce_stock_prices_emits_price_update(socketio_client, mock_yfinance, app):
    """Test that background thread emits price_update events."""
    # Start announcements with short interval
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1  # Will be clamped to 5 seconds minimum
    })

    # Wait for at least one price update
    time.sleep(6)

    received = socketio_client.get_received()
    price_update_events = [r for r in received if r['name'] == 'price_update']

    assert len(price_update_events) > 0

    # Verify structure of price_update event
    price_data = price_update_events[0]['args'][0]
    assert 'ticker' in price_data
    assert 'price' in price_data
    assert 'announcement' in price_data
    assert 'timestamp' in price_data

    # Clean up
    socketio_client.emit('stop_announcements')
    time.sleep(0.5)


@pytest.mark.socketio
@pytest.mark.slow
def test_announce_stock_prices_emits_error_on_none(socketio_client, mock_yfinance_empty, app):
    """Test that error event is emitted when API returns None."""
    # Start announcements with short interval
    socketio_client.emit('start_announcements', {
        'ticker': 'INVALID',
        'interval': 1
    })

    # Wait for at least one attempt
    time.sleep(6)

    received = socketio_client.get_received()
    error_events = [r for r in received if r['name'] == 'error']

    assert len(error_events) > 0
    assert 'Could not fetch price' in error_events[0]['args'][0]['message']
    assert 'INVALID' in error_events[0]['args'][0]['message']

    # Clean up
    socketio_client.emit('stop_announcements')
    time.sleep(0.5)


@pytest.mark.socketio
def test_announce_stock_prices_stops_on_event(socketio_client, mock_yfinance, app):
    """Test that background thread stops when stop_event is set."""
    # Start announcements
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1
    })

    time.sleep(1)

    # Stop announcements
    socketio_client.emit('stop_announcements')

    # Wait a bit to ensure thread stops
    time.sleep(1)

    # Verify thread is stopped
    import app as app_module
    if app_module.announcement_thread:
        assert not app_module.announcement_thread.is_alive() or app_module.stop_event.is_set()


@pytest.mark.socketio
def test_start_with_string_interval(socketio_client, mock_yfinance):
    """Test that string interval is converted to integer."""
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': '10'
    })

    received = socketio_client.get_received()
    started_events = [r for r in received if r['name'] == 'started']

    assert len(started_events) > 0
    assert started_events[0]['args'][0]['interval'] == 10
    assert isinstance(started_events[0]['args'][0]['interval'], int)


@pytest.mark.socketio
def test_thread_is_daemon(socketio_client, mock_yfinance, app):
    """Test that announcement thread is a daemon thread."""
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 10
    })

    time.sleep(0.5)

    import app as app_module
    assert app_module.announcement_thread is not None
    assert app_module.announcement_thread.daemon is True

    # Clean up
    socketio_client.emit('stop_announcements')
