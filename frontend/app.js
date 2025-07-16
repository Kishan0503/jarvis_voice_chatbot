// Get references to DOM elements
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");

// Global state variables
let speechRecognitionInstance = null; // Store the recognition instance
let authToken = localStorage.getItem('authToken');
let userEmail = localStorage.getItem('userEmail');
let currentAgent = localStorage.getItem('currentAgent');

// Show/hide auth forms
function toggleAuthForms() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    loginForm.classList.toggle('hidden');
    registerForm.classList.toggle('hidden');
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    // Get form inputs
    const email = document.getElementById('login-email')?.value;
    const password = document.getElementById('login-password')?.value;

    if (!email || !password) {
        alert('Please enter both email and password');
        return;
    }

    try {
        // Show loading state
        const loginButton = event.target.querySelector('button[type="submit"]');
        if (loginButton) {
            loginButton.disabled = true;
            loginButton.textContent = 'Logging in...';
        }

        const response = await fetch('/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'username': email,
                'password': password,
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Store auth data
            authToken = data.access_token;
            userEmail = email;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('userEmail', userEmail);

            // Update UI elements after successful login
            initializeUIAfterLogin();
        } else {
            throw new Error(data.detail || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert(error.message || 'An error occurred during login. Please try again.');
    } finally {
        // Reset loading state
        const loginButton = event.target.querySelector('button[type="submit"]');
        if (loginButton) {
            loginButton.disabled = false;
            loginButton.textContent = 'Login';
        }
    }
}

// Add this new function to handle UI initialization
function initializeUIAfterLogin() {
    const authContainer = document.getElementById('auth-container');
    const agentSelection = document.getElementById('agent-selection');
    const appHeader = document.getElementById('app-header');
    const userEmailDisplay = document.getElementById('user-email');
    const jarvisCard = document.getElementById('jarvis-card');
    const zaraCard = document.getElementById('zara-card');

    if (!authContainer || !agentSelection || !appHeader || !userEmailDisplay) {
        console.error('Required DOM elements not found');
        alert('An error occurred. Please refresh the page.');
        return;
    }

    // Hide auth container
    authContainer.style.opacity = '0';
    setTimeout(() => {
        authContainer.classList.add('hidden');
        
        // Show and update header
        appHeader.classList.remove('hidden');
        userEmailDisplay.textContent = userEmail;
        setTimeout(() => {
            appHeader.style.opacity = '1';
        }, 50);

        // Show and animate agent selection
        agentSelection.classList.remove('hidden');
        setTimeout(() => {
            agentSelection.style.opacity = '1';
            agentSelection.style.transform = 'scale(1)';
            
            // Animate agent cards
            if (jarvisCard) {
                jarvisCard.style.opacity = '1';
                jarvisCard.style.transform = 'translateX(0)';
            }
            if (zaraCard) {
                zaraCard.style.opacity = '1';
                zaraCard.style.transform = 'translateX(0)';
            }
        }, 50);
    }, 300);
}

// Handle registration
async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                email,
                password,
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Registration successful! Please login.');
            // Reset form fields
            document.getElementById('register-username').value = '';
            document.getElementById('register-email').value = '';
            document.getElementById('register-password').value = '';
            toggleAuthForms();
        } else {
            // Check for specific error messages
            if (data.detail === "Email already registered") {
                alert('This email is already registered. Please login or use a different email.');
            } else {
                alert(data.detail || 'Registration failed. Please try again.');
            }
        }
    } catch (error) {
        console.error('Registration error:', error);
        alert('An error occurred during registration. Please try again.');
    }
}

// Handle logout
function handleLogout() {
    // Clear all storage
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('currentAgent');
    currentAgent = null;
    authToken = null;
    userEmail = null;
    
    // Get all required elements
    const voiceChatContainer = document.getElementById('voice-chat-container');
    const agentSelection = document.getElementById('agent-selection');
    const authContainer = document.getElementById('auth-container');
    const appHeader = document.getElementById('app-header');
    const jarvisCard = document.getElementById('jarvis-card');
    const zaraCard = document.getElementById('zara-card');
    
    // Reset agent selection state with proper transitions
    if (jarvisCard) {
        jarvisCard.style.opacity = '0';
        jarvisCard.style.transform = 'translateX(-100px)';
    }
    if (zaraCard) {
        zaraCard.style.opacity = '0';
        zaraCard.style.transform = 'translateX(100px)';
    }
    if (agentSelection) {
        agentSelection.classList.remove('show-selection');
        agentSelection.style.opacity = '0';
        setTimeout(() => {
            agentSelection.classList.add('hidden');
        }, 300);
    }
    
    // Stop any ongoing voice recognition or speech
    stopVoiceRecognition();
    window.speechSynthesis.cancel();
    
    // Hide voice chat if visible
    if (voiceChatContainer) {
        voiceChatContainer.classList.remove('show-chat');
        voiceChatContainer.style.opacity = '0';
        voiceChatContainer.style.transform = 'scale(0.95)';
        setTimeout(() => {
            voiceChatContainer.classList.add('hidden');
        }, 300);
    }
    
    // Hide header with fade out
    if (appHeader) {
        appHeader.style.opacity = '0';
        setTimeout(() => {
            appHeader.classList.add('hidden');
        }, 300);
    }
    
    // Show auth container with proper fade in
    if (authContainer) {
        // Reset form fields
        const loginEmail = document.getElementById('login-email');
        const loginPassword = document.getElementById('login-password');
        if (loginEmail) loginEmail.value = '';
        if (loginPassword) loginPassword.value = '';
        
        // Show login form, hide register form
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        if (loginForm) loginForm.classList.remove('hidden');
        if (registerForm) registerForm.classList.add('hidden');
        
        // Reset and fade in auth container
        authContainer.style.opacity = '0';
        authContainer.classList.remove('hidden');
        
        // Small delay to ensure proper transition
        setTimeout(() => {
            authContainer.style.opacity = '1';
            // Reset body theme
            document.body.className = '';
        }, 50);
    }
}

// Check authentication on page load
window.addEventListener('load', () => {
    if (authToken && userEmail) {
        const authContainer = document.getElementById('auth-container');
        const agentSelection = document.getElementById('agent-selection');
        const appHeader = document.getElementById('app-header');
        const userEmailDisplay = document.getElementById('user-email');

        if (authContainer && agentSelection && userEmailDisplay && appHeader) {
            // Show and setup header
            appHeader.classList.remove('hidden');
            appHeader.style.opacity = '1';
            userEmailDisplay.textContent = userEmail;
            
            // Hide auth and show agent selection
            authContainer.classList.add('hidden');
            agentSelection.classList.remove('hidden');
            agentSelection.classList.add('show-selection');
            
            // If agent was previously selected, show that interface
            const savedAgent = localStorage.getItem('currentAgent');
            if (savedAgent) {
                selectAgent(savedAgent);
            }
        }
    }
});

// Handle agent selection
function selectAgent(agent) {
    currentAgent = agent;
    localStorage.setItem('currentAgent', agent);
    
    const agentSelection = document.getElementById('agent-selection');
    const voiceChatContainer = document.getElementById('voice-chat-container');
    const jarvisChat = document.getElementById('jarvis-chat');
    const zaraChat = document.getElementById('zara-chat');
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    // Fade out agent selection
    agentSelection.classList.remove('show-selection');
    agentSelection.style.opacity = '0';
    agentSelection.style.transform = 'scale(0.95)';
    
    // Change background theme
    document.body.className = agent === 'jarvis' ? 'theme-jarvis' : 'theme-zara';
    
    setTimeout(() => {
        // Hide agent selection
        agentSelection.classList.add('hidden');
        
        // Reset agent selection styles
        agentSelection.style.opacity = '';
        agentSelection.style.transform = '';
        
        // Show voice chat container
        voiceChatContainer.classList.remove('hidden');
        voiceChatContainer.style.opacity = '1';
        voiceChatContainer.style.transform = 'scale(1)';
        
        jarvisChat.classList.toggle('hidden', agent !== 'jarvis');
        zaraChat.classList.toggle('hidden', agent !== 'zara');
        
        // Animate voice chat container
        setTimeout(() => {
            voiceChatContainer.classList.add('show-chat');
        }, 50);
    }, 300);
}

// Go back to agent selection
function backToSelection() {
    stopVoiceRecognition();
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const voiceChatContainer = document.getElementById('voice-chat-container');
    const agentSelection = document.getElementById('agent-selection');
    const jarvisCard = document.getElementById('jarvis-card');
    const zaraCard = document.getElementById('zara-card');
    
    // Reset background theme with transition
    document.body.className = '';
    
    // Fade out voice chat
    voiceChatContainer.classList.remove('show-chat');
    voiceChatContainer.style.opacity = '0';
    voiceChatContainer.style.transform = 'scale(0.95)';
    
    setTimeout(() => {
        // Hide voice chat
        voiceChatContainer.classList.add('hidden');
        
        // Reset voice chat container styles
        voiceChatContainer.style.opacity = '';
        voiceChatContainer.style.transform = '';
        
        // Show agent selection
        agentSelection.classList.remove('hidden');
        agentSelection.style.opacity = '1';
        agentSelection.style.transform = 'scale(1)';
        
        // Reset and show cards with animation
        jarvisCard.style.opacity = '1';
        zaraCard.style.opacity = '1';
        jarvisCard.style.transform = 'translateX(0)';
        zaraCard.style.transform = 'translateX(0)';
        
        setTimeout(() => {
            agentSelection.classList.add('show-selection');
            jarvisCard.classList.add('show-card');
            zaraCard.classList.add('show-card');
        }, 50);
    }, 300);
}

// Global variables for conversation state
let isConversationActive = false;
let isSpeaking = false;

// Voice recognition handling
function startVoiceInput(agent) {
    if (!authToken) {
        alert('Please login to continue.');
        return;
    }

    const statusElement = document.getElementById(`${agent}-status`);
    const agentImage = document.querySelector(`#${agent}-chat .relative img`);
    
    // Toggle conversation state
    if (isConversationActive) {
        stopVoiceRecognition();
        isConversationActive = false;
        statusElement.textContent = `Click on ${agent.charAt(0).toUpperCase() + agent.slice(1)} to start conversation`;
        return;
    }

    isConversationActive = true;
    const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
    statusElement.textContent = `${agentName} is listening...`;
    statusElement.classList.add('listening');
    
    if (window.webkitSpeechRecognition) {
        // Stop any existing recognition instance
        if (speechRecognitionInstance) {
            stopVoiceRecognition();
        }

        speechRecognitionInstance = new webkitSpeechRecognition();
        speechRecognitionInstance.continuous = false;
        speechRecognitionInstance.interimResults = false;
        speechRecognitionInstance.lang = 'en-US';

        speechRecognitionInstance.onstart = () => {
            const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
            statusElement.textContent = `${agentName} is listening...`;
            statusElement.classList.add('listening');
        };

        // Update error handling
        speechRecognitionInstance.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error === 'no-speech') {
                // Only restart if we're not already listening
                if (isConversationActive && !isSpeaking && !speechRecognitionInstance) {
                    startVoiceInput(agent);
                }
            } else {
                statusElement.textContent = 'Error occurred. Please try again.';
                statusElement.classList.remove('listening');
                isConversationActive = false;
                stopVoiceRecognition();
            }
        };

        // Update onend handler
        speechRecognitionInstance.onend = () => {
            if (isConversationActive && !isSpeaking && !statusElement.textContent.includes('thinking')) {
                setTimeout(() => {
                    if (isConversationActive && !isSpeaking && !speechRecognitionInstance) {
                        startVoiceInput(agent);
                    }
                }, 100);
            }
        };

        // Update the speechRecognitionInstance.onresult handler
        speechRecognitionInstance.onresult = async (event) => {
            const transcript = event.results[0][0].transcript;
            const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
            
            // Update status to thinking as soon as speech is recognized
            statusElement.textContent = `${agentName} is thinking...`;
            statusElement.classList.remove('listening');
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({ 
                        message: transcript,
                        agent: agent
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    speakResponse(data, agent);
                } else if (response.status === 401) {
                    handleLogout();
                    const errorMessage = {
                        audio_data: '', // This will be handled by text-to-speech
                        text: "Oops! Your session has expired. Please login again."
                    };
                    speakResponse(errorMessage, agent);
                } else {
                    throw new Error('Failed to get response');
                }
            } catch (error) {
                console.error('Error:', error);
                const errorMessage = {
                    audio_data: '', // This will be handled by text-to-speech
                    text: `Sorry! I'm having trouble connecting right now. Please try again in a moment.`
                };
                statusElement.textContent = 'Sorry! Something went wrong. Please try again.';
                speakResponse(errorMessage, agent);
            }
        };

        try {
            speechRecognitionInstance.start();
        } catch (error) {
            console.error('Speech recognition start error:', error);
            stopVoiceRecognition();
            startVoiceInput(agent);
        }
    } else {
        alert('Speech recognition is not supported in this browser.');
    }
}

function stopVoiceRecognition() {
    if (speechRecognitionInstance) {
        try {
            speechRecognitionInstance.stop();
        } catch (error) {
            console.error('Error stopping speech recognition:', error);
        }
        speechRecognitionInstance = null;
    }
    isConversationActive = false;
    isSpeaking = false;
    
    // Remove speaking animation if it's still active
    const jarvisImage = document.querySelector('#jarvis-chat .relative img');
    const zaraImage = document.querySelector('#zara-chat .relative img');
    if (jarvisImage) jarvisImage.classList.remove('speaking');
    if (zaraImage) zaraImage.classList.remove('speaking');
}

// Text-to-speech with ElevenLabs voices
function speakResponse(data, agent) {
    const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
    const statusElement = document.getElementById(`${agent}-status`);
    const agentImage = document.querySelector(`#${agent}-chat .relative img`);
    
    // Set speaking state
    isSpeaking = true;
    statusElement.textContent = `${agentName} is speaking...`;
    
    // Add speaking animation to the agent image
    agentImage.classList.add('speaking');

    // Create audio element if it doesn't exist
    let audioElement = document.getElementById('tts-audio');
    if (!audioElement) {
        audioElement = document.createElement('audio');
        audioElement.id = 'tts-audio';
        document.body.appendChild(audioElement);
    }

    // Stop any currently playing audio
    audioElement.pause();
    audioElement.currentTime = 0;

    // Check if this is an error message that needs text-to-speech
    if (!data.audio_data) {
        // Use browser's text-to-speech for error messages
        const utterance = new SpeechSynthesisUtterance(data.text);
        utterance.onend = () => {
            agentImage.classList.remove('speaking');
            isSpeaking = false;
            if (isConversationActive) {
                statusElement.textContent = `${agentName} is listening...`;
                if (speechRecognitionInstance) {
                    speechRecognitionInstance.start();
                } else {
                    startVoiceInput(agent);
                }
            } else {
                statusElement.textContent = `Click on ${agentName} to start conversation`;
            }
        };
        window.speechSynthesis.speak(utterance);
        return;
    }

    // Get the audio data
    const audioData = data.audio_data;
    if (!audioData) {
        console.error('No audio data received');
        statusElement.textContent = 'Error occurred while speaking. Please try again.';
        return;
    }

    // Convert base64 to blob and create object URL
    const audioBlob = base64ToBlob(audioData, 'audio/mp3');
    const audioUrl = URL.createObjectURL(audioBlob);
    audioElement.src = audioUrl;
    
    // Handle audio events
    audioElement.onended = () => {
        const agentImage = document.querySelector(`#${agent}-chat .relative img`);
        agentImage.classList.remove('speaking');
        isSpeaking = false;
            if (isConversationActive) {
                const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
                statusElement.textContent = `${agentName} is listening...`;
                // Resume listening after speaking
                if (speechRecognitionInstance) {
                    speechRecognitionInstance.start();
                } else {
                    startVoiceInput(agent);
                }
        } else {
            statusElement.textContent = `Click on ${agentName} to start conversation`;
        }
        // Clean up the object URL after playback
        URL.revokeObjectURL(audioUrl);
    };

    audioElement.onerror = (error) => {
        console.error('Audio playback error:', error);
        statusElement.textContent = 'Error occurred while speaking. Please try again.';
        statusElement.classList.remove('listening');
        URL.revokeObjectURL(audioUrl);
    };

    // Play the audio
    audioElement.play().catch(error => {
        console.error('Error playing audio:', error);
        statusElement.textContent = 'Error occurred while speaking. Please try again.';
        statusElement.classList.remove('listening');
        URL.revokeObjectURL(audioUrl);
    });
}

// Helper function to convert base64 to blob
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}

function createStarryBackground() {
    const starsContainer = document.createElement('div');
    starsContainer.className = 'stars';
    document.body.prepend(starsContainer);

    const numberOfStars = 100;

    for (let i = 0; i < numberOfStars; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        
        // Random position
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        
        // Random size between 1-3px
        const size = Math.random() * 2 + 1;
        
        // Random duration between 3-6s
        const duration = Math.random() * 3 + 3;
        
        star.style.cssText = `
            left: ${x}%;
            top: ${y}%;
            width: ${size}px;
            height: ${size}px;
            --duration: ${duration}s;
        `;
        
        starsContainer.appendChild(star);
    }
}

// Call this function when the page loads
window.addEventListener('load', createStarryBackground);