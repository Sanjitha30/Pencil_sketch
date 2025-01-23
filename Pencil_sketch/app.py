from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import cv2
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['PROCESSED_FOLDER']):
    os.makedirs(app.config['PROCESSED_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return "Invalid file type", 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        # Process the image
        image = cv2.imread(file_path)
        if image is None:
            return "Invalid image file", 400
        pencil_sketch = create_pencil_sketch(image)
        
        sketch_filename = f"{uuid.uuid4().hex}_pencil_sketch.jpg"
        processed_path = os.path.join(app.config['PROCESSED_FOLDER'], sketch_filename)
        cv2.imwrite(processed_path, pencil_sketch)
        
        return redirect(url_for('show_images', uploaded_file=filename, sketch_file=sketch_filename))
    except Exception as e:
        return str(e), 500

@app.route('/show_images')
def show_images():
    uploaded_file = request.args.get('uploaded_file')
    sketch_file = request.args.get('sketch_file')
    return render_template('index.html', uploaded_file=uploaded_file, sketch_file=sketch_file)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], secure_filename(filename))

@app.route('/processed/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], secure_filename(filename))

def create_pencil_sketch(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    inverted_gray_image = cv2.bitwise_not(gray_image)
    blurred_image = cv2.medianBlur(inverted_gray_image, 21)
    inverted_blurred_image = cv2.bitwise_not(blurred_image)
    pencil_sketch = cv2.divide(gray_image, inverted_blurred_image, scale=256.0)
    return pencil_sketch

if __name__ == '__main__':
    app.run(debug=True)
