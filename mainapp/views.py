from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connections
from . import globals
import os
from django.conf import settings
from django.core.files.storage import default_storage
from datetime import date
import hashlib
from .models import PatientVisit  # Assuming this is your model
import cv2
import numpy as np
import tensorflow as tf
from .models import Patient
from tensorflow.keras.models import load_model
from django.core.files.storage import FileSystemStorage
from .models import ModelUpload  # Assuming you have a ModelUpload table
from django.utils.timezone import now



def index(request):
    return render(request, 'index.html')

def model_history(request):
        # Fetch all models for the history table
    models = []
    try:
        with connections['default'].cursor() as cursor:
            select_query = """
                SELECT model_name, model_version, updated_date, admin_name, model_path 
                FROM model
            """
            cursor.execute(select_query)
            models = cursor.fetchall()  # Fetch all rows from the `model` table
    except Exception as e:
        messages.error(request, f"Error fetching model history: {e}")

    # Pass data to the template
    return render(request, 'model_history.html', {
        'models': [
            {
                'model_name': row[0],
                'model_version': row[1],
                'updated_date': row[2],
                'admin_name': row[3],
                'model_path': row[4],
            }
            for row in models
        ],
        'admin_name': globals.admin_name,
    })


def upload_model(request):

        if request.method == 'POST' and request.FILES.get('modelFile'):
            # Retrieve form data
            model_file = request.FILES['modelFile']
            model_name = request.POST.get('modelName')  # Detection or Grading
            version = request.POST.get('version')  # Version number

            try:
                # Save the uploaded file
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'models')
                os.makedirs(upload_dir, exist_ok=True)  # Ensure the directory exists
                upload_path = os.path.join(upload_dir, model_file.name)
                file_url = f"{settings.MEDIA_URL}models/{model_file.name}"

                with open(upload_path, 'wb') as f:
                    for chunk in model_file.chunks():
                        f.write(chunk)

                # Update the model table with new data
                with connections['default'].cursor() as cursor:
                    update_query = """
                        INSERT INTO model (admin_id, model_name, model_version, updated_date, admin_name, model_path)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(update_query, [globals.admin_id, model_name, version, now(), globals.admin_name, file_url])
                
                # Feedback to the user
            except Exception as e:
                messages.error(request, f"Error updating model table: {e}")
        # Pass doctor_name to the template
        return render(request, 'upload_model.html', {
            'admin_name': globals.admin_name,
        })



def login_view(request):
    if request.method == 'POST':
        users_Id = request.POST.get('usersId')
        password = request.POST.get('password')
        
        print(users_Id)
        print(password)

        # Extract the first 3 digits of users_Id
        first_digit = users_Id[:1]


        with connections['default'].cursor() as cursor:
            if first_digit == '2':
                # Query 1: For admin users
                query = "SELECT * FROM nurse WHERE nurse_id = %s AND password = %s"
                cursor.execute(query, [users_Id, password])
                result = cursor.fetchone()
                if result:
                    globals.nurse_id = users_Id
                    return redirect('nurse_dashboard')
            elif first_digit == '1':
                # Query 2: For doctor users
                query = "SELECT * FROM doctor WHERE doctor_id = %s AND password = %s"
                cursor.execute(query, [users_Id, password])
                result = cursor.fetchone()
                if result:
                    globals.user_id = users_Id
                    return redirect('doctor_dashboard')
            elif first_digit == '3':
                # Query 3: For doctor users
                query = "SELECT * FROM admin WHERE admin_id = %s AND password = %s"
                cursor.execute(query, [users_Id, password])
                result = cursor.fetchone()
                if result:
                    globals.admin_id = users_Id
                    return redirect('admin_dashbord')
                
            else:
                # If the prefix doesn't match any known role
                messages.error(request, 'Invalid role or credentials.')

        # If no result was found in any query
                
    return render(request, 'doctor_login.html')  # Render the login page if no POST request



def admin_dashboard(request):
    admin_name=None

    # Fetch the admin's name based on the `admin_id`
    try:
        with connections['default'].cursor() as cursor:
            admin_query = "SELECT name FROM admin WHERE admin_id = %s"
            cursor.execute(admin_query, [globals.admin_id])
            admin_result = cursor.fetchone()
            if admin_result:
                admin_name = admin_result[0]
                globals.admin_name=admin_name

    except Exception as e:
        messages.error(request, f"Error fetching admin name: {e}")
        admin_name = "Unknown Admin"

    # Pass data to the template
    return render(request, 'admin_dashboard.html' ,{
        'admin_name': globals.admin_name,
    })
    


def doctor_dashboard(request):
    fileNumber = None
    doctor_name = None  # Default value for doctor name

    # Fetch the doctor's name based on the user_ID
    with connections['default'].cursor() as cursor:
        doctor_query = "SELECT name FROM doctor WHERE doctor_id = %s"
        cursor.execute(doctor_query, [globals.user_id])
        doctor_result = cursor.fetchone()
        if doctor_result:
            doctor_name = doctor_result[0]  # Fetch the name from the query result

    if request.method == 'POST':
        fileNumber = request.POST.get('fileNumber')
        print(fileNumber)
        globals.fileNumber = fileNumber

        with connections['default'].cursor() as cursor:
            query = "SELECT * FROM patient_visits WHERE patient_ID = %s AND doctor_id = %s"
            cursor.execute(query, [fileNumber, globals.user_id])
            result = cursor.fetchone()

            if result:
                return redirect('upload_results')
            else:
                messages.error(request, 'Invalid patient.')

    # Pass doctor_name to the template
    return render(request, 'doctor_dashboard.html', {
        'doctor_name': doctor_name,
    })



def doctor_and_nurse_info(request):
    doctors = []
    nurses = []

    # Fetch doctor information
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT name, doctor_id, phone_number, email FROM doctor")
        doctors = [
            {
                'name': row[0],
                'doctor_id': row[1],
                'phone_number': row[2],
                'email': row[3],
            }
            for row in cursor.fetchall()
        ]

    # Fetch nurse information
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT name, nurse_id, phone_number, email FROM nurse")
        nurses = [
            {
                'name': row[0],
                'nurse_id': row[1],
                'phone_number': row[2],
                'email': row[3],
            }
            for row in cursor.fetchall()
        ]

    return render(request, 'doctor_and_nurse_info.html', {
        'doctors': doctors,
        'nurses': nurses,'admin_name': globals.admin_name,
    })


def nurse_info(request):
    nurses = []  # Use 'doctors' to store multiple records
    with connections['default'].cursor() as cursor:
        # Fetch all doctors from the table
        query = "SELECT name, doctor_id, phone, email FROM nurse"
        cursor.execute(query)
        results = cursor.fetchall()  # Fetch all rows
        
        for row in results:
            nurses.append({
                'name': row[0],    
                'ID': row[1],      
                'phone': row[2],   
                'email': row[3],   
            })

    return render(request, 'nurse_info.html', {'nurses': nurses})

#----------------------------------------------------------

# Segmentation function 
def segment_eye(img):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred_img = cv2.GaussianBlur(gray_img, (5, 5), 0)
    threshold_img = cv2.adaptiveThreshold(
        blurred_img, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        11, 2
    )
    kernel = np.ones((3, 3), np.uint8)
    segmented_img = cv2.dilate(threshold_img, kernel, iterations=2)
    return segmented_img

# Blur the background 
def blur_background(img, segmented_img):
    blurred_background = cv2.GaussianBlur(img, (21, 21), 0)
    result = np.where(segmented_img[..., None] == 255, img, blurred_background)
    return result

# Highlight cloudiness
def highlight_cloudiness(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, white_areas = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    highlighted = cv2.addWeighted(img, 1, cv2.cvtColor(white_areas, cv2.COLOR_GRAY2BGR), 0.5, 0)
    return highlighted

# Remove reflections 
def remove_reflections(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, reflections = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    reflection_removed = cv2.inpaint(img, reflections, 3, cv2.INPAINT_TELEA)
    return reflection_removed

# Preprocessing function for the single image
def preprocess_image(img_path, target_size=(128, 128)):
    img = cv2.imread(img_path)
    
    if img is not None:
        # Apply all the preprocessing steps
        segmented_img = segment_eye(img)
        img = blur_background(img, segmented_img)
        img = highlight_cloudiness(img)
        img = remove_reflections(img)
        
        # Resize the image to the target size
        img_resized = cv2.resize(img, target_size)
        img_resized = np.expand_dims(img_resized, axis=0)  # Add batch dimension (1, height, width, channels)
        return img_resized
    else:
        print(f"Error: Image {img_path} could not be loaded.")
        return None

def upload_results(request):
    doctor_name = None
    patient_name = None
    user_id = globals.user_id
    patient_id = globals.fileNumber
    
        # Fetch doctor name using user_id
    with connections['default'].cursor() as cursor:
            cursor.execute("SELECT name FROM doctor WHERE doctor_id = %s", [user_id])
            result = cursor.fetchone()
            if result:
                doctor_name = result[0]

        # Fetch patient name using patient_id
    with connections['default'].cursor() as cursor:
            cursor.execute("SELECT name FROM patient WHERE patient_id = %s", [patient_id])
            result = cursor.fetchone()
            if result:
                patient_name = result[0]

    uploaded_image = None
    diagnosis = None
    doctor_notes = None  # Initialize the variable for doctor's notes

    if request.method == 'POST':
        if 'imageUpload' in request.FILES:
            # Handling the uploaded image
            uploaded_file = request.FILES['imageUpload']
            
            # Saving the uploaded image to the media directory
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)  # Save the file in the 'media' directory
            file_path = fs.save(uploaded_file.name, uploaded_file)  # Save the file and get its path
            uploaded_image = fs.url(file_path)  # Get the URL for accessing the uploaded image

            # Preprocess the uploaded image
            img_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            img_preprocessed = preprocess_image(img_path, target_size=(128, 128))

            # Define BASE_DIR (your Django project root)
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Construct the model's path
            MODEL_PATH = os.path.join(BASE_DIR, 'model', 'my_trained_cnn_model.keras')
            
            # Load the model
            model = load_model(MODEL_PATH)


            # Predict the severity of the disease
            if img_preprocessed is not None:
                prediction = model.predict(img_preprocessed)
                diagnosis = 'Cataract' if prediction >= 0.5 else 'Normal'
                print(diagnosis)

                # Update the database with the diagnosis and the image path
                with connections['default'].cursor() as cursor:
                    query = """
                        UPDATE patient_visits 
                        SET result = %s, image = %s 
                        WHERE patient_ID = %s
                    """
                    cursor.execute(query, [diagnosis, uploaded_image, patient_id])

        # Handle saving doctor's notes if provided
        if 'doctor_notes' in request.POST:
            doctor_notes = request.POST['doctor_notes']

            # Update the database with the doctor's notes
            with connections['default'].cursor() as cursor:
                query = """
                    UPDATE patient_visits
                    SET dr_notes = %s
                    WHERE patient_ID = %s
                """
                cursor.execute(query, [doctor_notes, patient_id])

    return render(request, 'upload_results.html', {
        'doctor_name': doctor_name,
        'patient_name': patient_name,
        'uploaded_image': uploaded_image,
        'diagnosis': diagnosis,
        'severity': diagnosis,  # You can modify this as needed
    })



#----------------------------------------------------------

def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def medical_record(request):
    # Define an empty list to hold patient data
    patients = []

    # Retrieve data from the database
    with connections['default'].cursor() as cursor:
        # Query patient visits and related data
        query = """
        SELECT 
            p.name AS patient_name,
            pv.patient_ID AS file_number,
            pv.VA_od AS visual_acuity_od,
            pv.VA_os AS visual_acuity_os,
            pv.lop_od AS iop_od,
            pv.lop_os AS iop_os,
            pv.result AS ai_diagnosis,
            pv.image AS result_image,
            pv.dr_notes AS doctor_notes,
            p.DOB AS birth_date,
            GROUP_CONCAT(DISTINCT hod.diseases SEPARATOR ', ') AS chronic_diseases,
            GROUP_CONCAT(DISTINCT med.medications SEPARATOR ', ') AS medications
        FROM patient_visits pv
        LEFT JOIN patient p ON pv.patient_ID = p.patient_ID
        LEFT JOIN history_of_diseases hod ON hod.patient_ID = p.patient_ID
        LEFT JOIN medications med ON med.patient_ID = p.patient_ID
        WHERE pv.doctor_id = %s
        GROUP BY pv.patient_ID
        """
        
        # Replace `user_id` with the currently logged-in user's ID
        user_id = globals.user_id  # Or use `request.user.id` if using Django's auth system
        
        cursor.execute(query, [user_id])
        result = cursor.fetchall()
        
        # Iterate through the results and append them to the patients list
        for row in result:
            birth_date = row[9]  # Assuming the 10th column is birth_date
            age = calculate_age(birth_date) if birth_date else "N/A"

            patients.append({
                'name': row[0],
                'file_number': row[1],
                'visual_acuity': f"{row[2]}/{row[3]}",
                'iop': f"{row[4]} mmHg / {row[5]} mmHg",
                'ai_diagnosis': row[6],
                'result_image': row[7],
                'doctor_notes': row[8],
                'age': age,
                'chronic_diseases': row[10],
                'medications': row[11],
            })

    # Render the template with the patients data
    return render(request, 'medical_record.html', {'patients': patients})



def nurse_dashboard(request):
    nurse_name = None

    try:
        # Fetch the nurse's name using `nurse_id`
        with connections['default'].cursor() as cursor:
            nurse_query = "SELECT name FROM nurse WHERE nurse_id = %s"
            cursor.execute(nurse_query, [globals.nurse_id])
            nurse_result = cursor.fetchone()
            if nurse_result:
                nurse_name = nurse_result[0]
    except Exception as e:
        messages.error(request, f"Error fetching nurse name: {e}")
        nurse_name = "Unknown Nurse"

    if request.method == 'POST':
        # Fetch data from the form
        globals.fileNumber = file_number = request.POST.get('fileNumber')
        Doctor_id= request.POST.get('doctorid')
        VA_od = request.POST.get('VA_od')
        VA_os = request.POST.get('VA_os')
        lop_od = request.POST.get('lop_od')
        lop_os = request.POST.get('lop_os')
        medications = request.POST.get('medications')
        diseases = request.POST.get('diseases')

        # Ensure that all values are entered
        if not file_number:
            messages.error(request, "Patient File Number is required.")
            return render(request, 'nurse_dashboard.html', {'nurse_name': nurse_name})

        try:
            # Check if the patient exists in the patient table
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM patient WHERE patient_ID = %s", [file_number])
                patient_exists = cursor.fetchone()[0]

                if patient_exists:
                    # Insert into patient_visits if the patient exists
                    insert_1_query = """
                        INSERT INTO patient_visits (patient_ID, nurse_id, visit_date ,doctor_id)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
                        ON DUPLICATE KEY UPDATE visit_date = CURRENT_TIMESTAMP
                    """
                    cursor.execute(insert_1_query, [file_number, globals.nurse_id,Doctor_id ])

                    insert_2_query = """
                        INSERT INTO medications (patient_ID, medications)
                        VALUES (%s, %s)
                    """
                    cursor.execute(insert_2_query, [file_number, medications ])

                    insert_3_query = """
                        INSERT INTO history_of_diseases (patient_ID, diseases)
                        VALUES (%s, %s)
                    """
                    cursor.execute(insert_3_query, [file_number, diseases ])

                    # Update the patient's details in the database
                    update_query = """
                        UPDATE patient_visits
                        SET VA_od = %s, VA_os = %s, lop_od = %s, lop_os = %s
                        WHERE patient_ID = %s AND nurse_id = %s AND doctor_id =%s
                    """
                    cursor.execute(update_query, [VA_od, VA_os, lop_od, lop_os, file_number, globals.nurse_id , Doctor_id])
                    # Patient does not exist
        except Exception as e:
            messages.error(request, f"Error updating patient details: {e}")

    # Render the nurse dashboard template with the nurse name
    return render(request, 'nurse_dashboard.html', {
        'nurse_name': nurse_name,
    })


def add_user(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')  # Doctor or Nurse
        name = request.POST.get('name')
        user_id = request.POST.get('user_id')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # Insert into the respective table
            with connections['default'].cursor() as cursor:
                if user_type == 'doctor':
                    query = """
                        INSERT INTO doctor (name, doctor_id, phone_number, email, password)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                elif user_type == 'nurse':
                    query = """
                        INSERT INTO nurse (name, nurse_id, phone_number, email, password)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                else:
                    raise ValueError("Invalid user type")

                cursor.execute(query, [name, user_id, phone_number, email, password])

            messages.success(request, f"{user_type.capitalize()} '{name}' added successfully!")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Error adding user: {e}")

    return render(request, 'add_user.html',{
        'admin_name': globals.admin_name,
    })



def contact_us(request):
    return render(request, 'contact_us.html')

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.http import HttpResponse

def contact_us_submit(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Email content
        subject = f"New Contact Us Message from {name}"
        html_message = f"""
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Message:</strong></p>
        <p>{message}</p>
        """

        # SMTP Configuration
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_user = 'neuroeye3@gmail.com'
        smtp_password = 'qacp zdkt kgvi pkmq'  # Use App Password

        try:
            # Create the email
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = 'neuroeye3@gmail.com'
            msg['Subject'] = subject
            msg.attach(MIMEText(html_message, 'html'))

            # Connect to Gmail SMTP server
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            return HttpResponse(f"Thank you, {name}! Your message has been sent.")
        except Exception as e:
            return HttpResponse(f"Failed to send email. Error: {e}", status=500)
    else:
        return HttpResponse("Invalid Request", status=400)
