import json
import asyncio
import random
from decimal import Decimal
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class PortfolioConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live portfolio price updates.
    
    Features:
    - Accepts WebSocket connections at ws/portfolio/
    - Broadcasts random portfolio price updates every 5 seconds
    - Supports user-specific portfolio data
    - Handles connection/disconnection gracefully
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.room_group_name = 'portfolio_updates'
        self.user = self.scope.get("user")
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to portfolio price feed',
            'timestamp': datetime.now().isoformat(),
            'user': getattr(self.user, 'username', 'anonymous') if self.user else 'anonymous'
        }))
        
        # Start the price update loop
        await self.start_price_updates()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages received from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', '')
            
            if message_type == 'get_portfolio_data':
                # Send current portfolio data
                portfolio_data = await self.get_user_portfolio_data()
                await self.send(text_data=json.dumps({
                    'type': 'portfolio_data',
                    'data': portfolio_data,
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif message_type == 'start_updates':
                # Start price updates
                await self.start_price_updates()
            
            elif message_type == 'stop_updates':
                # Stop price updates
                await self.stop_price_updates()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))
    
    async def start_price_updates(self):
        """Start broadcasting price updates every 5 seconds."""
        if hasattr(self, 'update_task') and not self.update_task.done():
            return  # Already running
        
        self.update_task = asyncio.create_task(self.price_update_loop())
    
    async def stop_price_updates(self):
        """Stop broadcasting price updates."""
        if hasattr(self, 'update_task'):
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def price_update_loop(self):
        """Main loop for broadcasting price updates."""
        try:
            while True:
                # Generate mock price data
                price_data = await self.generate_mock_price_data()
                
                # Send to WebSocket
                await self.send(text_data=json.dumps({
                    'type': 'price_update',
                    'data': price_data,
                    'timestamp': datetime.now().isoformat()
                }))
                
                # Wait 5 seconds
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            # Send error message
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Price update error: {str(e)}'
            }))
    
    async def generate_mock_price_data(self):
        """Generate mock portfolio price data."""
        # Return sample data for all users (simplified for testing)
        return {
            'portfolio_id': 'sample',
            'portfolio_name': 'Sample Portfolio',
            'total_value': round(random.uniform(45000, 55000), 2),
            'total_change': round(random.uniform(-500, 500), 2),
            'total_change_percent': round(random.uniform(-2, 2), 2),
            'investments': [
                {
                    'symbol': 'AAPL',
                    'name': 'Apple Inc.',
                    'current_price': round(random.uniform(150, 200), 2),
                    'change': round(random.uniform(-5, 5), 2),
                    'change_percent': round(random.uniform(-3, 3), 2),
                    'quantity': 100,
                    'value': round(random.uniform(15000, 20000), 2)
                },
                {
                    'symbol': 'MSFT',
                    'name': 'Microsoft Corporation',
                    'current_price': round(random.uniform(300, 400), 2),
                    'change': round(random.uniform(-8, 8), 2),
                    'change_percent': round(random.uniform(-2, 2), 2),
                    'quantity': 50,
                    'value': round(random.uniform(15000, 20000), 2)
                },
                {
                    'symbol': 'GOOGL',
                    'name': 'Alphabet Inc.',
                    'current_price': round(random.uniform(120, 150), 2),
                    'change': round(random.uniform(-3, 3), 2),
                    'change_percent': round(random.uniform(-2, 2), 2),
                    'quantity': 75,
                    'value': round(random.uniform(9000, 11250), 2)
                }
            ]
        }
    
    async def get_user_portfolio_data(self):
        """Get user's portfolio data (simplified for testing)."""
        # Return mock data for now
        return {
            'portfolio_id': 'mock',
            'portfolio_name': 'Mock Portfolio',
            'total_value': 50000,
            'total_change': 0,
            'total_change_percent': 0,
            'investments': []
        }
    
    # Handle different message types from the group
    async def portfolio_update(self, event):
        """Handle portfolio update messages from the group."""
        await self.send(text_data=json.dumps({
            'type': 'portfolio_update',
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def price_update(self, event):
        """Handle price update messages from the group."""
        await self.send(text_data=json.dumps({
            'type': 'price_update',
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def error_message(self, event):
        """Handle error messages from the group."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
