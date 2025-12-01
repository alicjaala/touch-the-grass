import asyncio
import websockets
import json
import time
import numpy as np

from processor import EEGProcessor

PORT = 8765
DEVICE_NAME = "BA MINI 047"
SFREQ = 250
WINDOW_SIZE = SFREQ * 5
ELECTRODES = {0: "Fp1", 1: "Fp2"}

BRAINACCESS_AVAILABLE = False
try:
    from brainaccess.utils import acquisition
    from brainaccess.core.eeg_manager import EEGManager
    BRAINACCESS_AVAILABLE = True
except ImportError:
    print("[!] Nie znaleziono bibliotek BrainAccess. Dostępna tylko symulacja.")

async def stream_simulation(websocket):
    print("Klient połączony (TRYB SYMULACJI)")
    try:
        while True:
            f_sim = np.random.randint(30, 80)
            s_sim = np.random.randint(10, 50)
            
            result = {
                "focus": f_sim,
                "stress": s_sim,
                "alert": 0,
                "mode": "simulation"
            }
            
            await websocket.send(json.dumps(result))
            print(f"Symulacja: Focus {f_sim}% | Stress {s_sim}%")
            await asyncio.sleep(1)
            
    except websockets.exceptions.ConnectionClosed:
        print("Klient symulacji rozłączony")

async def stream_real_eeg(websocket, eeg):
    print("Klient połączony (TRYB REAL EEG)")
    
    processor = EEGProcessor()
    
    try:
        while True:
            eeg.get_mne()
            
            if not hasattr(eeg.data, 'mne_raw') or eeg.data.mne_raw is None:
                await asyncio.sleep(0.1)
                continue

            mne_raw = eeg.data.mne_raw
            data, times = mne_raw.get_data(return_times=True)

            if data.shape[1] < WINDOW_SIZE:
                await asyncio.sleep(0.5)
                continue

            window = data[:, -WINDOW_SIZE:]

            metrics = processor.process_window(window)

            if metrics:
                result = {
                    "focus": metrics["focus"],
                    "stress": metrics["stress"],
                    "alert": metrics["alert"],
                    "mode": "real"
                }

                await websocket.send(json.dumps(result))
                
                print(f"REAL -> F: {metrics['focus']:05.2f}% | S: {metrics['stress']:05.2f}% | (Raw: {metrics['raw_focus']:.3f})")
            else:
                print("[!] Ignorowanie okna (artefakty/ruch)")

            await asyncio.sleep(0.5)

    except websockets.exceptions.ConnectionClosed:
        print("Klient rozłączony (EEG)")
    except Exception as e:
        print(f"Błąd w pętli EEG: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("--- START SERWERA MÓZGU ---")
    
    use_simulation = True
    eeg_instance = None
    manager = None

    if BRAINACCESS_AVAILABLE:
        try:
            print(f"Szukanie urządzenia...")
            manager = EEGManager()
            eeg_instance = acquisition.EEG()
            
            manager.__enter__() 
            
            eeg_instance.setup(manager, device_name=DEVICE_NAME, cap=ELECTRODES, sfreq=SFREQ)
            eeg_instance.start_acquisition()
            
            print(f"SUKCES: Połączono z urządzeniem.")
            print("Buforowanie wstępne danych (3s)...")
            time.sleep(3)
            use_simulation = False
            
        except Exception as e:
            print(f"[!] Nie udało się połączyć z opaską: {e}")
            print("[i] Przechodzę w tryb SYMULACJI.")
            if manager:
                manager.__exit__(None, None, None)
            use_simulation = True
    else:
        print("[i] Brak bibliotek - tryb SYMULACJI wymuszony.")

    print(f"\n>> Serwer WebSocket nasłuchuje na ws://localhost:{PORT}")
    print(f">> Tryb pracy: {'SYMULACJA (dane losowe)' if use_simulation else 'REAL TIME EEG'}")

    try:
        if use_simulation:
            async with websockets.serve(stream_simulation, "localhost", PORT):
                await asyncio.get_running_loop().create_future() 
        else:
            async with websockets.serve(lambda ws: stream_real_eeg(ws, eeg_instance), "localhost", PORT):
                await asyncio.get_running_loop().create_future()
    
    finally:
        if not use_simulation and manager:
            print("Zamykanie połączenia z EEG...")
            try:
                eeg_instance.stop_acquisition()
                eeg_instance.close()
                manager.__exit__(None, None, None)
            except:
                pass
            print("EEG zamknięte.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nZatrzymano serwer.")
