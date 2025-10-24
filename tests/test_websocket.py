#!/usr/bin/env python3
"""Simple WebSocket test client for Thai ID Card Reader API."""

import asyncio
import json
import websockets


async def test_websocket():
    """Test WebSocket connection and card events."""
    uri = "ws://localhost:8765/ws"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected!")

            # Receive welcome message
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data.get('type')} - {data.get('message')}")

            # Request manual card read
            print("\nSending read_card command...")
            await websocket.send(json.dumps({
                "type": "read_card",
                "include_photo": False
            }))

            # Listen for events (timeout after 10 seconds)
            try:
                async with asyncio.timeout(10):
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        event_type = data.get('type')
                        print(f"\n[{event_type}]")

                        if event_type == 'card_read':
                            card_data = data.get('data', {})
                            print(f"  CID: {card_data.get('cid')}")
                            print(f"  Name (TH): {card_data.get('name_th')}")
                            print(f"  Name (EN): {card_data.get('name_en')}")
                            print("✓ Card read successful!")
                            break
                        elif event_type == 'error':
                            print(f"  Error: {data.get('message')}")
                            break
                        else:
                            print(f"  Message: {data.get('message')}")

            except TimeoutError:
                print("\n⚠ Timeout waiting for card read")

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

    print("\n✓ WebSocket test completed successfully!")
    return True


if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
