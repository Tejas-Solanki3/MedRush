from flask import Flask, request, jsonify, send_from_directory, render_template
import google.generativeai as genai
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import os
from bson import ObjectId
from dotenv import load_dotenv
import datetime
import re

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# MongoDB setup
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGODB_URI)
db = client['medrush_db']
users_collection = db['users']
appointments_collection = db['appointments']

# Create indexes for faster queries
users_collection.create_index('username', unique=True)
users_collection.create_index('email', unique=True)
appointments_collection.create_index([('user_id', 1), ('date', 1)])

# Login manager setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure Gemini AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_data['_id'])

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user_data = users_collection.find_one({'username': username})
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data)
            login_user(user)
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'username': username
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during login'
        }), 500

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        print(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during logout'
        }), 500

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        print(f"Received signup data: {data}")  # Debug print
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Validate input
        if not all([username, email, password]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all fields'
            }), 400

        # Check password length
        if len(password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }), 400

        # Check if username already exists
        if users_collection.find_one({'username': username}):
            return jsonify({
                'success': False,
                'message': 'Username already taken'
            }), 400

        # Check if email already exists
        if users_collection.find_one({'email': email}):
            return jsonify({
                'success': False,
                'message': 'Email already registered'
            }), 400

        # Create new user
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.datetime.utcnow(),
            'profile': {
                'name': '',
                'age': '',
                'gender': '',
                'phone': '',
                'address': '',
                'medical_history': []
            }
        }

        print(f"Inserting user data: {user_data}")  # Debug print
        result = users_collection.insert_one(user_data)
        
        if result.inserted_id:
            # Create User instance
            user = User(user_data)
            login_user(user)
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully! Please complete your profile.',
                'redirect': '/profile'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create account'
            }), 500

    except Exception as e:
        print(f"Signup error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred during signup: {str(e)}'
        }), 500

@app.route('/book-appointment', methods=['POST'])
@login_required
def book_appointment():
    data = request.json
    try:
        appointment = {
            'date': datetime.datetime.fromisoformat(data.get('date')),
            'doctor': data.get('doctor'),
            'user_id': ObjectId(current_user.get_id()),
            'status': 'pending',
            'created_at': datetime.datetime.utcnow()
        }
        
        appointments_collection.insert_one(appointment)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Booking error: {e}")
        return jsonify({'success': False, 'message': 'Failed to book appointment'}), 500

@app.route('/ai-assistant')
def ai_assistant():
    return send_from_directory('pages', 'ai-assistant.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        print("Chat endpoint called")
        data = request.get_json()
        
        if not data:
            print("No JSON data received")
            return jsonify({
                'error': 'No data provided',
                'success': False
            }), 400
            
        user_message = data.get('message')
        language = data.get('language', 'english')
        
        if not user_message:
            print("No message provided")
            return jsonify({
                'error': 'No message provided',
                'success': False
            }), 400
            
        print(f"Processing message: {user_message[:50]}...")
        print(f"Selected language: {language}")

        try:
            model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            print(f"Error initializing Gemini model: {str(e)}")
            return jsonify({
                'error': 'Failed to initialize AI model',
                'success': False
            }), 500

        # Add medical context and safety parameters
        safety_settings = {
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH"
        }
        
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.8,
            top_k=40,
            max_output_tokens=2048,
        )

        # Update context with medical disclaimer
        medical_context = """IMPORTANT: This is a legitimate medical consultation assistant. 
        The responses will contain professional medical terminology and discussions about health conditions.
        All content is intended to be informative and educational."""
        
        if language == 'english':
            context = f"""{medical_context}
            You are MedRush's AI Health Assistant providing professional medical information. Your responses should be:
            1. Professional and clinical
            2. Evidence-based and accurate
            3. Using appropriate medical terminology
            4. Structured in bullet points
            
            Focus on providing factual medical information and guidance."""
        else:
            context = f"""{medical_context}
            You are MedRush's AI Health Assistant providing professional medical information in Hinglish. Your responses should be:
            1. Professional and clinical
            2. Evidence-based and accurate
            3. Using appropriate medical terminology with Hinglish explanations
            4. Structured in bullet points
            
            Focus on providing factual medical information and guidance."""

        prompt = f"""{context}

        Medical Query: {user_message}

        Provide a clear medical response with SEPARATE bullet points for each piece of information:

        **Initial Assessment**
        • Greet the patient and acknowledge their specific symptoms
        • Provide your understanding of their condition

        **Clinical Information**
        • Define what this medical condition is
        • Explain the main causes of this condition
        • List the most common symptoms
        • Describe how long this condition typically lasts
        • Mention factors that can make it worse

        **Medical Recommendations**
        • List the most effective immediate relief steps
        • Name specific helpful medications
        • Explain proper medication dosage
        • Describe important self-care steps
        • Suggest helpful lifestyle changes

        **Precautions & Warning Signs**
        • List specific symptoms that indicate worsening
        • Name emergency warning signs
        • State when to seek immediate medical care
        • Mention specific conditions that require extra caution

        FORMATTING RULES:
        1. Each bullet point must be ONE complete sentence
        2. Start each point with • and end with a period
        3. NO sub-points or nested information
        4. NO lists within bullet points
        5. Keep each point clear and separate
        6. Add blank line after each section header"""

        try:
            # Generate response with safety settings
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.9,
                    top_k=30,
                    max_output_tokens=2048,
                    candidate_count=1,
                    stop_sequences=["FORMATTING", "RULES:", "Note:", "Remember:"]
                ),
                safety_settings=safety_settings
            )

            if not response or not response.candidates:
                raise ValueError("No response generated")

            try:
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            parts = candidate.content.parts
                            if parts:
                                # Get raw response and clean up
                                raw_response = ' '.join(str(part) for part in parts)
                                
                                # Clean up escape sequences and initial formatting
                                cleaned_response = raw_response.replace('\\n', '\n').replace('\\', '')
                                
                                # Process the response section by section
                                sections = []
                                current_section = []
                                
                                # Split into lines and process each line
                                lines = cleaned_response.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    
                                    # Check if this is a section header
                                    if '**' in line:
                                        # If we have content in current section, add it
                                        if current_section:
                                            sections.extend(current_section)
                                            sections.append('')  # Add blank line between sections
                                            current_section = []
                                        
                                        # Add the header
                                        header = line.strip()
                                        if not header.startswith('**'):
                                            header = f"**{header.replace('*', '')}**"
                                        current_section.append(header)
                                        current_section.append('')  # Add blank line after header
                                    else:
                                        # Process content line
                                        content = line.strip()
                                        if content:
                                            # Remove any existing bullets and clean up
                                            content = re.sub(r'^[-•*]\s*', '', content)
                                            
                                            # Handle lines with colons (usually lists)
                                            if ':' in content:
                                                main_point, sub_points = content.split(':', 1)
                                                # Add the main point if it's meaningful
                                                if len(main_point.strip()) > 5:  # Avoid short headers
                                                    current_section.append(f"• {main_point.strip()}")
                                                
                                                # Process sub-points
                                                for sub_point in sub_points.split('.'):
                                                    sub_point = sub_point.strip()
                                                    if sub_point and not sub_point.isspace():
                                                        # Clean up the sub-point
                                                        sub_point = re.sub(r'^[-•*]\s*', '', sub_point)
                                                        if not sub_point[-1] in '.!?':
                                                            sub_point += '.'
                                                        current_section.append(f"• {sub_point}")
                                            else:
                                                # Regular line
                                                content = content.strip()
                                                if content and not content.isspace():
                                                    if not content[-1] in '.!?':
                                                        content += '.'
                                                    current_section.append(f"• {content}")
                                
                                # Add the last section
                                if current_section:
                                    sections.extend(current_section)
                                
                                # Join all sections with proper spacing
                                ai_response = '\n'.join(sections)
                                
                                # Clean up any remaining formatting issues
                                ai_response = re.sub(r'\n{3,}', '\n\n', ai_response)  # Fix multiple blank lines
                                ai_response = re.sub(r'•\s+•', '•', ai_response)      # Fix multiple bullets
                                ai_response = re.sub(r'\*{3,}', '**', ai_response)    # Fix multiple asterisks
                                ai_response = re.sub(r':\s*\n', ':\n', ai_response)   # Fix colon spacing
                                ai_response = re.sub(r'\s*\.\s*\n', '.\n', ai_response)  # Fix period spacing
                                
                                # Add disclaimer with proper spacing
                                disclaimer = "\n\nIMPORTANT: This information is for educational purposes only and should not replace professional medical advice. Please consult a healthcare provider for diagnosis and treatment."
                                if language == 'hinglish':
                                    disclaimer = "\n\nZARURI SUCHNA: Yeh jankari sirf educational purposes ke liye hai aur doctor ki professional salah ka replacement nahi hai. Diagnosis aur treatment ke liye kripya doctor se sampark karein."
                                
                                return jsonify({
                                    'response': ai_response + disclaimer,
                                    'success': True
                                })
                            else:
                                raise ValueError("No content parts in response")
                        else:
                            raise ValueError("No parts attribute in content")
                    else:
                        raise ValueError("No content in candidate")
                else:
                    raise ValueError("No valid candidates in response")
                
            except Exception as e:
                print(f"Error processing response: {str(e)}")
                raise ValueError(f"Failed to process response: {str(e)}")

        except Exception as e:
            print(f"Error generating or processing response: {str(e)}")
            # Try one more time with a simplified prompt
            try:
                simplified_response = model.generate_content(
                    f"{context}\n\nProvide a brief medical response about: {user_message}\n\n",
                    generation_config=genai.types.GenerationConfig(temperature=0.2),
                    safety_settings=safety_settings
                )
                
                if simplified_response and simplified_response.candidates:
                    return jsonify({
                        'response': simplified_response.candidates[0].content.parts[0] + disclaimer,
                        'success': True
                    })
                else:
                    raise ValueError("Failed to generate simplified response")
                    
            except Exception as backup_error:
                return jsonify({
                    'error': f'Failed to generate response: {str(backup_error)}',
                    'success': False
                }), 500
        
    except Exception as e:
        print(f"Unexpected error in chat endpoint: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}',
            'success': False
        }), 500

@app.route('/profile')
@login_required
def profile():
    user_data = users_collection.find_one({'_id': ObjectId(current_user.get_id())})
    return render_template('profile.html', user=user_data)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        # Update user profile
        result = users_collection.update_one(
            {'_id': ObjectId(current_user.get_id())},
            {'$set': {
                'profile.name': data.get('name'),
                'profile.age': data.get('age'),
                'profile.gender': data.get('gender'),
                'profile.phone': data.get('phone'),
                'profile.address': data.get('address'),
                'profile.medical_history': data.get('medical_history', [])
            }}
        )
        
        if result.modified_count:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No changes made to profile'
            })
            
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update profile'
        }), 500

@app.context_processor
def utility_processor():
    def get_user_profile():
        if current_user.is_authenticated:
            return current_user.user_data.get('profile', {})
        return {}
    return dict(get_user_profile=get_user_profile)

if __name__ == '__main__':
    # Verify MongoDB connection
    try:
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print("❌ Failed to connect to MongoDB:", e)
        
    # Run the Flask app
    app.run(host='0.0.0.0', port=8000, debug=True)