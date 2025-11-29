# backend/server.py
import asyncio
import websockets
import json
import random

# Konfiguracja
PORT = 8765

async def brain_stream(websocket):
    print("Klient połączony (Wtyczka)")
    try:
        while True:
            # tu potem wkleić prawdziwe odczyty
            focus_level = random.randint(40, 100) 
            
            is_stressed = random.random() > 0.90 
            stress_level = random.randint(80, 100) if is_stressed else random.randint(0, 30)

            data = {
                "focus": focus_level,
                "stress": stress_level,
                "alert": is_stressed 
            }

            await websocket.send(json.dumps(data))
            print(f"Wysłano: {data}")

            # Czekamy 1 sekundę (symulacja próbkowania co sekunde)
            # W realnym EEG zmienisz to np. na 0.1 (10Hz)
            await asyncio.sleep(1)
            
    except websockets.exceptions.ConnectionClosed:
        print("Klient rozłączony")

async def main():
    print(f"Serwer Mózgu startuje na ws://localhost:{PORT}")
    async with websockets.serve(brain_stream, "localhost", PORT):
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())