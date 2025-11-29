let socket = null;
let lastNotificationTime = 0; 

function connect() {
    socket = new WebSocket('ws://localhost:8765');

    socket.onopen = () => {
        console.log("Połączono z mózgiem.");
        chrome.action.setBadgeText({ text: "ON" });
        chrome.action.setBadgeBackgroundColor({ color: "#888" });
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleBrainData(data);
    };

    socket.onclose = () => {
        setTimeout(connect, 3000); 
    };
}

function handleBrainData(data) {
    chrome.action.setBadgeText({ text: data.focus.toString() });

    // Kolory badge'a: Zielony (>60), Żółty (30-60), Czerwony (<30)
    if (data.focus > 60) chrome.action.setBadgeBackgroundColor({ color: "#4CAF50" });
    else if (data.focus > 30) chrome.action.setBadgeBackgroundColor({ color: "#FFC107" });
    else chrome.action.setBadgeBackgroundColor({ color: "#F44336" });


    const isBrainFried = (data.focus < 20) || (data.stress > 85);

    if (isBrainFried) {
        sendNotification();
    }
}

function sendNotification() {
    const now = Date.now();
    if (now - lastNotificationTime < 60000) {
        return; 
    }

    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icon.png',
        title: '🛑 PRZEGRZANIE SYSTEMU!',
        message: 'DUPA Poziom stresu krytyczny lub skupienie zerowe. Idź dotknij trawy!',
        priority: 2
    });

    lastNotificationTime = now;
}

connect();