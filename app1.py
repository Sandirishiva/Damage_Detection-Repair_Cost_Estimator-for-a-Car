from flask import Flask, render_template, request, redirect, url_for, session, flash
import config
import mysql.connector as connector
from werkzeug.utils import secure_filename
import os
from ultralytics import YOLO
from collections import Counter
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def connect_to_db():
    try:
        connection = connector.connect(**config.mysql_credentials)
        return connection
    except connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None
        
@app.route('/')
def home():
   return render_template('dashboard.html',brands=get_brands(),models=get_models(),original_image='uploaded_image.jpg', detected_image='detected_image.jpg', part_prices={},car_model='',car_brand='')


# Load YOLO model
model_path = r"C:\Users\akash\OneDrive\Desktop\New folder\accident-damage-detection\models\model weights\best.pt"
model = YOLO(model_path)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        file = request.files.get('image')
        car_brand = request.form.get('carBrand')
        car_model = request.form.get('carModel')
        if not file:
            flash('Please upload an image.', 'error')
            return render_template('dashboard.html',brands=get_brands(),models=get_models(),original_image='uploaded_image.jpg', detected_image='detected_image.jpg', part_prices={},car_model='',car_brand='')

        filename = secure_filename(file.filename)
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            flash('Invalid file type. Please upload an image.', 'error')
            return render_template('dashboard.html',brands=get_brands(),models=get_models(),original_image='uploaded_image.jpg', detected_image='detected_image.jpg', part_prices={},car_model='',car_brand='')
        
        # Save the uploaded image
        image_path = os.path.join(r'C:\Users\akash\OneDrive\Desktop\New folder\accident-damage-detection\static', 'uploaded_image.jpg')
        print("File uploaded successfully")
        
        file.save(image_path)
        # print(f"Upload image path : {image_path}")
        # Make predictions using YOLO
        result = model(image_path)
        detected_objects = result[0].boxes
        class_ids = [box.cls.item() for box in detected_objects]
        class_counts = Counter(class_ids)
        # print(f"Class counts : {class_counts}")

        # Check if any damage is detected
        if not class_counts:
            flash('No damage detected in the uploaded image.', 'error')
            return render_template('estimate.html', original_image='uploaded_image.jpg', detected_image='uploaded_image.jpg', part_prices={}, car_model=car_model, car_brand=car_brand, brands=get_brands(), models=get_models(), damage_detected=False)

        # Save the image with detections
        detected_image_path = os.path.join(r'C:\Users\akash\OneDrive\Desktop\New folder\accident-damage-detection\static', 'detected_image.jpg')
        detected_image_path = result[0].save(detected_image_path)
        print(f"Detected image path : {detected_image_path}")
        # Fetch part prices from the database
        part_prices = get_part_prices(class_counts,car_brand,car_model)
        # print(f"Part prices : {part_prices}")
        return render_template('estimate.html', original_image='uploaded_image.jpg', detected_image='detected_image.jpg', part_prices=part_prices,car_model=car_model,car_brand=car_brand,brands=get_brands(),models=get_models(), damage_detected=True)

    return render_template('dashboard.html', brands=get_brands(), models=get_models(), original_image='uploaded_image.jpg', detected_image='detected_image.jpg', part_prices={}, car_model='', car_brand='')

def get_brands():
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT distinct brand FROM car_models")
                brands = cursor.fetchall()
                brands_list=[]
                for brand in brands:
                    brands_list.append(brand['brand'])
                return brands_list
        except connector.Error as e:
            print(f"Error executing query: {e}")
            return {}
    print("Connection failed")
    return {}


def get_models():
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT distinct model FROM car_models")
                models = cursor.fetchall()
                models_list=[]
                for model in models:
                    models_list.append(model['model'])
                return models_list
        except connector.Error as e:
            print(f"Error executing query: {e}")
            return {}
    print("Connection failed")
    return {}

def get_part_prices(class_counts, car_brand, car_model):
    connection = connect_to_db()
    if connection:
        try:
            with connection.cursor(dictionary=True) as cursor:
                # Fetch part prices
                prices = {}
                for class_id, count in class_counts.items():
                    part_name = get_part_name_from_id(class_id)
                    # print(f"Parts name: {part_name}")
                    if part_name:
                        cursor.execute(
                            "SELECT price FROM car_models WHERE brand = %s AND model = %s AND part = %s",
                            (car_brand, car_model, part_name)
                        )
                        price_data = cursor.fetchone()
                        # Ensure the cursor is cleared before the next query
                        cursor.fetchall()  # Fetch any remaining results to clear the cursor
                        if price_data:
                            price_per_part = price_data['price']
                            total_price = price_per_part * count
                            prices[part_name] = {'count': count, 'price': price_per_part, 'total': total_price}
                # print(f"Prices : {prices}")
                return prices
        except connector.Error as e:
            print(f"Error executing query: {e}")
            return {}
    print("Connection failed")
    return {}


def get_part_name_from_id(class_id):
    class_names = ['Bonnet', 'Bumper', 'Dickey', 'Door', 'Fender', 'Light', 'Windshield', 'Window', 'Wheel', 'Grille', 'Mirror', 'Roof', 'Skirt', 'Spoiler', 'Tailgate', 'Trunk', 'Wheel', 'Wing', 'Hood', 'Headlight', 'Taillight', 'Foglight', 'Indicator', 'Brake light', 'Reverse light', 'Number plate', 'Exhaust', 'Muffler', 'Bumper', 'Fender', 'Grille', 'Hood', 'Door', 'Window', 'Windshield']
    if 0 <= class_id < len(class_names):
        return class_names[int(class_id)]
    return None


if __name__ == '__main__':
    app.run(debug=True)
