"""Tests for Flask application routes."""
import pytest


@pytest.mark.unit
def test_index_route_returns_200(client):
    """Test that index route returns 200 status code."""
    response = client.get('/')

    assert response.status_code == 200


@pytest.mark.unit
def test_index_route_returns_html(client):
    """Test that index route returns HTML content."""
    response = client.get('/')

    assert response.content_type == 'text/html; charset=utf-8'


@pytest.mark.unit
def test_index_route_renders_template(client):
    """Test that index route renders the correct template with expected content."""
    response = client.get('/')

    # Check for key elements in the rendered HTML
    assert b'Stock Ticker Audio Announcer' in response.data
    assert b'ticker' in response.data.lower()
    assert b'interval' in response.data.lower()


@pytest.mark.unit
def test_index_route_includes_default_interval(client, app):
    """Test that template receives default_interval value."""
    response = client.get('/')

    # The default interval should be present in the response
    # (it's passed to the template and used in JavaScript)
    assert response.status_code == 200

    # Check if the default interval value appears in the page
    from config import Config
    default_interval = str(Config.DEFAULT_INTERVAL)
    assert default_interval.encode() in response.data


@pytest.mark.unit
def test_app_config_loaded(app):
    """Test that app configuration is properly loaded."""
    assert app.config is not None
    assert 'SECRET_KEY' in app.config or hasattr(app.config, 'SECRET_KEY')


@pytest.mark.unit
def test_app_testing_mode(app):
    """Test that app is in testing mode."""
    assert app.config['TESTING'] is True


@pytest.mark.unit
def test_index_route_get_method_only(client):
    """Test that index route only accepts GET requests."""
    response = client.get('/')
    assert response.status_code == 200

    # POST should return 405 Method Not Allowed
    response = client.post('/')
    assert response.status_code == 405


@pytest.mark.unit
def test_app_has_socketio(app):
    """Test that SocketIO is configured for the app."""
    from app import socketio
    assert socketio is not None


@pytest.mark.unit
def test_app_has_stock_service(app):
    """Test that stock service is initialized."""
    from app import stock_service
    assert stock_service is not None


@pytest.mark.unit
def test_invalid_route_returns_404(client):
    """Test that invalid routes return 404."""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
