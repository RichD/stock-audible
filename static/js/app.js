// Initialize WebSocket connection
const socket = io();

// DOM elements
const statusDiv = document.getElementById('status');
const tickerInput = document.getElementById('ticker');
const intervalSelect = document.getElementById('interval-minutes');
const announcementToggle = document.getElementById('announcement-toggle');
const audioStatus = document.getElementById('audio-status');
const priceDisplay = document.getElementById('price-display');
const tickerDisplay = document.getElementById('ticker-display');
const priceValue = document.getElementById('price-value');
const lastUpdate = document.getElementById('last-update');

// Speech synthesis
let synth = window.speechSynthesis;
let isAnnouncing = false;
let lastAnnouncement = '';

// Detect mobile Safari
const isMobileSafari = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

// Show Mobile Safari tip if on iOS
if (isMobileSafari) {
    const mobileTip = document.getElementById('mobile-safari-tip');
    if (mobileTip) {
        mobileTip.style.display = 'list-item';
    }
}

// Connection handlers
socket.on('connect', () => {
    updateStatus('Connected to server', 'connected');
});

socket.on('disconnect', () => {
    updateStatus('Disconnected from server', 'error');
    announcementToggle.classList.add('disabled');
});

socket.on('connected', (data) => {
    console.log(data.status);
    announcementToggle.classList.remove('disabled');
});

// Announcement handlers
socket.on('started', (data) => {
    isAnnouncing = true;
    const intervalMinutes = Math.round(data.interval / 60);
    updateStatus(`Announcing ${data.ticker} every ${intervalMinutes} minute${intervalMinutes !== 1 ? 's' : ''}`, 'connected');
    announcementToggle.classList.add('active');
    audioStatus.textContent = 'ON';
    audioStatus.classList.remove('off');
    audioStatus.classList.add('on');
    tickerInput.disabled = true;
    intervalSelect.disabled = true;
});

socket.on('stopped', (data) => {
    isAnnouncing = false;
    updateStatus('Announcements stopped', 'connected');
    announcementToggle.classList.remove('active');
    audioStatus.textContent = 'OFF';
    audioStatus.classList.remove('on');
    audioStatus.classList.add('off');
    tickerInput.disabled = false;
    intervalSelect.disabled = false;
    priceDisplay.style.display = 'none';
});

socket.on('price_update', (data) => {
    console.log('Received price update:', data);

    // Store announcement for mobile
    lastAnnouncement = data.announcement;

    // Update display
    tickerDisplay.textContent = data.ticker;
    priceValue.textContent = `$${data.price}`;

    const timeStr = new Date(data.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (isMobileSafari) {
        lastUpdate.textContent = `Last updated: ${timeStr} - Tap to hear`;
        priceDisplay.style.cursor = 'pointer';
    } else {
        lastUpdate.textContent = `Last updated: ${timeStr}`;
    }

    priceDisplay.style.display = 'block';

    // Announce (will only work on desktop, not mobile Safari)
    if (!isMobileSafari) {
        console.log('Calling speak()');
        speak(data.announcement);
    } else {
        console.log('Mobile Safari detected, waiting for user tap');
    }
});

socket.on('error', (data) => {
    updateStatus(`Error: ${data.message}`, 'error');
});

// Toggle button handler
announcementToggle.addEventListener('click', () => {
    if (announcementToggle.classList.contains('disabled')) {
        return;
    }

    if (!isAnnouncing) {
        startAnnouncements();
    } else {
        stopAnnouncements();
    }
});

function startAnnouncements() {
    const ticker = tickerInput.value.trim().toUpperCase();
    const intervalMinutes = parseInt(intervalSelect.value);
    const intervalSeconds = intervalMinutes * 60;

    if (!ticker) {
        updateStatus('Please enter a ticker symbol', 'error');
        return;
    }

    socket.emit('start_announcements', {
        ticker: ticker,
        interval: intervalSeconds
    });
}

function stopAnnouncements() {
    socket.emit('stop_announcements');
}

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
    // Update message text
    const messageSpan = statusDiv.querySelector('span:last-child');
    if (messageSpan) {
        messageSpan.textContent = message;
    } else {
        statusDiv.textContent = message;
    }

    // Update status class
    statusDiv.className = `status-message ${type}`;
}

// Mobile Safari workaround - tap to play audio
if (isMobileSafari) {
    priceDisplay.addEventListener('click', () => {
        if (lastAnnouncement) {
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
