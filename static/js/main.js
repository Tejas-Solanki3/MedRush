// Authentication Functions
function openLoginModal() {
    const signupModal = bootstrap.Modal.getInstance(document.getElementById('signupModal'));
    if (signupModal) {
        signupModal.hide();
    }
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();
}

function openSignupModal() {
    const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
    if (loginModal) {
        loginModal.hide();
    }
    const signupModal = new bootstrap.Modal(document.getElementById('signupModal'));
    signupModal.show();
}

async function login(event) {
    if (event) event.preventDefault();
    
    const username = document.getElementById('login-username')?.value;
    const password = document.getElementById('login-password')?.value;

    if (!username || !password) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Login successful! Welcome back, ' + data.username, 'success');
            // Close the modal
            const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            if (loginModal) {
                loginModal.hide();
            }
            // Reload page to update navigation
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.message || 'Login failed', 'danger');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('An error occurred during login. Please try again.', 'danger');
    }
}

async function signup(event) {
    if (event) event.preventDefault();
    
    const username = document.getElementById('signup-username')?.value;
    const email = document.getElementById('signup-email')?.value;
    const password = document.getElementById('signup-password')?.value;

    if (!username || !email || !password) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'warning');
        return;
    }

    // Validate password length
    if (password.length < 8) {
        showAlert('Password must be at least 8 characters long', 'warning');
        return;
    }

    try {
        const response = await fetch('/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Account created successfully! Redirecting to profile setup...', 'success');
            // Close the modal
            const signupModal = bootstrap.Modal.getInstance(document.getElementById('signupModal'));
            if (signupModal) {
                signupModal.hide();
            }
            // Redirect to profile page after a short delay
            setTimeout(() => {
                window.location.href = '/profile';
            }, 1500);
        } else {
            showAlert(data.message || 'Signup failed', 'danger');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showAlert('An error occurred during signup. Please try again.', 'danger');
    }
}

async function updateProfile(event) {
    event.preventDefault();
    
    const medicalHistory = document.getElementById('medical-history').value
        .split('\n')
        .filter(item => item.trim());
    
    const profileData = {
        name: document.getElementById('name').value,
        age: document.getElementById('age').value,
        gender: document.getElementById('gender').value,
        phone: document.getElementById('phone').value,
        address: document.getElementById('address').value,
        medical_history: medicalHistory
    };

    try {
        const response = await fetch('/update_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Profile updated successfully!', 'success');
        } else {
            showAlert(data.message || 'Failed to update profile', 'danger');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showAlert('Failed to update profile. Please try again.', 'danger');
    }
}

async function logout() {
    fetch('/logout', { method: 'POST' })
        .then(() => {
            showAlert('Logged out successfully!', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        })
        .catch(error => {
            console.error('Logout error:', error);
            showAlert('Failed to logout. Please try again.', 'danger');
        });
}

// Appointment Booking
async function bookAppointment(event) {
    if (event) event.preventDefault();
    const date = document.getElementById('appointment-date')?.value;
    const doctor = document.getElementById('doctor-select')?.value;
    const time = document.getElementById('appointment-time')?.value;

    if (!date || !doctor || !time) {
        showAlert('Please fill in all appointment details', 'error');
        return;
    }

    try {
        const response = await fetch('/book-appointment', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date, doctor, time })
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('Appointment booked successfully!', 'success');
            location.reload();
        } else {
            showAlert(data.message || 'Failed to book appointment', 'error');
        }
    } catch (error) {
        console.error('Booking error:', error);
        showAlert('Failed to book appointment', 'error');
    }
}

// Feature Functions
async function findDoctor(event) {
    if (event) event.preventDefault();
    const specialty = document.getElementById('specialty-select')?.value;
    const location = document.getElementById('location-input')?.value;

    if (!specialty || !location) {
        showAlert('Please select specialty and location', 'error');
        return;
    }

    try {
        // Here you would typically make an API call to search doctors
        showAlert('Finding doctors in your area...', 'info');
        // Simulate loading
        const doctorsList = document.getElementById('doctors-list');
        if (doctorsList) {
            doctorsList.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div></div>';
            // Add mock doctors after delay
            setTimeout(() => {
                displayDoctors([
                    { name: 'Dr. Smith', specialty: 'Cardiology', rating: 4.5 },
                    { name: 'Dr. Johnson', specialty: 'Pediatrics', rating: 4.8 },
                    // Add more mock doctors
                ]);
            }, 1000);
        }
    } catch (error) {
        console.error('Find doctor error:', error);
        showAlert('Failed to find doctors', 'error');
    }
}

async function bookAmbulance(event) {
    if (event) event.preventDefault();
    const location = document.getElementById('emergency-location')?.value;
    const contact = document.getElementById('emergency-contact')?.value;

    if (!location || !contact) {
        showAlert('Please provide location and contact details', 'error');
        return;
    }

    try {
        showAlert('Dispatching emergency services...', 'info');
        // Simulate ambulance booking
        setTimeout(() => {
            showAlert('Emergency services have been dispatched to your location!', 'success');
        }, 1500);
    } catch (error) {
        console.error('Emergency booking error:', error);
        showAlert('Failed to book emergency services', 'error');
    }
}

// Stats Counter Animation
function animateStats() {
    const stats = document.querySelectorAll('.stat-number[data-target]');
    
    stats.forEach(stat => {
        const target = parseInt(stat.getAttribute('data-target'));
        const duration = 2000; // Animation duration in milliseconds
        const step = target / (duration / 16); // Update every 16ms (60fps)
        let current = 0;
        
        const updateCounter = () => {
            current += step;
            if (current < target) {
                stat.textContent = Math.ceil(current) + '+';
                requestAnimationFrame(updateCounter);
            } else {
                stat.textContent = target + '+';
            }
        };
        
        updateCounter();
    });
}

// Initialize stats animation when the section is in view
const statsSection = document.querySelector('.stats-section');
if (statsSection) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateStats();
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    observer.observe(statsSection);
}

// Helper Functions
function showAlert(message, type = 'info') {
    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);

    // Add animation classes
    setTimeout(() => alertDiv.classList.add('show'), 100);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

function displayDoctors(doctors) {
    const doctorsList = document.getElementById('doctors-list');
    if (!doctorsList) return;

    doctorsList.innerHTML = doctors.map(doctor => `
        <div class="card mb-3">
            <div class="card-body">
                <h5 class="card-title">${doctor.name}</h5>
                <p class="card-text">
                    <span class="badge bg-primary">${doctor.specialty}</span>
                    <span class="ms-2">⭐ ${doctor.rating}</span>
                </p>
                <button class="btn btn-primary" onclick="bookAppointment(event)">Book Appointment</button>
            </div>
        </div>
    `).join('');
}

// Intersection Observer for animations
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('show');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe elements with animation classes
document.addEventListener('DOMContentLoaded', () => {
    // Animate elements on scroll
    const animatedElements = document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .bounce-in');
    animatedElements.forEach(el => observer.observe(el));

    // Smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Initialize features based on current page
    if (window.location.pathname.includes('virtual-consultation')) {
        initializeVirtualRoom();
    } else if (window.location.pathname.includes('book-ambulance')) {
        initializeMap();
    } else if (window.location.pathname.includes('ai-assistant')) {
        chatAssistant.init();
    }

    // Initialize all interactive elements
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const appointmentForm = document.getElementById('appointment-form');
    const findDoctorForm = document.getElementById('find-doctor-form');
    const ambulanceForm = document.getElementById('ambulance-form');
    const logoutBtn = document.getElementById('logout-btn');
    const updateProfileForm = document.getElementById('update-profile-form');

    if (loginForm) loginForm.addEventListener('submit', login);
    if (signupForm) signupForm.addEventListener('submit', signup);
    if (appointmentForm) appointmentForm.addEventListener('submit', bookAppointment);
    if (findDoctorForm) findDoctorForm.addEventListener('submit', findDoctor);
    if (ambulanceForm) ambulanceForm.addEventListener('submit', bookAmbulance);
    if (logoutBtn) logoutBtn.addEventListener('click', logout);
    if (updateProfileForm) updateProfileForm.addEventListener('submit', updateProfile);

    // Initialize tooltips and popovers if using Bootstrap
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
});

// Virtual Consultation Room
function initializeVirtualRoom() {
    const room = document.getElementById('virtual-room');
    if (room) {
        // Initialize WebRTC or any video chat service
        console.log('Initializing virtual consultation room...');
    }
}

// Ambulance Booking Map
function initializeMap() {
    if (document.getElementById('map')) {
        // Initialize Google Maps
        console.log('Initializing map...');
    }
}

// AI Chat Assistant
const chatAssistant = {
    messageContainer: null,
    userInput: null,
    chatForm: null,
    typingIndicator: null,
    currentLanguage: 'english', // Default language
    langToggle: null,
    langText: null,

    init() {
        console.log('Initializing AI Assistant');
        this.messageContainer = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.chatForm = document.getElementById('chat-form');
        this.langToggle = document.getElementById('langToggle');
        this.langText = document.getElementById('langText');

        if (this.messageContainer && this.userInput && this.chatForm) {
            // Clear any existing messages
            this.messageContainer.innerHTML = '';
            
            // Setup event listeners
            this.chatForm.addEventListener('submit', (e) => this.sendMessage(e));
            if (this.langToggle) {
                this.langToggle.addEventListener('click', () => this.toggleLanguage());
            }
            
            // Add welcome message
            this.addWelcomeMessage();
            console.log('Chat assistant initialized');
        } else {
            console.error('Chat container not found');
        }
    },

    toggleLanguage() {
        this.currentLanguage = this.currentLanguage === 'english' ? 'hinglish' : 'english';
        if (this.langText) {
            this.langText.textContent = this.currentLanguage === 'english' 
                ? "Switch to Hinglish" 
                : "Switch to English";
        }
        if (this.langToggle) {
            this.langToggle.classList.toggle('active');
        }
    },

    addWelcomeMessage() {
        const welcomeMessage = this.currentLanguage === 'english' 
            ? "Hello! I'm your AI Health Assistant. How can I help you today?"
            : "Hi! Main aapka AI Health Assistant hoon. Aaj main aapki kya help kar sakta hoon?";
        this.addMessage(welcomeMessage, 'ai');
    },

    createMessageElement(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        if (type === 'ai') {
            // Split the response into sections
            const sections = text.split(/\*\*([^*]+)\*\*/).filter(Boolean);
            
            for (let i = 0; i < sections.length; i += 2) {
                const sectionTitle = sections[i];
                const sectionContent = sections[i + 1] || '';

                const section = document.createElement('div');
                section.className = 'response-section';

                // Add section header
                const header = document.createElement('h4');
                header.textContent = sectionTitle.trim();
                section.appendChild(header);

                // Create bullet point list
                const ul = document.createElement('ul');
                ul.className = 'response-list';

                // Process content into bullet points
                const points = sectionContent
                    .split('\n')
                    .map(point => point.trim())
                    .filter(point => point && !point.toLowerCase().includes('important:'))
                    .map(point => point.replace(/^[•\-*]\s*/, ''));

                // Add each point as a list item
                points.forEach(point => {
                    if (point) {
                        const li = document.createElement('li');
                        li.textContent = point;
                        ul.appendChild(li);
                    }
                });

                section.appendChild(ul);
                messageDiv.appendChild(section);
            }

            // Add disclaimer if present
            if (text.includes('IMPORTANT:') || text.includes('ZARURI SUCHNA:')) {
                const disclaimer = document.createElement('div');
                disclaimer.className = 'disclaimer';
                disclaimer.textContent = text.split(/IMPORTANT:|ZARURI SUCHNA:/)[1].trim();
                messageDiv.appendChild(disclaimer);
            }
        } else {
            // User message
            messageDiv.textContent = text;
        }

        return messageDiv;
    },

    showTypingIndicator() {
        if (!this.typingIndicator) {
            this.typingIndicator = document.createElement('div');
            this.typingIndicator.className = 'typing-indicator';

            const preFormat = `
                <div class="response-section">
                    <h4>Initial Assessment</h4>
                    <ul class="response-list">
                        <li>Analyzing your symptoms...</li>
                    </ul>
                </div>
                <div class="response-section">
                    <h4>Clinical Information</h4>
                    <ul class="response-list">
                        <li>Gathering medical details...</li>
                    </ul>
                </div>
                <div class="response-section">
                    <h4>Medical Recommendations</h4>
                    <ul class="response-list">
                        <li>Preparing treatment plan...</li>
                    </ul>
                </div>
                <div class="response-section">
                    <h4>Precautions & Warning Signs</h4>
                    <ul class="response-list">
                        <li>Identifying important warnings...</li>
                    </ul>
                </div>`;

            this.typingIndicator.innerHTML = preFormat;

            // Add typing dots
            const dots = document.createElement('div');
            dots.className = 'typing-dots';
            for (let i = 0; i < 3; i++) {
                const dot = document.createElement('span');
                dots.appendChild(dot);
            }
            this.typingIndicator.appendChild(dots);
        }
        this.messageContainer.appendChild(this.typingIndicator);
        this.scrollToBottom();
    },

    removeTypingIndicator() {
        if (this.typingIndicator && this.typingIndicator.parentNode) {
            this.typingIndicator.parentNode.removeChild(this.typingIndicator);
        }
    },

    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    },

    async sendMessage(e) {
        e.preventDefault();
        const message = this.userInput.value.trim();
        if (!message) return;

        // Clear input
        this.userInput.value = '';

        // Add user message
        this.addMessage(message, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    language: this.currentLanguage
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator();

            if (data.success) {
                // Format the response before adding
                let formattedResponse = this.formatAIResponse(data.response);
                this.addMessage(formattedResponse, 'ai');
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            this.removeTypingIndicator();
            const errorMsg = this.currentLanguage === 'english'
                ? `Sorry, there was an error: ${error.message}`
                : `Sorry, kuch problem ho gaya hai: ${error.message}`;
            this.addMessage(errorMsg, 'ai');
        }
    },

    formatAIResponse(response) {
        // Split into sections
        const sections = response.split(/\*\*([^*]+)\*\*/).filter(Boolean);
        let formatted = [];
        
        for (let i = 0; i < sections.length; i += 2) {
            if (i + 1 < sections.length) {
                const title = sections[i].trim();
                const content = sections[i + 1].trim();
                
                // Add section header
                formatted.push(`**${title}**`);
                
                // Process content into bullet points
                const points = content.split('\n')
                    .map(line => line.trim())
                    .filter(line => line)
                    .map(line => {
                        // Clean up any existing bullets
                        line = line.replace(/^[•\-*]\s*/, '');
                        // Add bullet point if not already present
                        return line.startsWith('•') ? line : `• ${line}`;
                    });
                
                formatted.push(points.join('\n'));
            }
        }
        
        // Add disclaimer
        const disclaimer = this.currentLanguage === 'english'
            ? "\n\nIMPORTANT: This information is for educational purposes only and should not replace professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
            : "\n\nIMPORTANT NOTE: Ye information sirf educational purpose ke liye hai aur ye doctor ki advice ki jagah nahi le sakti. Diagnosis aur treatment ke liye please kisi doctor se consult karein.";
        
        return formatted.join('\n\n') + disclaimer;
    },

    addMessage(text, type) {
        console.log(`Adding ${type} message: ${text.substring(0, 50)} + '...'`);
        const message = this.createMessageElement(text, type);
        this.messageContainer.appendChild(message);
        this.scrollToBottom();
    }
};

// Initialize chat assistant on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, checking for chat container');
    if (document.getElementById('chat-messages')) {
        console.log('Chat container found, initializing AI Assistant');
        chatAssistant.init();
    } else {
        console.error('Chat container not found');
    }
});

// Add loading animation
window.addEventListener('load', () => {
    document.body.classList.add('loaded');
});