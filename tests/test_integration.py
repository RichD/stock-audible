"""Integration tests for end-to-end functionality."""
import pytest
import time


@pytest.mark.integration
@pytest.mark.slow
def test_full_announcement_flow(socketio_client, mock_yfinance, app):
    """Test complete flow: connect → start → updates → stop."""
    # Step 1: Connect (automatic)
    received = socketio_client.get_received()
    connected_events = [r for r in received if r['name'] == 'connected']
    assert len(connected_events) > 0

    # Step 2: Start announcements
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1
    })

    received = socketio_client.get_received()
    started_events = [r for r in received if r['name'] == 'started']
    assert len(started_events) > 0
    assert started_events[0]['args'][0]['ticker'] == 'AAPL'

    # Step 3: Wait for price updates
    time.sleep(6)
    received = socketio_client.get_received()
    price_update_events = [r for r in received if r['name'] == 'price_update']
    assert len(price_update_events) > 0

    # Step 4: Stop announcements
    socketio_client.emit('stop_announcements')
    received = socketio_client.get_received()
    stopped_events = [r for r in received if r['name'] == 'stopped']
    assert len(stopped_events) > 0

    # Verify no more updates after stopping
    time.sleep(2)
    old_count = len(price_update_events)
    received = socketio_client.get_received()
    new_price_updates = [r for r in received if r['name'] == 'price_update']

    # Allow for at most one more update (due to timing)
    assert len(new_price_updates) <= 1


@pytest.mark.integration
@pytest.mark.slow
def test_multiple_clients_receive_same_updates(app, mock_yfinance):
    """Test that multiple clients receive the same price updates."""
    from app import socketio

    # Create two separate clients
    client1 = socketio.test_client(app)
    client2 = socketio.test_client(app)

    # Client 1 starts announcements
    client1.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1
    })

    # Wait for price updates
    time.sleep(6)

    # Both clients should receive updates
    received1 = client1.get_received()
    received2 = client2.get_received()

    price_updates1 = [r for r in received1 if r['name'] == 'price_update']
    price_updates2 = [r for r in received2 if r['name'] == 'price_update']

    assert len(price_updates1) > 0
    assert len(price_updates2) > 0

    # Both should have the same ticker
    assert price_updates1[0]['args'][0]['ticker'] == 'AAPL'
    assert price_updates2[0]['args'][0]['ticker'] == 'AAPL'

    # Clean up
    client1.emit('stop_announcements')
    time.sleep(0.5)

    client1.disconnect()
    client2.disconnect()


@pytest.mark.integration
@pytest.mark.slow
def test_changing_ticker_mid_stream(socketio_client, mock_yfinance, app):
    """Test changing ticker while announcements are running."""
    # Start with AAPL
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1
    })

    time.sleep(3)

    # Get initial updates
    received = socketio_client.get_received()
    price_updates = [r for r in received if r['name'] == 'price_update']
    assert len(price_updates) > 0
    assert all(r['args'][0]['ticker'] == 'AAPL' for r in price_updates)

    # Change to MSFT
    socketio_client.emit('start_announcements', {
        'ticker': 'MSFT',
        'interval': 1
    })

    time.sleep(3)

    # Get new updates
    received = socketio_client.get_received()
    new_price_updates = [r for r in received if r['name'] == 'price_update']

    # Should have MSFT updates now
    if len(new_price_updates) > 0:
        # At least one should be MSFT
        msft_updates = [r for r in new_price_updates if r['args'][0]['ticker'] == 'MSFT']
        assert len(msft_updates) > 0

    # Verify current_ticker is MSFT
    import app as app_module
    assert app_module.current_ticker == 'MSFT'

    # Clean up
    socketio_client.emit('stop_announcements')
    time.sleep(0.5)


@pytest.mark.integration
@pytest.mark.slow
def test_api_failure_recovery(socketio_client, mocker, app):
    """Test recovery when API fails first then succeeds."""
    call_count = {'count': 0}

    def mock_get_price(ticker):
        call_count['count'] += 1
        if call_count['count'] == 1:
            # First call fails
            return None
        else:
            # Subsequent calls succeed
            return {
                'ticker': ticker.upper(),
                'price': 150.25,
                'currency': 'USD'
            }

    # Mock the stock service method
    import app as app_module
    mocker.patch.object(app_module.stock_service, 'get_current_price', side_effect=mock_get_price)
    mocker.patch.object(app_module.stock_service, 'format_announcement', return_value='A P P L. 150.25')

    # Start announcements
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1
    })

    # Wait for multiple attempts
    time.sleep(8)

    received = socketio_client.get_received()

    # Should have at least one error event (from first call)
    error_events = [r for r in received if r['name'] == 'error']
    assert len(error_events) > 0

    # Should have at least one successful price_update (from subsequent calls)
    price_update_events = [r for r in received if r['name'] == 'price_update']
    assert len(price_update_events) > 0

    # Clean up
    socketio_client.emit('stop_announcements')
    time.sleep(0.5)


@pytest.mark.integration
def test_concurrent_start_stop_operations(socketio_client, mock_yfinance, app):
    """Test rapid start/stop operations don't cause race conditions."""
    # Rapidly start and stop multiple times
    for i in range(5):
        socketio_client.emit('start_announcements', {
            'ticker': 'AAPL',
            'interval': 10
        })
        time.sleep(0.1)

        socketio_client.emit('stop_announcements')
        time.sleep(0.1)

    # Final state should be stopped
    import app as app_module
    assert app_module.stop_event.is_set()
    assert app_module.current_ticker is None

    # Should not crash and should have received events
    received = socketio_client.get_received()
    assert len(received) > 0


@pytest.mark.integration
def test_app_and_socketio_integration(client, socketio_client):
    """Test that Flask app and SocketIO work together."""
    # HTTP request works
    response = client.get('/')
    assert response.status_code == 200

    # WebSocket connection works
    received = socketio_client.get_received()
    connected_events = [r for r in received if r['name'] == 'connected']
    assert len(connected_events) > 0


@pytest.mark.integration
def test_stock_service_integration_with_app(socketio_client, app, mock_yfinance):
    """Test that stock service integrates properly with the app."""
    from app import stock_service

    # Stock service can fetch data
    data = stock_service.get_current_price('AAPL')
    assert data is not None
    assert data['ticker'] == 'AAPL'

    # Stock service can format announcements
    announcement = stock_service.format_announcement(data)
    assert 'A A P L' in announcement

    # App uses stock service for announcements
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1
    })

    time.sleep(6)

    received = socketio_client.get_received()
    price_updates = [r for r in received if r['name'] == 'price_update']

    if len(price_updates) > 0:
        assert price_updates[0]['args'][0]['ticker'] == 'AAPL'
        assert 'announcement' in price_updates[0]['args'][0]

    # Clean up
    socketio_client.emit('stop_announcements')
    time.sleep(0.5)


@pytest.mark.integration
@pytest.mark.slow
def test_long_running_announcements(socketio_client, mock_yfinance, app):
    """Test that announcements can run for extended period."""
    socketio_client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 2
    })

    # Run for longer period
    time.sleep(12)

    received = socketio_client.get_received()
    price_updates = [r for r in received if r['name'] == 'price_update']

    # Should have multiple updates
    assert len(price_updates) >= 2

    # All updates should be valid
    for update in price_updates:
        assert 'ticker' in update['args'][0]
        assert 'price' in update['args'][0]
        assert 'announcement' in update['args'][0]
        assert 'timestamp' in update['args'][0]

    # Clean up
    socketio_client.emit('stop_announcements')
    time.sleep(0.5)


@pytest.mark.integration
def test_disconnect_during_announcements(app, mock_yfinance):
    """Test that disconnecting client doesn't crash server."""
    from app import socketio

    client = socketio.test_client(app)

    # Start announcements
    client.emit('start_announcements', {
        'ticker': 'AAPL',
        'interval': 1
    })

    time.sleep(2)

    # Disconnect abruptly
    client.disconnect()

    # Server should still be running (implicit - if we crash, test fails)
    time.sleep(2)

    # Create new client to verify server is still working
    client2 = socketio.test_client(app)
    received = client2.get_received()
    connected_events = [r for r in received if r['name'] == 'connected']
    assert len(connected_events) > 0

    client2.disconnect()

    # Clean up background thread
    import app as app_module
    app_module.stop_event.set()
    time.sleep(0.5)
