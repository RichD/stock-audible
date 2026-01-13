"""Stock data fetching service."""
import yfinance as yf

class StockService:
    """Service for fetching stock price data."""

    def get_current_price(self, ticker):
        """Fetch current price for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'SPY')

        Returns:
            Dictionary with ticker and price, or None if error
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Try to get current price from different fields
            price = info.get('currentPrice') or info.get('regularMarketPrice')

            if price is None:
                # Fallback: get latest price from history
                hist = stock.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]

            if price is None:
                return None

            return {
                'ticker': ticker.upper(),
                'price': round(float(price), 2),
                'currency': info.get('currency', 'USD')
            }
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def format_announcement(self, data):
        """Format data for audio announcement.

        Args:
            data: Dictionary with ticker and price

        Returns:
            String formatted for TTS (e.g., "A P P L. 150.25")
        """
        ticker = data['ticker']
        price = data['price']

        # Spell out ticker letter by letter for TTS
        ticker_spelled = ' '.join(ticker)

        return f"{ticker_spelled}. {price}"
