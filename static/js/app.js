// Initialize WebSocket connection
const socket = io();

// DOM elements
const statusDiv = document.getElementById('status');
const tickerForm = document.getElementById('ticker-form');
const tickerInput = document.getElementById('ticker');
const intervalInput = document.getElementById('interval');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const priceDisplay = document.getElementById('price-display');
const tickerDisplay = document.getElementById('ticker-display');
const priceValue = document.getElementById('price-value');
const lastUpdate = document.getElementById('last-update');
const speechEnabled = document.getElementById('speech-enabled');

// Speech synthesis
let synth = window.speechSynthesis;
let isRunning = false;
let lastAnnouncement = '';

// Detect mobile Safari
const isMobileSafari = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

// Connection handlers
socket.on('connect', () => {
    updateStatus('Connected to server', 'success');
});

socket.on('disconnect', () => {
    updateStatus('Disconnected from server', 'danger');
});

socket.on('connected', (data) => {
    console.log(data.status);
});

// Announcement handlers
socket.on('started', (data) => {
    isRunning = true;
    updateStatus(`Announcing ${data.ticker} every ${data.interval} seconds`, 'primary');
    startBtn.disabled = true;
    stopBtn.disabled = false;
    tickerInput.disabled = true;
    intervalInput.disabled = true;
});

socket.on('stopped', (data) => {
    isRunning = false;
    updateStatus('Announcements stopped', 'info');
    startBtn.disabled = false;
    stopBtn.disabled = true;
    tickerInput.disabled = false;
    intervalInput.disabled = false;
    priceDisplay.style.display = 'none';
});

socket.on('price_update', (data) => {
    console.log('Received price update:', data);

    // Store announcement for mobile
    lastAnnouncement = data.announcement;

    // Update display
    tickerDisplay.textContent = data.ticker;
    priceValue.textContent = `$${data.price}`;

    if (isMobileSafari && speechEnabled.checked) {
        lastUpdate.textContent = `Last updated: ${new Date(data.timestamp * 1000).toLocaleTimeString()} - Tap to hear`;
        priceDisplay.style.cursor = 'pointer';
    } else {
        lastUpdate.textContent = `Last updated: ${new Date(data.timestamp * 1000).toLocaleTimeString()}`;
    }

    priceDisplay.style.display = 'block';

    // Announce if enabled (will only work on desktop Safari, not mobile)
    if (speechEnabled.checked && !isMobileSafari) {
        console.log('Speech enabled, calling speak()');
        speak(data.announcement);
    } else if (isMobileSafari) {
        console.log('Mobile Safari detected, waiting for user tap');
    } else {
        console.log('Speech disabled, skipping announcement');
    }
});

socket.on('error', (data) => {
    updateStatus(`Error: ${data.message}`, 'danger');
});

// Form handlers
tickerForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const ticker = tickerInput.value.trim().toUpperCase();
    const interval = parseInt(intervalInput.value);

    if (!ticker) {
        alert('Please enter a ticker symbol');
        return;
    }

    if (interval < 5) {
        alert('Interval must be at least 5 seconds');
        return;
    }

    socket.emit('start_announcements', {
        ticker: ticker,
        interval: interval
    });
});

stopBtn.addEventListener('click', () => {
    socket.emit('stop_announcements');
});

// Text-to-Speech function
function speak(text) {
    console.log('Attempting to speak:', text);

    // Cancel any ongoing speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;  // Slightly slower for clarity
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Safari-specific: Wait for voices to load
    if (synth.getVoices().length === 0) {
        synth.addEventListener('voiceschanged', () => {
            console.log('Voices loaded, speaking now');
            synth.speak(utterance);
        }, { once: true });
    } else {
        synth.speak(utterance);
    }

    // Error handling
    utterance.onerror = (event) => {
        console.error('Speech error:', event);
    };

    utterance.onstart = () => {
        console.log('Speech started');
    };

    utterance.onend = () => {
        console.log('Speech ended');
    };
}

// Status helper
function updateStatus(message, type) {
    statusDiv.textContent = message;
    statusDiv.className = `alert alert-${type}`;
}

// Mobile Safari workaround - tap to play audio
if (isMobileSafari) {
    priceDisplay.addEventListener('click', () => {
        if (lastAnnouncement && speechEnabled.checked) {
            console.log('Mobile tap detected, playing announcement');
            speak(lastAnnouncement);
        }
    });
}

// Test speech synthesis on page load
window.addEventListener('load', () => {
    if (!synth) {
        alert('Text-to-speech is not supported in your browser');
    }
});
