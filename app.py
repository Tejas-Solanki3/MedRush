from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import re
from urllib.parse import quote_plus
import random
import json
from functools import wraps
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'super secret key'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure Google AI
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Upload folder configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MongoDB setup
db = None
try:
    # Get MongoDB connection string from environment variables
    mongodb_username = os.getenv('MONGODB_USERNAME')
    mongodb_password = os.getenv('MONGODB_PASSWORD')
    mongodb_cluster = os.getenv('MONGODB_CLUSTER')
    
    if not all([mongodb_username, mongodb_password, mongodb_cluster]):
        raise ValueError("Missing MongoDB credentials in environment variables")
    
    # Construct the connection string - using the correct format
    connection_string = f"mongodb+srv://{mongodb_username}:{mongodb_password}@{mongodb_cluster}.mongodb.net/?retryWrites=true&w=majority"
    print(f"Connecting to MongoDB with cluster: {mongodb_cluster}")
    
    # Create MongoDB client
    client = MongoClient(connection_string)
    
    # Select database
    db = client['medrush_db']
    print(f"Selected database: {db.name}")
    
    # Test connection
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
    
    # Initialize collections if they don't exist
    required_collections = ['users', 'appointments', 'emergency_calls', 'activities', 'admins', 'insurance', 'prescription_verifications', 'chat_history']
    existing_collections = db.list_collection_names()
    
    for collection in required_collections:
        if collection not in existing_collections:
            db.create_collection(collection)
            print(f"Created new collection: {collection}")
    
    # Create default admin user if not exists
    if db.admins.count_documents({}) == 0:
        admin = {
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'email': 'admin@medrush.com',
            'created_at': datetime.now(),
            'role': 'admin'
        }
        result = db.admins.insert_one(admin)
        print(f"Created default admin user with ID: {result.inserted_id}")
    
    # Create indexes if they don't exist
    print("\nCreating/Verifying indexes...")
    db.users.create_index([('username', 1)], unique=True)
    db.users.create_index([('email', 1)], unique=True)
    db.appointments.create_index([('user_id', 1), ('date', 1)])
    db.insurance.create_index([('user_id', 1), ('created_at', 1)])
    print("Indexes created/verified successfully")
    
    # Print collection statistics
    print("\nCollection statistics:")
    for collection in required_collections:
        count = db[collection].count_documents({})
        print(f"- {collection}: {count} documents")

except Exception as e:
    print(f"MongoDB Error: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    db = None
    raise e

if db is None:
    raise Exception("Failed to establish MongoDB connection")

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self._authenticated = True

    def is_authenticated(self):
        return self._authenticated

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get(user_id):
        try:
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            return User(user_data) if user_data else None
        except Exception as e:
            print(f"Error loading user: {e}")
            return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return render_template('admin_login.html')
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            print(f"Admin login attempt for username: {username}")  # Debug print
            
            # Find admin user
            admin = db.admins.find_one({'username': username})
            print(f"Found admin: {admin is not None}")  # Debug print
            
            if admin and check_password_hash(admin['password'], password):
                print("Admin password verified successfully")
                # Set session variables
                session['admin_logged_in'] = True
                session['admin_id'] = str(admin['_id'])
                session['admin_username'] = admin['username']
                
                # Log activity
                activity = {
                    'type': 'admin',
                    'description': f'Admin login: {username}',
                    'timestamp': datetime.now()
                }
                db.activities.insert_one(activity)
                print("Admin login activity logged")
                
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                print("Invalid admin credentials")
                flash('Invalid credentials!', 'danger')
                return redirect(url_for('admin_login'))
                
        return render_template('admin_login.html')
        
    except Exception as e:
        print(f"Admin login error: {str(e)}")
        flash('An error occurred during login', 'danger')
        return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('admin_login'))

def admin_required(f):
    @wraps(f)  # Use wraps to avoid function name conflicts
    def admin_check(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login first!', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return admin_check

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        # Get counts
        emergency_count = db.emergency_calls.count_documents({})
        appointment_count = db.appointments.count_documents({})
        doctor_count = db.users.count_documents({'role': 'doctor'})
        patient_count = db.users.count_documents({'role': 'patient'})

        # Get all patients with their details
        patients = list(db.users.find({'role': 'patient'}).sort('created_at', -1))
        
        # Enhance patient data
        for patient in patients:
            # Ensure profile exists
            if 'profile' not in patient:
                patient['profile'] = {
                    'first_name': '',
                    'last_name': '',
                    'age': '',
                    'gender': '',
                    'blood_type': '',
                    'phone': '',
                    'address': '',
                    'medical_history': [],
                    'allergies': [],
                    'medications': []
                }
            
            # Get last visit
            last_appointment = db.appointments.find_one(
                {'patient_id': patient['_id']},
                sort=[('date', -1)]
            )
            patient['last_visit'] = last_appointment['date'] if last_appointment else None
            
            # Set active status
            patient['active'] = True  # You can set this based on your criteria
            
            # Convert ObjectId to string for template
            patient['_id'] = str(patient['_id'])

        # Get recent emergency calls with detailed information
        emergency_calls = list(db.emergency_calls.find().sort('time', -1).limit(10))
        
        # Enhance emergency call data
        for call in emergency_calls:
            # Get patient details
            patient = db.users.find_one({'_id': call.get('patient_id')})
            if patient:
                call['patient_name'] = f"{patient.get('profile', {}).get('first_name', '')} {patient.get('profile', {}).get('last_name', '')}"
                call['patient_age'] = patient.get('profile', {}).get('age')
                call['blood_type'] = patient.get('profile', {}).get('blood_type')
                call['medical_history'] = patient.get('profile', {}).get('medical_history', [])
                call['allergies'] = patient.get('profile', {}).get('allergies', [])
                call['contact_number'] = patient.get('profile', {}).get('phone')
                call['email'] = patient.get('email')
            else:
                call['patient_name'] = 'Unknown'
            
            # Calculate time elapsed
            if call.get('time'):
                elapsed = datetime.now() - call['time']
                if elapsed.days > 0:
                    call['time_elapsed'] = f"{elapsed.days} days ago"
                elif elapsed.seconds > 3600:
                    call['time_elapsed'] = f"{elapsed.seconds // 3600} hours ago"
                else:
                    call['time_elapsed'] = f"{elapsed.seconds // 60} minutes ago"
            
            # Set status color
            status = call.get('status', 'pending').lower()
            call['status_color'] = {
                'pending': 'warning',
                'accepted': 'success',
                'rejected': 'danger',
                'completed': 'info'
            }.get(status, 'secondary')

        # Get recent appointments
        appointments = list(db.appointments.find().sort('date', -1).limit(10))
        
        # Enhance appointment data
        for appt in appointments:
            # Get patient details
            patient = db.users.find_one({'_id': appt.get('patient_id')})
            if patient:
                appt['patient_name'] = f"{patient.get('profile', {}).get('first_name', '')} {patient.get('profile', {}).get('last_name', '')}"
            else:
                appt['patient_name'] = 'Unknown'
            
            # Get doctor details
            doctor = db.users.find_one({'_id': appt.get('doctor_id')})
            if doctor:
                appt['doctor_name'] = f"Dr. {doctor.get('profile', {}).get('first_name', '')} {doctor.get('profile', {}).get('last_name', '')}"
            else:
                appt['doctor_name'] = 'Unknown'
            
            # Set status color
            status = appt.get('status', 'pending').lower()
            appt['status_color'] = {
                'pending': 'warning',
                'confirmed': 'success',
                'cancelled': 'danger',
                'completed': 'info'
            }.get(status, 'secondary')

        return render_template('admin_dashboard.html',
                             emergency_count=emergency_count,
                             appointment_count=appointment_count,
                             doctor_count=doctor_count,
                             patient_count=patient_count,
                             emergency_calls=emergency_calls,
                             appointments=appointments,
                             patients=patients)
                             
    except Exception as e:
        print(f"Error in admin dashboard: {str(e)}")
        flash('Error loading dashboard data', 'danger')
        return redirect(url_for('admin_login'))

@app.route('/admin/emergency/update', methods=['POST'])
@admin_required
def update_emergency_status():
    try:
        data = request.get_json()
        call_id = data.get('call_id')
        status = data.get('status')
        
        if not call_id or not status:
            return jsonify({'success': False, 'message': 'Missing required fields'})
            
        result = db.emergency_calls.update_one(
            {'_id': ObjectId(call_id)},
            {'$set': {
                'status': status,
                'updated_at': datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Emergency call not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/emergency/dispatch', methods=['POST'])
@admin_required
def dispatch_ambulance():
    try:
        data = request.get_json()
        call_id = data.get('call_id')
        
        if not call_id:
            return jsonify({'success': False, 'message': 'Missing call ID'})
            
        # Simulate ambulance assignment
        ambulance = {
            'unit_number': f"AMB-{random.randint(100,999)}",
            'driver_name': "John Doe",
            'contact': "+1234567890"
        }
        
        result = db.emergency_calls.update_one(
            {'_id': ObjectId(call_id)},
            {'$set': {
                'status': 'dispatched',
                'assigned_ambulance': ambulance,
                'eta': '15 minutes',
                'updated_at': datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': 'Emergency call not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/emergency-call', methods=['POST'])
@login_required
def emergency_call():
    try:
        data = request.get_json()
        print(f"Received emergency call data: {data}")  # Debug print

        # Create emergency call document
        emergency_data = {
            'user_id': str(current_user.id),
            'location': data.get('location', ''),
            'description': data.get('description', ''),
            'status': 'pending',
            'timestamp': datetime.now(),
            'patient_name': f"{current_user.username}"
        }
        
        print(f"Saving emergency call: {emergency_data}")  # Debug print
        result = db.emergency_calls.insert_one(emergency_data)
        print(f"Emergency call saved with ID: {result.inserted_id}")  # Debug print

        if result.inserted_id:
            # Log activity
            activity = {
                'type': 'emergency',
                'description': f'Emergency call created by {current_user.username}',
                'timestamp': datetime.now()
            }
            db.activities.insert_one(activity)
            print("Activity logged for emergency call")

            return jsonify({
                'success': True,
                'message': 'Emergency call sent successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create emergency call'
            }), 500

    except Exception as e:
        print(f"Emergency call error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your emergency call'
        }), 500

@app.route('/book-appointment')
@login_required
def book_appointment():
    return render_template('book_appointment.html')

@app.route('/submit-appointment', methods=['POST'])
@login_required
def submit_appointment():
    try:
        # Print form data for debugging
        print("Form data received:", request.form)
        
        # Get form data
        appointment_data = {
            'user_id': str(current_user.get_id()),
            'patient_name': request.form.get('patient_name'),
            'service_type': request.form.get('service_type'),
            'appointment_date': request.form.get('appointment_date'),
            'appointment_time': request.form.get('appointment_time'),
            'symptoms': request.form.get('symptoms', ''),
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        print("Appointment data:", appointment_data)  # Debug print
        
        # Validate required fields
        required_fields = ['patient_name', 'service_type', 'appointment_date', 'appointment_time']
        missing_fields = []
        for field in required_fields:
            if not appointment_data.get(field):
                missing_fields.append(field.replace('_', ' ').title())
        
        if missing_fields:
            flash(f'Please fill in the following required fields: {", ".join(missing_fields)}', 'danger')
            return redirect(url_for('book_appointment'))
        
        # Insert into database
        try:
            # Verify MongoDB connection
            client.admin.command('ping')
            print("MongoDB connection verified")  # Debug print
            
            result = db.appointments.insert_one(appointment_data)
            print("Insert result:", result.inserted_id)  # Debug print
            
            if result.inserted_id:
                flash('Appointment booked successfully!', 'success')
                return redirect(url_for('profile'))
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            flash('Error saving appointment. Please try again.', 'danger')
            return redirect(url_for('book_appointment'))
            
    except Exception as e:
        print(f"Booking error: {str(e)}")
        flash('An error occurred while booking. Please try again.', 'danger')
        return redirect(url_for('book_appointment'))

@app.route('/book-appointment', methods=['POST'])
@login_required
def book_appointment_post():
    data = request.json
    try:
        appointment = {
            'date': datetime.fromisoformat(data.get('date')),
            'doctor': data.get('doctor'),
            'user_id': ObjectId(current_user.get_id()),
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        db.appointments.insert_one(appointment)
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
        data = request.json
        user_message = data.get('message', '')
        language = data.get('language', 'english')
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-pro')
        
        # Create context and prompt
        context = """You are a knowledgeable and empathetic medical AI assistant. 
        Your role is to provide helpful health-related information and guidance, while being clear that you are not a replacement for professional medical advice. 
        Always encourage users to consult healthcare professionals for specific medical concerns."""
        
        if language == 'hinglish':
            context += "\nRespond in Hinglish (a mix of Hindi and English) to make the information more accessible."
        
        # Create the chat
        chat = model.start_chat(history=[])
        
        # Add system context
        chat.send_message(context)
        
        # Send user message and get response
        response = chat.send_message(user_message)
        
        # Extract and format the response
        ai_response = response.text
        
        # Log the chat interaction if user is authenticated
        if current_user.is_authenticated:
            db.chat_history.insert_one({
                'user_id': current_user.get_id(),
                'user_message': user_message,
                'ai_response': ai_response,
                'language': language,
                'timestamp': datetime.now()
            })
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        print(f"Error in chat: {str(e)}")
        return jsonify({
            'response': 'I apologize, but I encountered an error. Please try again or rephrase your question.'
        }), 500

@app.route('/profile')
@login_required
def profile():
    user_data = db.users.find_one({'_id': ObjectId(current_user.get_id())})
    # Get user's appointments
    appointments = list(db.appointments.find(
        {'user_id': str(current_user.get_id())},
        {'_id': 1, 'patient_name': 1, 'service_type': 1, 'appointment_date': 1, 'appointment_time': 1, 'status': 1}
    ).sort('appointment_date', -1))
    return render_template('profile.html', user=user_data, appointments=appointments)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        # Update user profile
        result = db.users.update_one(
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

@app.route('/insurance')
@login_required
def insurance():
    return render_template('insurance.html')

@app.route('/submit-insurance', methods=['POST'])
@login_required
def submit_insurance():
    try:
        # Print form data for debugging
        print("Insurance form data received:", request.form)
        
        insurance_data = {
            'user_id': str(current_user.get_id()),
            'full_name': request.form.get('full_name'),
            'insurance_type': request.form.get('insurance_type'),
            'policy_number': request.form.get('policy_number'),
            'claim_type': request.form.get('claim_type'),
            'claim_amount': request.form.get('claim_amount'),
            'description': request.form.get('description'),
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        print("Insurance data:", insurance_data)  # Debug print
        
        # Validate required fields
        required_fields = ['full_name', 'insurance_type', 'policy_number', 'claim_type']
        missing_fields = []
        for field in required_fields:
            if not insurance_data.get(field):
                missing_fields.append(field.replace('_', ' ').title())
        
        if missing_fields:
            flash(f'Please fill in the following required fields: {", ".join(missing_fields)}', 'danger')
            return redirect(url_for('insurance'))
        
        # Insert into database
        try:
            # Verify MongoDB connection
            client.admin.command('ping')
            print("MongoDB connection verified")  # Debug print
            
            result = db.insurance.insert_one(insurance_data)
            print("Insert result:", result.inserted_id)  # Debug print
            
            if result.inserted_id:
                flash('Insurance claim submitted successfully!', 'success')
                return redirect(url_for('profile'))
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            flash('Error saving claim. Please try again.', 'danger')
            return redirect(url_for('insurance'))
            
    except Exception as e:
        print(f"Insurance claim error: {str(e)}")
        flash('An error occurred while submitting claim. Please try again.', 'danger')
        return redirect(url_for('insurance'))

@app.route('/verify-prescription', methods=['POST'])
def verify_prescription():
    try:
        # Get form data
        medications = request.form.get('medications', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Handle image upload if present
        prescription_image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Save image temporarily
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                prescription_image = filepath

        # Split medications into list
        med_list = [med.strip() for med in medications.split('\n') if med.strip()]
        
        # Initialize response
        response = {
            'safe': True,
            'message': 'Your medications have been reviewed.',
            'recommendations': []
        }
        
        # Check for common drug interactions and dosage issues
        dangerous_combinations = {
            ('aspirin', 'warfarin'): 'Increased risk of bleeding',
            ('ibuprofen', 'aspirin'): 'Increased risk of gastrointestinal bleeding',
            ('cipro', 'calcium'): 'Reduced absorption of antibiotic'
        }
        
        # Convert medications to lowercase for comparison
        med_list_lower = [med.lower() for med in med_list]
        
        # Check for dangerous combinations
        for (drug1, drug2), risk in dangerous_combinations.items():
            if drug1 in ' '.join(med_list_lower) and drug2 in ' '.join(med_list_lower):
                response['safe'] = False
                response['recommendations'].append(f"Warning: {drug1.title()} and {drug2.title()} - {risk}")
        
        # Check dosage patterns
        for med in med_list:
            # Extract dosage if present
            dosage_match = re.search(r'(\d+)\s*(mg|g|ml)', med.lower())
            if dosage_match:
                dosage = int(dosage_match.group(1))
                unit = dosage_match.group(2)
                
                # Example dosage checks (add more based on your needs)
                if 'aspirin' in med.lower() and unit == 'mg' and dosage > 325:
                    response['safe'] = False
                    response['recommendations'].append(
                        f"High dosage detected for Aspirin ({dosage}mg). Standard dosage is 81-325mg."
                    )
                elif 'ibuprofen' in med.lower() and unit == 'mg' and dosage > 800:
                    response['safe'] = False
                    response['recommendations'].append(
                        f"High dosage detected for Ibuprofen ({dosage}mg). Maximum single dose is 800mg."
                    )
        
        # Add general recommendations if medications are safe
        if response['safe']:
            response['message'] = "Your medications appear to be safe to take as prescribed."
            response['recommendations'].extend([
                "Take medications with food unless otherwise directed",
                "Store in a cool, dry place",
                "Set reminders to take medications on time"
            ])
        else:
            response['message'] = "Some potential issues were detected with your medications."
            response['recommendations'].append(
                "Please consult with your healthcare provider about these concerns."
            )
        
        # Clean up uploaded file if it exists
        if prescription_image and os.path.exists(prescription_image):
            os.remove(prescription_image)
        
        # Log the verification
        if current_user.is_authenticated:
            db.prescription_verifications.insert_one({
                'user_id': current_user.get_id(),
                'medications': med_list,
                'notes': notes,
                'result': response,
                'timestamp': datetime.now()
            })
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in prescription verification: {str(e)}")
        return jsonify({
            'safe': False,
            'message': 'An error occurred while analyzing your prescription.',
            'recommendations': ['Please try again or consult with your healthcare provider.']
        }), 500

@app.context_processor
def utility_processor():
    def get_user_profile():
        if current_user.is_authenticated:
            return current_user.user_data.get('profile', {})
        return {}
    return dict(get_user_profile=get_user_profile)

def format_time_ago(timestamp):
    """Format a timestamp into a human-readable 'time ago' string."""
    now = datetime.now()
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return 'just now'
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif diff < timedelta(days=30):
        days = diff.days
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif diff < timedelta(days=365):
        months = int(diff.days / 30)
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = int(diff.days / 365)
        return f'{years} year{"s" if years != 1 else ""} ago'

# Routes
@app.route('/')
def index():
    return render_template('index.html', current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            data = request.get_json()
            print(f"Login attempt for: {data.get('username')}")  # Debug print
            
            identifier = data.get('username')  # This can be email or username
            password = data.get('password')
            
            if not identifier or not password:
                print("Missing login credentials")
                return jsonify({
                    'success': False,
                    'message': 'Email/Username and password are required'
                }), 400
            
            # Find user by email or username
            user_data = db.users.find_one({
                '$or': [
                    {'email': identifier.lower()},  # Case-insensitive email
                    {'username': identifier}  # Case-sensitive username
                ]
            })
            print(f"Found user: {user_data is not None}")  # Debug print
            
            if user_data and check_password_hash(user_data['password'], password):  # Changed from password_hash
                print("Password verified successfully")
                user = User(user_data)
                login_user(user, remember=True)
                session.permanent = True
                
                # Log activity
                activity = {
                    'type': 'user',
                    'description': f'User login: {user.username}',
                    'timestamp': datetime.now()
                }
                db.activities.insert_one(activity)
                print("Login activity logged")
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful!',
                    'redirect': url_for('index')
                })
            else:
                print("Invalid credentials")
                return jsonify({
                    'success': False,
                    'message': 'Invalid email/username or password'
                }), 401
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred during login'
            }), 500
    
    # For GET requests, redirect to home page with login modal
    return redirect(url_for('index'))

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Check if the request is JSON or form data
            if request.is_json:
                data = request.get_json()
                username = data.get('username')
                email = data.get('email')
                password = data.get('password')
                confirm_password = data.get('confirm_password')
                role = data.get('role', 'patient')
            else:
                # Handle form data
                username = request.form.get('username')
                email = request.form.get('email')
                password = request.form.get('password')
                confirm_password = request.form.get('confirm_password')
                role = request.form.get('role', 'patient')
            
            print(f"Received signup request for username: {username}, email: {email}, role: {role}")
            
            # Validate required fields
            if not all([username, email, password, confirm_password]):
                missing_fields = []
                if not username: missing_fields.append('username')
                if not email: missing_fields.append('email')
                if not password: missing_fields.append('password')
                if not confirm_password: missing_fields.append('confirm password')
                print(f"Missing required fields: {', '.join(missing_fields)}")
                
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': f"Required fields missing: {', '.join(missing_fields)}"
                    }), 400
                else:
                    flash(f"Required fields missing: {', '.join(missing_fields)}", 'danger')
                    return render_template('signup.html')
            
            # Validate password match
            if password != confirm_password:
                print("Password mismatch")
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': 'Passwords do not match!'
                    }), 400
                else:
                    flash('Passwords do not match!', 'danger')
                    return render_template('signup.html')
            
            # Create user document
            user_data = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                'role': role,
                'created_at': datetime.now(),
                'profile': {
                    'first_name': '',
                    'last_name': '',
                    'phone': '',
                    'address': '',
                    'medical_history': []
                }
            }
            
            print(f"Attempting to create user: {username}")
            result = db.users.insert_one(user_data)
            print(f"User created with ID: {result.inserted_id}")
            
            if result.inserted_id:
                # Log activity
                activity = {
                    'type': 'user',
                    'description': f'New user signup: {username}',
                    'timestamp': datetime.now()
                }
                db.activities.insert_one(activity)
                print(f"Activity logged for new user: {username}")
                
                # Create user object and log them in
                user = User(user_data)
                login_user(user)
                
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': 'Account created successfully!'
                    })
                else:
                    flash('Account created successfully! Please complete your profile.', 'success')
                    return redirect(url_for('profile'))
            
        except DuplicateKeyError as e:
            error_msg = str(e)
            print(f"Duplicate key error: {error_msg}")
            message = 'An account with these details already exists.'
            if 'username_1' in error_msg:
                message = 'This username is already taken. Please choose another.'
            elif 'email_1' in error_msg:
                message = 'This email is already registered. Please use another email or try logging in.'
            
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': message
                }), 400
            else:
                flash(message, 'danger')
                return render_template('signup.html')
            
        except Exception as e:
            print(f"Signup error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'An error occurred during signup. Please try again.'
                }), 500
            else:
                flash('An error occurred during signup. Please try again.', 'danger')
                return render_template('signup.html')
    
    # GET request - show signup form
    return render_template('signup.html')

if __name__ == '__main__':
    # Verify MongoDB connection
    try:
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
    except Exception as e:
        print("❌ Failed to connect to MongoDB:", e)
        
    # Run the Flask app
    app.run(host='0.0.0.0', port=8000, debug=True)