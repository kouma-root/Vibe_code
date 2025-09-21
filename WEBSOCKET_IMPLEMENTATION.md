# Django Channels WebSocket Implementation

This document describes the implementation of Django Channels for live portfolio price feeds in the FinFlow application.

## Overview

The implementation provides real-time portfolio price updates using WebSockets, allowing users to see live price changes every 5 seconds with mock data.

## Files Created/Modified

### 1. `finflow/core/consumers.py` (NEW)
WebSocket consumer that handles real-time portfolio price updates.

**Key Features:**
- Accepts WebSocket connections at `ws/portfolio/`
- Broadcasts random portfolio price updates every 5 seconds
- Supports both authenticated and anonymous users
- Handles connection/disconnection gracefully
- Provides mock data for demonstration

### 2. `finflow/core/routing.py` (NEW)
WebSocket URL routing configuration.

**Routes:**
- `ws/portfolio/` → `PortfolioConsumer`

### 3. `finflow/asgi.py` (MODIFIED)
Updated ASGI configuration to include WebSocket routing.

**Changes:**
- Added import for `websocket_urlpatterns`
- Configured WebSocket routing in `ProtocolTypeRouter`

### 4. `templates/core/live_portfolio.html` (NEW)
Tailwind-styled template with JavaScript for live portfolio updates.

**Features:**
- Real-time WebSocket connection
- Live portfolio value updates
- Interactive chart using Chart.js
- Connection status indicators
- Start/stop update controls
- Responsive design with Tailwind CSS

### 5. `finflow/core/views.py` (MODIFIED)
Added `live_portfolio_view` function.

### 6. `finflow/core/urls.py` (MODIFIED)
Added URL pattern for live portfolio page.

### 7. `templates/core/home.html` (MODIFIED)
Added link to live portfolio page.

## WebSocket Consumer Details

### PortfolioConsumer Class

```python
class PortfolioConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live portfolio price updates.
    """
```

**Methods:**
- `connect()` - Handle WebSocket connection
- `disconnect()` - Handle WebSocket disconnection
- `receive()` - Handle incoming messages
- `start_price_updates()` - Start broadcasting updates
- `stop_price_updates()` - Stop broadcasting updates
- `price_update_loop()` - Main update loop (5-second intervals)
- `generate_mock_price_data()` - Generate mock portfolio data
- `get_user_portfolio_data()` - Get real portfolio data from database

### Message Types

**Incoming Messages:**
- `get_portfolio_data` - Request current portfolio data
- `start_updates` - Start price updates
- `stop_updates` - Stop price updates

**Outgoing Messages:**
- `connection_established` - Connection confirmation
- `portfolio_data` - Current portfolio data
- `price_update` - Live price update
- `error` - Error messages

## Frontend Implementation

### JavaScript WebSocket Client

The frontend uses a custom `PortfolioWebSocket` class that:

1. **Connects to WebSocket** at `ws://localhost:8000/ws/portfolio/`
2. **Handles connection states** (connecting, connected, disconnected)
3. **Manages message flow** (send/receive JSON messages)
4. **Updates UI elements** in real-time
5. **Provides user controls** (start/stop updates)
6. **Displays live charts** using Chart.js
7. **Shows connection status** and debug information

### Key Frontend Features

- **Real-time Updates**: Portfolio values update every 5 seconds
- **Interactive Chart**: Line chart showing portfolio value over time
- **Connection Status**: Visual indicators for WebSocket connection state
- **User Controls**: Start/stop update buttons
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Graceful handling of connection errors
- **Debug Information**: Development tools for monitoring WebSocket activity

## Mock Data Structure

The consumer generates mock portfolio data with the following structure:

```json
{
  "portfolio_id": "sample",
  "portfolio_name": "Sample Portfolio",
  "total_value": 50000.00,
  "total_change": 250.00,
  "total_change_percent": 0.50,
  "investments": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "current_price": 175.50,
      "change": 2.50,
      "change_percent": 1.45,
      "quantity": 100,
      "value": 17550.00
    }
  ]
}
```

## Usage Instructions

### 1. Start the Django Server

```bash
cd /home/kouma/Desktop/Personal_Projects/Vibe_code
source venv/bin/activate
python manage.py runserver
```

### 2. Access the Live Portfolio Page

Visit: `http://localhost:8000/live-portfolio/`

### 3. WebSocket Connection

The page will automatically connect to: `ws://localhost:8000/ws/portfolio/`

### 4. Control Updates

- Click "Start Updates" to begin receiving live price updates
- Click "Stop Updates" to pause the updates
- Updates occur every 5 seconds automatically

## Testing

### Automated Testing

Run the WebSocket test script:

```bash
python test_websocket.py
```

This script tests:
- WebSocket connection establishment
- Message sending and receiving
- Portfolio data requests
- Price update functionality
- Multiple concurrent connections

### Manual Testing

1. **Open Browser Developer Tools**
2. **Navigate to Console tab**
3. **Visit the live portfolio page**
4. **Monitor WebSocket messages in the console**
5. **Check Network tab for WebSocket connection**

### Browser Testing

1. Open multiple browser tabs/windows
2. Navigate to the live portfolio page in each
3. Verify all connections receive updates
4. Test start/stop functionality

## Configuration

### ASGI Settings

The ASGI configuration in `settings.py` should include:

```python
ASGI_APPLICATION = 'finflow.asgi.application'
```

### Channel Layers (Redis)

The Redis configuration is already set up in `settings.py`:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}
```

## Security Considerations

1. **Authentication**: WebSocket connections use Django's authentication middleware
2. **User Isolation**: Each user sees their own portfolio data
3. **Input Validation**: All incoming messages are validated
4. **Error Handling**: Graceful error handling prevents crashes
5. **Rate Limiting**: Consider implementing rate limiting for production

## Production Deployment

### Requirements

1. **Redis Server**: Required for channel layers
2. **ASGI Server**: Use Daphne or Uvicorn instead of runserver
3. **WebSocket Support**: Ensure your proxy/load balancer supports WebSockets
4. **SSL/TLS**: Use WSS (WebSocket Secure) in production

### Deployment Commands

```bash
# Install Daphne
pip install daphne

# Run with Daphne
daphne -b 0.0.0.0 -p 8000 finflow.asgi:application

# Or with Uvicorn
pip install uvicorn
uvicorn finflow.asgi:application --host 0.0.0.0 --port 8000
```

### Nginx Configuration

```nginx
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Django server is running
   - Check WebSocket URL is correct
   - Verify ASGI configuration

2. **No Updates Received**
   - Check browser console for errors
   - Verify WebSocket connection is established
   - Ensure "Start Updates" button is clicked

3. **Chart Not Updating**
   - Check Chart.js is loaded
   - Verify data format is correct
   - Check browser console for JavaScript errors

4. **Redis Connection Issues**
   - Ensure Redis server is running
   - Check Redis URL configuration
   - Verify Redis connectivity

### Debug Information

The live portfolio page includes debug information showing:
- WebSocket URL
- Connection state
- Message count
- Error count
- Last message received

## Future Enhancements

1. **Real Market Data**: Integrate with actual market data APIs
2. **User Notifications**: Add push notifications for significant changes
3. **Portfolio Alerts**: Set up price alerts and notifications
4. **Historical Data**: Store and display historical price data
5. **Multiple Portfolios**: Support multiple portfolios per user
6. **Advanced Charts**: Add more chart types and indicators
7. **Mobile App**: Create mobile app with WebSocket support

## API Reference

### WebSocket Endpoint

**URL:** `ws://localhost:8000/ws/portfolio/`

**Protocol:** WebSocket

**Authentication:** Django session-based (optional)

### Message Format

All messages are JSON format:

**Incoming:**
```json
{
  "type": "start_updates"
}
```

**Outgoing:**
```json
{
  "type": "price_update",
  "data": { /* portfolio data */ },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

This implementation provides a solid foundation for real-time portfolio monitoring and can be easily extended with additional features and integrations.
