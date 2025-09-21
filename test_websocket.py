#!/usr/bin/env python3
"""
Test script for Django Channels WebSocket implementation.
This script tests the PortfolioConsumer WebSocket functionality.
"""

import asyncio
import websockets
import json
import sys
import os

# Add the project directory to Python path
sys.path.append('/home/kouma/Desktop/Personal_Projects/Vibe_code')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finflow.settings')

import django
django.setup()


async def test_websocket_connection():
    """Test WebSocket connection and message handling."""
    print("Testing Django Channels WebSocket Implementation")
    print("=" * 50)
    
    # WebSocket URL
    ws_url = "ws://localhost:8000/ws/portfolio/"
    
    try:
        print(f"Connecting to: {ws_url}")
        
        async with websockets.connect(ws_url) as websocket:
            print("✓ WebSocket connection established")
            
            # Test 1: Wait for connection confirmation
            print("\n1. Waiting for connection confirmation...")
            message = await websocket.recv()
            data = json.loads(message)
            print(f"   Received: {data.get('type')} - {data.get('message')}")
            
            # Test 2: Request portfolio data
            print("\n2. Requesting portfolio data...")
            await websocket.send(json.dumps({"type": "get_portfolio_data"}))
            
            message = await websocket.recv()
            data = json.loads(message)
            print(f"   Received: {data.get('type')}")
            if data.get('data'):
                portfolio_data = data['data']
                print(f"   Portfolio: {portfolio_data.get('portfolio_name', 'Unknown')}")
                print(f"   Total Value: ${portfolio_data.get('total_value', 0):,.2f}")
                print(f"   Investments: {len(portfolio_data.get('investments', []))}")
            
            # Test 3: Start price updates
            print("\n3. Starting price updates...")
            await websocket.send(json.dumps({"type": "start_updates"}))
            
            # Test 4: Receive price updates
            print("\n4. Receiving price updates (5 updates)...")
            for i in range(5):
                message = await websocket.recv()
                data = json.loads(message)
                if data.get('type') == 'price_update':
                    portfolio_data = data.get('data', {})
                    print(f"   Update {i+1}: ${portfolio_data.get('total_value', 0):,.2f} "
                          f"({portfolio_data.get('total_change_percent', 0):+.2f}%)")
                else:
                    print(f"   Received: {data.get('type')}")
            
            # Test 5: Stop updates
            print("\n5. Stopping price updates...")
            await websocket.send(json.dumps({"type": "stop_updates"}))
            
            print("\n✓ All WebSocket tests completed successfully!")
            
    except ConnectionRefusedError:
        print("✗ Connection refused. Make sure the Django server is running:")
        print("  python manage.py runserver")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


async def test_multiple_connections():
    """Test multiple WebSocket connections."""
    print("\n" + "=" * 50)
    print("Testing Multiple WebSocket Connections")
    print("=" * 50)
    
    async def single_connection(connection_id):
        try:
            async with websockets.connect("ws://localhost:8000/ws/portfolio/") as websocket:
                print(f"Connection {connection_id}: Connected")
                
                # Wait for connection confirmation
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Connection {connection_id}: {data.get('message')}")
                
                # Start updates and receive a few messages
                await websocket.send(json.dumps({"type": "start_updates"}))
                
                for i in range(3):
                    message = await websocket.recv()
                    data = json.loads(message)
                    if data.get('type') == 'price_update':
                        portfolio_data = data.get('data', {})
                        print(f"Connection {connection_id}: Update {i+1} - "
                              f"${portfolio_data.get('total_value', 0):,.2f}")
                
                print(f"Connection {connection_id}: Completed")
                
        except Exception as e:
            print(f"Connection {connection_id}: Error - {e}")
    
    # Create multiple concurrent connections
    tasks = [single_connection(i) for i in range(3)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print("✓ Multiple connections test completed")


async def main():
    """Main test function."""
    print("Django Channels WebSocket Test Suite")
    print("=" * 50)
    
    # Test basic connection
    success = await test_websocket_connection()
    
    if success:
        # Test multiple connections
        await test_multiple_connections()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        print("=" * 50)
        print("\nTo test in browser:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Visit: http://localhost:8000/live-portfolio/")
        print("3. Open browser developer tools to see WebSocket messages")
        print("\nWebSocket endpoint: ws://localhost:8000/ws/portfolio/")
    else:
        print("\nTests failed. Please check the Django server is running.")


if __name__ == '__main__':
    # Install websockets if not available
    try:
        import websockets
    except ImportError:
        print("Installing websockets package...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'websockets'])
        import websockets
    
    asyncio.run(main())
