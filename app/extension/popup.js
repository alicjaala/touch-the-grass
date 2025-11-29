const socket = new WebSocket('ws://localhost:8765');

const textFocus = document.getElementById('text-focus');
const barFocus = document.getElementById('bar-focus');

const textStress = document.getElementById('text-stress');
const barStress = document.getElementById('bar-stress');

const btnCalibrate = document.getElementById('btn-calibrate');

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    textFocus.innerText = data.focus + "%";
    barFocus.style.width = data.focus + "%"; 

    textStress.innerText = data.stress + "%";
    barStress.style.width = data.stress + "%";

    if (data.stress > 80) {
        barStress.style.backgroundColor = "#b71c1c";
    } else {
        barStress.style.backgroundColor = "#F44336"; 
    }
};

btnCalibrate.addEventListener('click', () => {
    // Sprawdzamy, czy połączenie działa
    if (socket.readyState === WebSocket.OPEN) {
        
        // Tworzymy paczkę z komendą
        const message = {
            command: "start_calibration",
            timestamp: Date.now()
        };

        // Wysyłamy do Pythona jako tekst
        socket.send(JSON.stringify(message));
        
        console.log("Wysłano komendę kalibracji");
        
        // Efekt wizualny dla użytkownika (zablokuj przycisk na chwilę)
        btnCalibrate.innerText = "Kalibrowanie...";
        btnCalibrate.disabled = true;

        // Opcjonalnie: odblokuj po 5 sekundach
        setTimeout(() => {
            btnCalibrate.innerText = "Rozpocznij Kalibrację";
            btnCalibrate.disabled = false;
        }, 5000);

    } else {
        console.error("Błąd: Nie połączono z serwerem.");
        btnCalibrate.innerText = "Błąd połączenia";
    }
});