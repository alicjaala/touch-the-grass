const socket = new WebSocket('ws://localhost:8765');

const textFocus = document.getElementById('text-focus');
const barFocus = document.getElementById('bar-focus');

const textStress = document.getElementById('text-stress');
const barStress = document.getElementById('bar-stress');

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