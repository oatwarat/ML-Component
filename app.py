from flask import Flask, render_template, request, redirect, url_for, flash
import os
import requests
from werkzeug.utils import secure_filename
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"
headers = {"Authorization": f"Bearer {Config.HF_API_TOKEN}"}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_image_caption(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        response = requests.post(API_URL, headers=headers, data=data)
        result = response.json()
        
        # Print response for debugging
        print("API Response:", result)
        
        # Check if response is a list
        if isinstance(result, list) and len(result) > 0:
            return result[0]['generated_text']
        # Check if response is a dictionary
        elif isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text']
        else:
            return "Unable to generate caption"
    except Exception as e:
        print(f"Error generating caption: {str(e)}")
        return "Error generating caption"

@app.route('/')
def gallery():
    images = []
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                caption = get_image_caption(image_path)
                images.append({
                    'filename': filename,
                    'path': url_for('static', filename=f'uploads/{filename}'),
                    'caption': caption
                })
    except Exception as e:
        print(f"Error in gallery route: {str(e)}")
        flash('Error loading images')
    
    return render_template('gallery.html', images=images)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        files = request.files.getlist('file')

        for file in files:
            if file.filename == '':
                flash('No selected file')
                continue

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        return redirect(url_for('gallery'))

    return render_template('upload.html')


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)