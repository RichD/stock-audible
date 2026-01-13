"""Main Flask application."""
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread, Event
import time

from config import Config
from stock_service import StockService

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize stock service
stock_service = StockService()

# Global state for announcement thread
announcement_thread = None
stop_event = Event()
current_ticker = None
current_interval = Config.DEFAULT_INTERVAL


def announce_stock_prices():
    """Background thread to fetch and emit stock prices."""
    global current_ticker, current_interval

    while not stop_event.is_set():
        if current_ticker:
            data = stock_service.get_current_price(current_ticker)

            if data:
                announcement = stock_service.format_announcement(data)
                socketio.emit('price_update', {
                    'ticker': data['ticker'],
                    'price': data['price'],
                    'announcement': announcement,
                    'timestamp': time.time()
                })
            else:
                socketio.emit('error', {
                    'message': f'Could not fetch price for {current_ticker}'
                })

        # Wait for interval or until stopped
        stop_event.wait(current_interval)


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html',
                          default_interval=Config.DEFAULT_INTERVAL)


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'status': 'Connected to server'})


@socketio.on('start_announcements')
def handle_start(data):
    """Start announcing stock prices.

    Args:
        data: Dictionary with 'ticker' and 'interval' keys
    """
    global announcement_thread, current_ticker, current_interval, stop_event

    ticker = data.get('ticker', '').strip().upper()
    interval = int(data.get('interval', Config.DEFAULT_INTERVAL))

    if not ticker:
        emit('error', {'message': 'Please provide a ticker symbol'})
        return

    # Stop existing thread if running
    if announcement_thread and announcement_thread.is_alive():
        stop_event.set()
        announcement_thread.join()

    # Reset and start new thread
    stop_event.clear()
    current_ticker = ticker
    current_interval = max(5, interval)  # Minimum 5 seconds

    announcement_thread = Thread(target=announce_stock_prices)
    announcement_thread.daemon = True
    announcement_thread.start()

    emit('started', {
        'ticker': current_ticker,
        'interval': current_interval
    })


@socketio.on('stop_announcements')
def handle_stop():
    """Stop announcing stock prices."""
    global stop_event, current_ticker

    stop_event.set()
    current_ticker = None

    emit('stopped', {'status': 'Announcements stopped'})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=Config.DEBUG, port=5000)
