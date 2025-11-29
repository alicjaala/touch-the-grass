import time
import numpy as np
from scipy.signal import welch, iirnotch, lfilter, butter
from brainaccess.utils import acquisition
from brainaccess.core.eeg_manager import EEGManager

SFREQ = 250

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
    """Focus i stress ratio"""
    # Filtracja kanał po kanale
    filtered = np.array([filter_data(ch) for ch in window_data])
    avg_data = np.mean(filtered, axis=0)

    freqs, psd = welch(avg_data, SFREQ)
    beta = np.mean(psd[(freqs>=13) & (freqs<=30)])
    alpha = np.mean(psd[(freqs>=8) & (freqs<=12)])
    high_beta = np.mean(psd[(freqs>=20) & (freqs<=30)])

    focus_ratio = beta / alpha
    stress_ratio = high_beta / alpha if alpha > 0 else 0

    return focus_ratio, stress_ratio, beta