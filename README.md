![Logo projektu Touch the Grass - krowa](app/extension/icons/cow-128.png)

# Touch the Grass

> Stay calm and focused: reduce stress while sending messages and emails.

"Touch the Grass" is an innovative neuro-feedback project designed to monitor and actively help users reduce stress and maintain focus while performing attention-demanding tasks, such as writing emails or chatting. It combines a real-time EEG processing backend with a cross-browser extension. It has been created during Neurohackaton Fall 2025 Wroclaw University of Science and Technology

---

## Features

* **Real-Time EEG Monitoring**: The Python backend uses a BrainAccess device to acquire and process EEG signals in real-time from Fp1 and Fp2 electrodes.
* **Focus and Stress Metrics**: It calculates `focus` and `stress` metrics from the EEG data, handles artifact rejection (e.g., movement), and streams the results to the frontend via a WebSocket server.
* **Simulation Mode**: If the EEG device is unavailable or BrainAccess libraries aren't found, the server automatically switches to **Simulation Mode**, generating random data for testing and demonstration.
* **Browser Integration**: The Chrome/Edge extension runs in the background and uses content scripts to inject a user interface on virtually any website (`<all_urls>`).
* **Configuration Mechanisms**: The extension has host permissions for external services like **YouTube** and a **Sudoku API** and utilises them for metrics calibration to make measures of users max focus level and stress level with limited time tasks.

---

## Technologies

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python, `websockets`, `brainaccess` SDK, `mne` | Server for EEG acquisition and processing. Uses WebSocket on port **8765** for frontend communication. |
| **Frontend** | Chrome/Edge Extension (Manifest V3), JavaScript, HTML, CSS | Browser extension consuming data from the WebSocket and reacting to stress/focus levels. |

---

## Setup and Installation

The project requires running the Python backend server separately and installing the browser extension.

### 1. Backend Setup (Python Server)

#### A. Prerequisites
* **BrainAccess Halo**
* **Python 3**

#### B. Installation

1.  **Clone the repository** (if not already done).
    ```bash
    git clone [YOUR_REPO_LINK]
    cd neurohackathon-main
    ```
2.  **Create and activate a virtual environment** (recommended).
    * **Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * **Windows:**
        ```bash
        python -m venv .venv
        .venv\Scripts\activate.bat
        ```
3.  **Install dependencies:**
    The project relies on libraries like `brainaccess`, `mne`, `numpy`, and `websockets`.
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the EEG server:**
    The default device name is `"BA MINI 047"`. If you are using a different device, update the `DEVICE_NAME` variable in `app/backend/server.py`.
    ```bash
    python app/backend/server.py
    ```
    The server will listen on `ws://localhost:8765`.

### 2. Frontend Installation (Browser Extension)

1.  Open your browser's extensions management page (e.g., `chrome://extensions`).
2.  Enable **Developer Mode**.
3.  Click the **Load unpacked** button.
4.  Select the **`app/extension/`** directory from the cloned repository.
5.  The "Touch the Grass" extension should now be loaded and active.

---

## Project Structure

```
neurohackathon-main/
├── app/
│   ├── backend/
│   │   ├── server.py
│   │   └── processor.py
│   ├── extension/
│   │   ├── icons/*
│   │   ├── videos/*
│   │   ├── background.js
│   │   ├── content.js
│   │   ├── manifest.json
│   │   ├── package.json
│   │   ├── popup.js
│   │   └── popup.html
├── requirements.txt
└── device-guide/
```
