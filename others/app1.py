from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
from reco import get_recommendations

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle the main page requests and image uploading."""
    if request.method == 'POST':
        occasion = request.form.get('occasion')  # Get the occasion from form data
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(img_path)

            try:
                recommended_image_paths, recommended_item_ids = get_recommendations(img_path, occasion)
                recommendations = list(zip(recommended_image_paths, recommended_item_ids))
                return render_template('results.html', recommendations=recommendations)
            except Exception as e:
                print(e)  # Log the error for debugging
                # Handle the error in a user-friendly way
                return render_template('error.html', message="Error in processing the image.")
                
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Placeholder for actual login logic
    if request.method == 'POST':
        # Process login here
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Placeholder for actual registration logic
    if request.method == 'POST':
        # Process registration here
        return redirect(url_for('index'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
