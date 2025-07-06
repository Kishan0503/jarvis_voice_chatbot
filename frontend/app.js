// Get references to DOM elements
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
// const loadingIndicator = document.getElementById('loading-indicator'); // REMOVED: No longer a static element

const textChatUI = document.getElementById('text-chat-ui');
const voiceChatUI = document.getElementById('voice-chat-ui');
const textModeBtn = document.getElementById('text-mode-btn');
const voiceModeBtn = document.getElementById('voice-mode-btn');
const voiceGifContainer = document.getElementById('voice-gif-container');
const voiceGif = document.getElementById('voice-gif');
const voiceStatus = document.getElementById('voice-status');
const voiceErrorMessage = document.getElementById('voice-error-message');
const voiceMicButton = document.getElementById('voice-mic-button');

// Define GIF URLs for different states
const GIF_URLS = {
    idle: "/static/Jarvis_img.gif", // REPLACE with your actual idle GIF
    listening: "/static/Jarvis_img.gif", // REPLACE with your actual listening GIF
    processing: "/static/Jarvis_img.gif", // REPLACE with your actual processing GIF
    speaking: "/static/Jarvis_img.gif", // REPLACE with your actual speaking GIF
    error: "/static/Jarvis_img.gif" // Optional: REPLACE with an error GIF
};

let currentUIMode = 'text'; // Default mode
let speechRecognitionInstance = null; // Store the recognition instance
let currentLoadingIndicator = null; // NEW: To store reference to the dynamically created loading indicator

// Initialize UI mode when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    switchUIMode('text'); // Start in text chat mode
});

/**
 * Switches between text and voice UI modes.
 * @param {string} mode - 'text' or 'voice'.
 */
function switchUIMode(mode) {
    currentUIMode = mode;

    if (mode === 'text') {
        textChatUI.classList.remove('hidden');
        textChatUI.classList.add('active-ui');
        voiceChatUI.classList.add('hidden');
        voiceChatUI.classList.remove('active-ui');

        textModeBtn.classList.add('active-tab');
        voiceModeBtn.classList.remove('active-tab');

        // Ensure voice recognition is stopped if switching from voice mode
        if (speechRecognitionInstance) {
            speechRecognitionInstance.stop();
            speechRecognitionInstance = null;
        }
        resetVoiceVisuals(); // Reset voice GIF state
    } else { // mode === 'voice'
        voiceChatUI.classList.remove('hidden');
        voiceChatUI.classList.add('active-ui');
        textChatUI.classList.add('hidden');
        textChatUI.classList.remove('active-ui');

        voiceModeBtn.classList.add('active-tab');
        textModeBtn.classList.remove('active-tab');

        resetVoiceVisuals(); // Reset voice GIF state
    }
}

// Event listeners for UI switcher buttons
textModeBtn.addEventListener('click', () => switchUIMode('text'));
voiceModeBtn.addEventListener('click', () => switchUIMode('voice'));

/**
 * Appends a message to the chat box (only for text mode).
 * @param {string} sender - The sender of the message ('user' or 'bot').
 * @param {string} text - The text content of the message.
 */
function appendMessage(sender, text) {
    if (currentUIMode !== 'text') return; // Only append in text mode

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", "flex");

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("p-3", "rounded-lg", "shadow-md", "max-w-xs");

    if (sender === "user") {
        messageDiv.classList.add("justify-end");
        contentDiv.classList.add("bg-blue-600", "text-white");
    } else {
        messageDiv.classList.add("justify-start");
        contentDiv.classList.add("bg-gray-700", "text-gray-200");
    }

    contentDiv.textContent = text;
    messageDiv.appendChild(contentDiv);
    chatBox.appendChild(messageDiv);

    // Scroll to the bottom of the chat box
    chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Shows the loading indicator (only for text mode).
 * Creates a new loading indicator element and appends it.
 */
function showLoadingIndicator() {
    if (currentUIMode !== 'text') return;

    // Create the loading indicator structure dynamically
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'dynamic-loading-indicator'; // Give it an ID for easy removal
    loadingDiv.classList.add('flex', 'justify-start'); // Tailwind classes for layout

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("bg-black/40", "text-gray-300", "p-3", "rounded-lg", "shadow-md", "flex", "items-center", "space-x-1"); // space-x-1 for closer dots

    const typingIndicatorDiv = document.createElement('div');
    typingIndicatorDiv.classList.add('typing-indicator'); // Apply the new typing indicator CSS

    // Create the three pulsating dots
    for (let i = 0; i < 3; i++) {
        const dotSpan = document.createElement('span');
        typingIndicatorDiv.appendChild(dotSpan);
    }

    contentDiv.appendChild(typingIndicatorDiv);
    loadingDiv.appendChild(contentDiv);

    chatBox.appendChild(loadingDiv);
    currentLoadingIndicator = loadingDiv; // Store reference to the created element

    chatBox.scrollTop = chatBox.scrollHeight; // Scroll to show indicator
}

/**
 * Hides the loading indicator (only for text mode).
 * Removes the dynamically created loading indicator element.
 */
function hideLoadingIndicator() {
    if (currentUIMode !== 'text') return;

    if (currentLoadingIndicator && currentLoadingIndicator.parentNode) {
        currentLoadingIndicator.parentNode.removeChild(currentLoadingIndicator);
        currentLoadingIndicator = null; // Clear the reference
    }
}

/**
 * Updates the voice GIF's visual state and status message.
 * @param {string} state - 'idle', 'listening', 'processing', 'speaking', 'error'.
 * @param {string} message - The message to display in voice status.
 */
function updateVoiceVisuals(state, message = '') {
    // Remove all state classes from the container
    voiceGifContainer.classList.remove('listening', 'processing', 'speaking', 'error');

    // Set the GIF source based on the state
    voiceGif.src = GIF_URLS[state] || GIF_URLS.idle; // Fallback to idle GIF

    // Update status message and error visibility
    voiceStatus.textContent = message;
    voiceErrorMessage.classList.add('hidden'); // Hide error message by default

    if (state === 'listening') {
        voiceGifContainer.classList.add('listening'); // Add class for glow animation
        voiceStatus.textContent = message || "Listening...";
    } else if (state === 'processing') {
        voiceGifContainer.classList.add('processing'); // Add class for glow animation
        voiceStatus.textContent = message || "Jarvis is thinking...";
    } else if (state === 'speaking') {
        voiceGifContainer.classList.add('speaking'); // Add class for glow animation
        voiceStatus.textContent = message || "Jarvis is speaking...";
    } else if (state === 'error') {
        voiceGifContainer.classList.add('error'); // Add class for glow animation
        voiceErrorMessage.textContent = message || "An error occurred.";
        voiceErrorMessage.classList.remove('hidden');
        voiceStatus.textContent = "Please try again.";
    } else { // idle
        voiceStatus.textContent = message || "Click the microphone to speak";
    }
}

/**
 * Resets the voice GIF and status to its idle state.
 */
function resetVoiceVisuals() {
    updateVoiceVisuals('idle', "Click the microphone to speak");
}

/**
 * Sends a message from the user to the API and handles the response.
 * This function is used by both text and voice modes, but behaves differently.
 * @param {boolean} isTextMode - True if called from text mode, false if from voice mode.
 * @param {string} [transcript] - The transcribed text from voice input (only for voice mode).
 */
async function sendMessage(isTextMode = true, transcript = '') {
    let input;
    if (isTextMode) {
        input = userInput.value.trim();
        if (!input) return;
        appendMessage("user", input); // Display user message immediately in text mode
        userInput.value = ""; // Clear input field
        showLoadingIndicator(); // Show loading spinner in text mode
    } else {
        input = transcript; // Use the provided transcript for voice mode
        if (!input) {
            updateVoiceVisuals('error', "No speech detected. Please try again.");
            return;
        }
        updateVoiceVisuals('processing', "Jarvis is thinking..."); // Update GIF for voice mode
    }

    try {
        const res = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: input }),
        });

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();

        if (isTextMode) {
            hideLoadingIndicator(); // Hide loading spinner in text mode
            appendMessage("bot", data.reply); // Display bot response in text mode
        } else {
            // Voice mode: directly speak the response and update GIF
            speakText(data.reply); // speakText will handle GIF state and reset
        }

    } catch (error) {
        console.error("Error sending message to API:", error);
        if (isTextMode) {
            hideLoadingIndicator(); // Hide loading spinner even on error
            appendMessage("bot", "Oops! Jarvis encountered an error. Please try again later.");
        } else {
            updateVoiceVisuals('error', "Jarvis encountered an error. Please check console.");
            speakText("Oops! Jarvis encountered an error. Please try again later."); // Speak error in voice mode
        }
    }
}

// Text-to-Speech (TTS)
/**
 * Speaks the given text.
 * @param {string} text - The text to speak.
 */
function speakText(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);

        if (currentUIMode === 'voice') {
            updateVoiceVisuals('speaking', "Jarvis is speaking...");
            utterance.onend = () => {
                resetVoiceVisuals(); // Reset after speaking
            };
            utterance.onerror = (event) => {
                console.error("SpeechSynthesisUtterance.onerror", event);
                updateVoiceVisuals('error', "Speech playback failed.");
                resetVoiceVisuals(); // Reset on error
            };
            // Adding a small timeout to ensure CSS class has time to apply before speech starts
            setTimeout(() => {
                speechSynthesis.speak(utterance);
            }, 50); // 50ms delay
        } else {
            // If in text mode, speak immediately without GIF state changes
            speechSynthesis.speak(utterance);
        }
    } else {
        console.warn("Text-to-Speech not supported in this browser.");
        if (currentUIMode === 'voice') {
            updateVoiceVisuals('error', "Text-to-Speech not supported.");
        }
    }
}

/**
 * Initiates voice input.
 * @param {boolean} isTextMode - True if voice input is for text mode, false for voice-only mode.
 */
function startVoiceInput(isTextMode) {
    // Stop any existing recognition instance if active
    if (speechRecognitionInstance) {
        speechRecognitionInstance.stop();
        speechRecognitionInstance = null;
        if (!isTextMode) { // If stopping in voice mode, reset GIF
            resetVoiceVisuals();
        }
        return; // Exit if already listening and clicked again to stop
    }

    // Check for Web Speech API support
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        const msg = "Voice input is not supported by your browser.";
        if (isTextMode) {
            appendMessage("bot", msg);
        } else {
            updateVoiceVisuals('error', msg);
        }
        console.warn(msg);
        return;
    }

    const recognition = new (window.webkitSpeechRecognition || window.SpeechRecognition)();
    recognition.lang = "en-US";
    recognition.interimResults = false; // Get final results only
    recognition.maxAlternatives = 1; // Get only the most probable result
    speechRecognitionInstance = recognition; // Store the instance

    if (isTextMode) {
        appendMessage("bot", "Listening..."); // Indicate that listening has started in text mode
    } else {
        updateVoiceVisuals('listening', "Listening..."); // Update GIF for voice mode
    }

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        if (isTextMode) {
            userInput.value = transcript;
            sendMessage(true); // Send message for text mode
        } else {
            sendMessage(false, transcript); // Pass transcript to sendMessage for voice mode
        }
        speechRecognitionInstance = null; // Clear instance after successful result
    };

    recognition.onerror = function (event) {
        console.error("Voice input failed:", event.error);
        let errorMessage = "Voice input failed.";
        if (event.error === 'not-allowed') {
            errorMessage = "Microphone access denied. Please allow microphone access in your browser settings.";
        } else if (event.error === 'no-speech') {
            errorMessage = "No speech detected. Please try speaking louder or clearer.";
        } else if (event.error === 'aborted') {
            errorMessage = "Voice input was cancelled.";
        } else if (event.error === 'network') {
            errorMessage = "Network error. Please check your internet connection.";
        }

        if (isTextMode) {
            appendMessage("bot", errorMessage); // Display error in chat
        } else {
            updateVoiceVisuals('error', errorMessage); // Display error in voice status
        }
        speechRecognitionInstance = null; // Clear instance on error
    };

    recognition.onend = function() {
        // This event fires when recognition service disconnects.
        // If the instance is still active here, it means it ended without a result or error.
        if (speechRecognitionInstance) {
            console.log("Voice recognition ended unexpectedly or was stopped.");
            if (!isTextMode) {
                resetVoiceVisuals(); // Reset GIF if in voice mode and recognition ended without a result
            }
        }
        speechRecognitionInstance = null; // Ensure instance is cleared
    };

    try {
        recognition.start();
    } catch (e) {
        console.error("Error starting voice recognition:", e);
        const err_msg = "Could not start voice input. Please ensure your microphone is connected and permissions are granted.";
        if (isTextMode) {
            appendMessage("bot", err_msg);
        } else {
            updateVoiceVisuals('error', err_msg);
        }
        speechRecognitionInstance = null; // Clear instance on error
    }
}

// Event listener for sending message on Enter key press in text mode
userInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter' && currentUIMode === 'text') {
        sendMessage(true);
    }
});