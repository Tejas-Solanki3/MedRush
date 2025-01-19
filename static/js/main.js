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
    event.preventDefault();
    
    // Get the form data
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    
    // Clear any existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Validate inputs
    if (!username || !password) {
        showAlert('Please fill in all fields', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Login successful! Redirecting...', 'success');
            
            // Close the modal
            const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
            if (loginModal) {
                loginModal.hide();
            }
            
            // Redirect after a short delay
            setTimeout(() => {
                window.location.href = data.redirect || '/';
            }, 1500);
        } else {
            showAlert(data.message || 'Login failed. Please try again.', 'danger');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('An error occurred. Please try again later.', 'danger');
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

async function logout(event) {
    event.preventDefault();
    
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Logout successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            showAlert(data.message || 'Logout failed. Please try again.', 'danger');
        }
    } catch (error) {
        console.error('Logout error:', error);
        showAlert('An error occurred during logout. Please try again.', 'danger');
    }
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
    const alertPlaceholder = document.querySelector('.modal-body');
    if (!alertPlaceholder) return;
    
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show mb-3" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Insert alert at the top of the modal body
    alertPlaceholder.insertBefore(wrapper.firstChild, alertPlaceholder.firstChild);
    
    // Auto-dismiss after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            const alert = wrapper.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
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

    if (loginForm) loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        // Get the form data
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value.trim();
        
        // Clear any existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        // Validate inputs
        if (!username || !password) {
            showAlert('Please fill in all fields', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showAlert('Login successful! Redirecting...', 'success');
                
                // Close the modal
                const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
                if (loginModal) {
                    loginModal.hide();
                }
                
                // Redirect after a short delay
                setTimeout(() => {
                    window.location.href = data.redirect || '/';
                }, 1500);
            } else {
                showAlert(data.message || 'Login failed. Please try again.', 'danger');
            }
        } catch (error) {
            console.error('Login error:', error);
            showAlert('An error occurred. Please try again later.', 'danger');
        }
    });
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

    init() {
        this.messageContainer = document.getElementById('chat-messages');
        this.userInput = document.getElementById('user-input');
        this.chatForm = document.getElementById('chat-form');
        
        if (this.chatForm) {
            this.chatForm.addEventListener('submit', (e) => this.sendMessage(e));
        }
        
        this.addWelcomeMessage();
    },

    formatAIResponse(response) {
        // Clean the response of unnecessary asterisks
        response = response.replace(/\*\*/g, '');
        
        // Split response into sections
        const sections = {
            symptoms: [],
            precautions: [],
            preventions: [],
            other: []
        };
        
        const lines = response.split('\n');
        let currentSection = 'other';
        
        lines.forEach(line => {
            line = line.trim();
            if (!line) return;
            
            // Clean any remaining asterisks from individual lines
            line = line.replace(/\*/g, '');
            
            if (line.toLowerCase().includes('symptom')) {
                currentSection = 'symptoms';
                return;
            } else if (line.toLowerCase().includes('precaution')) {
                currentSection = 'precautions';
                return;
            } else if (line.toLowerCase().includes('prevent')) {
                currentSection = 'preventions';
                return;
            }
            
            sections[currentSection].push(line);
        });
        
        // Build formatted HTML
        let html = '';
        
        if (sections.symptoms.length) {
            html += '<h6 class="mt-2">Symptoms:</h6><ul>';
            sections.symptoms.forEach(item => html += `<li>${item}</li>`);
            html += '</ul>';
        }
        
        if (sections.precautions.length) {
            html += '<h6 class="mt-2">Precautions:</h6><ul>';
            sections.precautions.forEach(item => html += `<li>${item}</li>`);
            html += '</ul>';
        }
        
        if (sections.preventions.length) {
            html += '<h6 class="mt-2">Preventions:</h6><ul>';
            sections.preventions.forEach(item => html += `<li>${item}</li>`);
            html += '</ul>';
        }
        
        if (sections.other.length) {
            html += '<ul>';
            sections.other.forEach(item => html += `<li>${item}</li>`);
            html += '</ul>';
        }
        
        return html || response;
    },

    addMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <i class="fas fa-user text-primary me-2"></i>${message}
                </div>`;
        } else {
            // Format AI response with sections
            const sections = this.formatAIResponse(message);
            messageDiv.innerHTML = `
                <div class="message-content">
                    <i class="fas fa-robot text-primary me-2"></i>${sections}
                </div>`;
        }
        
        this.messageContainer.appendChild(messageDiv);
        this.scrollToBottom();
    },

    showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.textContent = '...';
        this.messageContainer.appendChild(typingIndicator);
    },

    removeTypingIndicator() {
        const typingIndicator = this.messageContainer.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    },

    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    },

    addWelcomeMessage() {
        this.addMessage('Hello! How can I assist you today?', 'ai');
    },

    async sendMessage(e) {
        e.preventDefault();
        const userMessage = this.userInput.value.trim();
        
        if (!userMessage) return;
        
        // Add user message
        this.addMessage(userMessage, 'user');
        this.userInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/chat', {  
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message: userMessage,
                    language: 'english'  
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator();
            
            if (data.response) {
                // Format the response and add it
                const formattedResponse = this.formatAIResponse(data.response);
                this.addMessage(formattedResponse, 'ai');
            } else {
                this.addMessage('I apologize, but I am having trouble understanding. Could you please rephrase your question?', 'ai');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.removeTypingIndicator();
            this.addMessage('I apologize, but I encountered an error. Please try again.', 'ai');
        }
        
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