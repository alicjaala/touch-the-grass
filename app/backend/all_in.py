import time
import numpy as np
from scipy.signal import welch, iirnotch, lfilter, butter
from brainaccess.utils import acquisition
from brainaccess.core.eeg_manager import EEGManager

# --- KONFIGURACJA ---
SFREQ = 250
WINDOW_SIZE = SFREQ * 1  # 1 sekunda
DEVICE_NAME = "BA MINI 050"

# Elektrody (dostosuj do swojego urządzenia)
electrodes_mini = {
    0: "Fp1",
    1: "Fp2",
}

# --- FILTRY ---
def filter_data(data, fs=SFREQ):
    """Notch 50Hz i bandpass 1-40Hz"""
    # Notch
    b_notch, a_notch = iirnotch(50.0, 30.0, fs)
    data = lfilter(b_notch, a_notch, data)
    # Bandpass
    nyq = fs * 0.5
    b_band, a_band = butter(4, [1/nyq, 40/nyq], btype='band')
    data = lfilter(b_band, a_band, data)
    return data

# --- ANALIZA PASM ---
def get_band_power(data, fs, low_f, high_f):
    freqs, psd = welch(data, fs, nperseg=fs)
    idx_min = np.argmax(freqs >= low_f)
    idx_max = np.argmax(freqs >= high_f)
    return float(np.mean(psd[idx_min:idx_max]))

def calculate_metrics(window_data):
    """Focus ratio i Beta dla stresu"""
    # Filtracja kanał po kanale
    filtered = np.array([filter_data(ch) for ch in window_data])
    avg_data = np.mean(filtered, axis=0)

    theta = get_band_power(avg_data, SFREQ, 4, 8)
    alpha = get_band_power(avg_data, SFREQ, 8, 12)
    beta  = get_band_power(avg_data, SFREQ, 13, 30)

    denom = theta + alpha
    focus_ratio = beta / denom if denom > 0 else 0

    return focus_ratio, beta

# --- GŁÓWNY PROGRAM ---
def main():
    eeg = acquisition.EEG()

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
                    time.sleep(0.5)
                    continue

                # Wycięcie ostatniej 1 sekundy
                window = data[:, -WINDOW_SIZE:]

                # Obliczenie metryk
                focus_raw, beta_raw = calculate_metrics(window)
                normalized_focus = np.clip(focus_raw * 50, 0, 100)

                # Wykrywanie stresu (wysoka Beta)
                is_stressed = beta_raw > 40  # kalibracja eksperymentalna

                # Log do konsoli
                bar = "|" * int(normalized_focus / 5)
                print(f"Focus: {normalized_focus:5.1f}% [{bar:<20}]  |  Stress: {is_stressed}")

                # Tu można wysłać JSON do WebSocket / aplikacji
                # data_to_send = {"focus": round(normalized_focus,1), "stress": is_stressed}

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("Zatrzymywanie...")

        finally:
            eeg.stop_acquisition()
            eeg.close()
            mgr.disconnect()
            print("Rozłączono.")

if __name__ == "__main__":
    main()
