import time
import numpy as np
from scipy.signal import welch, iirnotch, lfilter, butter
from brainaccess.utils import acquisition
from brainaccess.core.eeg_manager import EEGManager
from processor import *
from transmitter import *

# --- KONFIGURACJA ---
SFREQ = 250
WINDOW_SIZE = SFREQ * 5  # 1 sekunda
DEVICE_NAME = "BA MINI 047"


# Elektrody
electrodes_mini = {
    0: "Fp1",
    1: "Fp2",
}

# --- GŁÓWNY PROGRAM ---
def main():
    transmitter = DataTransmitter(port=8765)
    transmitter.start_server()

    eeg = acquisition.EEG()
    max_focus = 0
    min_focus = 100

    max_stress = 0.2
    min_stress = 0.007

    print(f"Łączenie z {DEVICE_NAME}...")
    with EEGManager() as mgr:
        eeg.setup(mgr, device_name=DEVICE_NAME, cap=electrodes_mini, sfreq=SFREQ)
        eeg.start_acquisition()
        print("Akwizycja rozpoczęta. Buforowanie 2 sekundy...")
        time.sleep(2)

        try:
            while True:
                # Aktualizacja MNE Raw
                eeg.get_mne()
                mne_raw = eeg.data.mne_raw
                data, times = mne_raw.get_data(return_times=True)

                if data.shape[1] < WINDOW_SIZE:
                    print("Buforowanie danych...")
                    time.sleep(5)
                    continue

                window = data[:, -WINDOW_SIZE:]

                # Obliczenie metryk
                focus_raw, stress_raw, beta_raw = calculate_metrics(window)
                print("Jestem")
                normalized_focus = np.clip(focus_raw * 200, 0, 100)
                
                if (max_focus == 0): 
                    max_focus = normalized_focus
                

                min_focus = min(min_focus, normalized_focus)

                if (normalized_focus <= max_focus + min_focus*0.03):
                    max_focus = max(max_focus, normalized_focus)
                
                max_stress = max(max_stress, stress_raw)
                min_stress = min(min_stress, stress_raw)

                focus_percent = min((normalized_focus - min_focus) / (max_focus - min_focus) * 100, 100)
                stress_percent = min((stress_raw - min_stress) / (max_stress - min_stress) * 100, 100)
                
                result = {'focus_percent': focus_percent, 'stress_percent': stress_percent}

                transmitter.send_data(result)

                # Log do konsoli
                print(f"Min: {min_focus:5.3f}% Max: {max_focus:5.3f}% ")

                bar = "|" * int(normalized_focus / 5)
                print(f"Focus: {normalized_focus:5.3f}% [{bar:<20}]  |  focus percent: {focus_percent}% | stress percent: {stress_percent}%")
                '''
                if (normalized_focus < min_focus + (max_focus-min_focus)/3):
                    print("nie skupione")
                elif (normalized_focus > max_focus - (max_focus-min_focus)/3):
                    print("skupione")
                else:
                    print("neutralnie")
                '''
                time.sleep(3)

        except KeyboardInterrupt:
            print("Zatrzymywanie...")

        finally:
            eeg.stop_acquisition()
            eeg.close()
            mgr.disconnect()
            print("Rozłączono.")

if __name__ == "__main__":
    main()
