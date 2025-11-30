import asyncio
import websockets
import json
import random
import time
import numpy as np

# --- IMPORTY EEG ---
# Próbujemy zaimportować biblioteki. Jeśli ich nie ma, kod przejdzie w tryb symulacji.
try:
    from brainaccess.utils import acquisition
    from brainaccess.core.eeg_manager import EEGManager
    # Zakładam, że masz plik processor.py w tym samym folderze
    from processor import calculate_metrics 
    BRAINACCESS_AVAILABLE = True
except ImportError as e:
    print(f"[!] Nie znaleziono bibliotek BrainAccess lub processor.py: {e}")
    print("[i] Przełączanie w tryb TYLKO SYMULACJA.")
    BRAINACCESS_AVAILABLE = False

# --- KONFIGURACJA ---
PORT = 8765
DEVICE_NAME = "BA MINI 047"
SFREQ = 250
WINDOW_SIZE = SFREQ * 5
ELECTRODES = {0: "Fp1", 1: "Fp2"}

# --- TRYB 1: SYMULACJA (Gdy brak opaski) ---
async def stream_simulation(websocket):
    """Generuje losowe dane, gdy brak urządzenia EEG."""
    print(f"Klient połączony (Tryb Symulacji)")
    try:
        while True:
            # Losowe dane (jak w twoim server.py)
            focus_level = random.randint(40, 100) 
            is_stressed = random.random() > 0.90 
            stress_level = random.randint(80, 100) if is_stressed else random.randint(0, 30)

            data = {
                "focus": focus_level,
                "stress": stress_level,
                "alert": is_stressed,
                "mode": "simulation" # info dla klienta, że to fake
            }

            await websocket.send(json.dumps(data))
            # print(f"Wysłano (Symulacja): {data}")
            await asyncio.sleep(1) # WAŻNE: asyncio.sleep zamiast time.sleep
            
    except websockets.exceptions.ConnectionClosed:
        print("Klient rozłączony (Symulacja)")


# --- TRYB 2: PRAWDZIWE EEG ---
async def stream_real_eeg(websocket, eeg):
    """Pobiera dane z urządzenia, przetwarza i wysyła."""
    print("Klient połączony (Tryb EEG)")

    # Zmienne do normalizacji (dynamiczne skalowanie)
    max_focus = 0
    min_focus = 100
    max_stress = 0.2
    min_stress = 0.007

    try:
        while True:
            # 1. Pobranie danych z biblioteki BrainAccess
            eeg.get_mne()
            if not hasattr(eeg.data, 'mne_raw') or eeg.data.mne_raw is None:
                await asyncio.sleep(0.1)
                continue

            mne_raw = eeg.data.mne_raw
            data, times = mne_raw.get_data(return_times=True)

            # 2. Sprawdzenie czy mamy wystarczająco dużo danych do okna
            if data.shape[1] < WINDOW_SIZE:
                # print(f"Buforowanie... {data.shape[1]}/{WINDOW_SIZE}")
                await asyncio.sleep(1)
                continue

            # 3. Wycięcie ostatniego okna czasowego
            window = data[:, -WINDOW_SIZE:]

            # 4. OBLICZENIA (z processor.py)
            focus_raw, stress_raw, beta_raw = calculate_metrics(window)

            # 5. NORMALIZACJA
            normalized_focus = np.clip(focus_raw * 200, 0, 100)

            # Dynamiczna kalibracja min/max
            if max_focus == 0: max_focus = normalized_focus
            min_focus = min(min_focus, normalized_focus)
            
            if normalized_focus <= max_focus + min_focus * 0.03:
                max_focus = max(max_focus, normalized_focus)

            max_stress = max(max_stress, stress_raw)
            min_stress = min(min_stress, stress_raw)

            # Obliczenie procentów
            denom_focus = (max_focus - min_focus) if (max_focus - min_focus) != 0 else 1
            denom_stress = (max_stress - min_stress) if (max_stress - min_stress) != 0 else 1

            focus_percent = min((normalized_focus - min_focus) / denom_focus * 100, 100)
            stress_percent = min((stress_raw - min_stress) / denom_stress * 100, 100)

            print(f"Min: {min_focus:5.3f}% Max: {max_focus:5.3f}% ")
            print(f"Focus: {normalized_focus:5.3f}% |  focus percent: {focus_percent}% | stress percent: {stress_raw} => {stress_percent}%")
            # 6. Przygotowanie danych do wysłania
            # Rzutujemy na float(), bo json nie lubi typów numpy
            result = {
                "focus": round(float(focus_percent), 2),
                "stress": round(float(stress_percent), 2),
                "alert": 1,
                "mode": "real"
            }

            await websocket.send(json.dumps(result))
            print("Wysłano (EEG):", result)

            await asyncio.sleep(1) # Częstotliwość wysyłania danych

    except websockets.exceptions.ConnectionClosed:
        print("Klient rozłączony (EEG)")
    except Exception as e:
        print(f"Błąd w pętli EEG: {e}")

# --- GŁÓWNA FUNKCJA ---
async def main():
    print("--- START SERWERA MÓZGU ---")
    
    use_simulation = True
    eeg_instance = None
    manager = None

    # 1. Próba połączenia ze sprzętem (tylko jeśli biblioteki są dostępne)
    if BRAINACCESS_AVAILABLE:
        try:
            print(f"Szukanie urządzenia: {DEVICE_NAME}...")
            manager = EEGManager()
            eeg_instance = acquisition.EEG()
            
            # Otwieramy managera "na stałe" na czas działania serwera
            manager.__enter__() 
            
            eeg_instance.setup(manager, device_name=DEVICE_NAME, cap=ELECTRODES, sfreq=SFREQ)
            eeg_instance.start_acquisition()
            
            print(f"SUKCES: Połączono z {DEVICE_NAME}")
            print("Buforowanie wstępne danych (2s)...")
            time.sleep(2) # Tu można użyć time.sleep, bo pętla async jeszcze nie ruszyła
            use_simulation = False
            
        except Exception as e:
            print(f"[!] Nie udało się połączyć z opaską: {e}")
            print("[i] Przechodzę w tryb SYMULACJI.")
            # Jeśli się nie uda, zamykamy managera
            if manager:
                manager.__exit__(None, None, None)
            use_simulation = True
    else:
        print("[i] Brak bibliotek - tryb SYMULACJI wymuszony.")

    # 2. Uruchomienie serwera WebSocket
    print(f"\n>> Serwer WebSocket nasłuchuje na ws://localhost:{PORT}")
    print(f">> Tryb pracy: {'SYMULACJA (dane losowe)' if use_simulation else 'REAL TIME EEG'}")

    try:
        if use_simulation:
            # Uruchom handler symulacji
            async with websockets.serve(stream_simulation, "localhost", PORT):
                await asyncio.get_running_loop().create_future() # Czekaj w nieskończoność
        else:
            # Uruchom handler EEG (przekazujemy instancję eeg przez lambda)
            async with websockets.serve(lambda ws: stream_real_eeg(ws, eeg_instance), "localhost", PORT):
                await asyncio.get_running_loop().create_future()
    
    finally:
        # Sprzątanie po zamknięciu (CTRL+C)
        if not use_simulation and manager:
            print("Zamykanie połączenia z EEG...")
            eeg_instance.stop_acquisition()
            eeg_instance.close()
            manager.__exit__(None, None, None)
            print("EEG zamknięte.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nZatrzymano serwer.")