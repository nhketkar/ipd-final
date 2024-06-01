import os
import numpy as np
import sqlite3
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.layers import GlobalMaxPooling2D
from tensorflow.keras.models import Sequential
from numpy.linalg import norm
from tqdm import tqdm

# Create or connect to the SQLite database
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# Create a table for embeddings without the foreign key constraint
cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY,
        occasion TEXT,
        item_id INTEGER,
        file_path TEXT,
        image_path TEXT,
        gender TEXT,
        bodytype TEXT
    )
''')
conn.commit()

# Initialize the ResNet50 model
model = Sequential([
    ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3)),
    GlobalMaxPooling2D()
])
model.trainable = False

# Function to extract features from an image
def extract_features(img_path, model):
    try:
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        expanded_img_array = np.expand_dims(img_array, axis=0)
        preprocessed_img = preprocess_input(expanded_img_array)
        result = model.predict(preprocessed_img).flatten()
        normalized_result = result / norm(result) if norm(result) > 0 else result
        return normalized_result
    except Exception as e:
        print(f"Error processing image {img_path}: {e}")
        return None

# Ensure the embeddings directory exists
os.makedirs('embeddings', exist_ok=True)

# Initialize a global counter for item_id
cursor.execute('SELECT MAX(item_id) FROM embeddings')
result = cursor.fetchone()
global_item_id = (result[0] + 1) if result[0] is not None else 0

# Process images from each gender and occasion subfolder
genders = ['female']
bodytypes = ['Hourglass']
occasions = ['Beachwear','Casual','Formal','Party','Semi-Formal','Wedding']
for gender in genders:
  for bodytype in bodytypes:
    for occasion in occasions:
        folder_path = os.path.join('app1','static', 'downloaded_images1', gender,bodytype,occasion)
        print(f"Checking folder: {folder_path}")  # Debug print
        if os.path.isdir(folder_path):
            print(f"Found folder: {folder_path}")  # Debug print
            for filename in tqdm(os.listdir(folder_path), desc=f"Processing {gender}/{occasion} images"):
                file_path = os.path.join(folder_path, filename)
                print(f"Processing file: {file_path}")  # Debug print
                features = extract_features(file_path, model)
                if features is not None:
                    embedding_file_path = f'embeddings/{gender}_{occasion}_{bodytype}_{global_item_id}.npy'
                    np.save(embedding_file_path, features)
                    cursor.execute('INSERT INTO embeddings (occasion, item_id, file_path, image_path, gender,bodytype) VALUES (?, ?, ?, ?, ?, ?)', 
                                   (occasion, global_item_id, embedding_file_path, file_path, gender,bodytype))
                    global_item_id += 1  # Increment the global item_id
                else:
                    print(f"Failed to process file: {file_path}")  # Debug print

conn.commit()
conn.close()
