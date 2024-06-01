import os
import numpy as np
import sqlite3
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.layers import GlobalMaxPooling2D
from sklearn.neighbors import NearestNeighbors
from numpy.linalg import norm
import datetime

# Initialize the model
model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
model.trainable = False
model = tf.keras.Sequential([model, GlobalMaxPooling2D()])

def feature_extraction(img_path):
    """Extract features from an image."""
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    expanded_img_array = np.expand_dims(img_array, axis=0)
    preprocessed_img = preprocess_input(expanded_img_array)
    result = model.predict(preprocessed_img).flatten()
    normalized_result = result / norm(result) if norm(result) > 0 else result
    return normalized_result

def get_embedding_and_image_paths(occasion, gender, bodytype=None):
    try:
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()
        
        # Base query without bodytype condition
        query = '''
        SELECT file_path, image_path, item_id
        FROM embeddings
        WHERE occasion = ? AND Gender = ?
        '''
        params = [occasion, gender]  # Base parameters for the query
        
        # If bodytype is provided, add it to the query and parameters
        if bodytype:
            query += ' AND bodytype = ?'
            params.append(bodytype)
        
        cursor.execute(query, params)
        paths = cursor.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        paths = []
    finally:
        conn.close()
    
    return [(row[0], row[1], row[2]) for row in paths]

def load_occasion_data(occasion, gender, bodytype=None):
    # Conditionally set paths depending on gender
    if gender == 'male':
        # For male, assume bodytype might not be needed or a different logic is applied
        paths = get_embedding_and_image_paths(occasion, gender, None)  # Pass None or adjust as needed
    else:
        # For female, use the bodytype as before
        paths = get_embedding_and_image_paths(occasion, gender, bodytype)

    feature_list = []
    for embedding_path, _, _ in paths:
        if os.path.exists(embedding_path):  # Check if the file exists
            feature_list.append(np.load(embedding_path))
        else:
            print(f"File not found: {embedding_path}")  # Debugging output
    if not feature_list:  # If feature_list is empty after attempting to load files
        print("No embeddings were loaded. Please check the file paths and database entries.")
    else:
        feature_list = np.array(feature_list)
    image_paths = [image_path for _, image_path, _ in paths]
    item_ids = [item_id for _, _, item_id in paths]
    return feature_list, image_paths, item_ids


def recommend(features, feature_list, image_paths, item_ids):
    """Recommend items based on features."""
    print(f"Features shape (before reshape): {features.shape}")  # Debugging
    features = features.reshape(1, -1)
    print(f"Features shape (after reshape): {features.shape}")  # Debugging
    print(f"Feature list shape: {feature_list.shape}")  # Debugging

    neighbors = NearestNeighbors(n_neighbors=5, algorithm='auto', metric='cosine')
    neighbors.fit(feature_list)
    distances, indices = neighbors.kneighbors(features)
    
    recommended_image_paths = [image_paths[i].replace('\\', '/') for i in indices[0]]
    recommended_item_ids = [item_ids[i] for i in indices[0]]

    return recommended_image_paths, recommended_item_ids

def get_recommendations(img_path, occasion, gender, bodytype=None):
    """Get recommendations for an image path based on occasion, gender, and optionally bodytype."""
    features = feature_extraction(img_path)
    feature_list, image_paths, item_ids = load_occasion_data(occasion, gender, bodytype)
    
    return recommend(features, feature_list, image_paths, item_ids)


def insert_recommendations(user_id, recommended_item_ids):
    """Insert recommendations into the database."""
    conn = sqlite3.connect('your_database.db')
    cursor = conn.cursor()

    try:
        for item_id in recommended_item_ids:
            timestamp = datetime.datetime.now()
            cursor.execute('''
                INSERT INTO recommendations (user_id, item_id, timestamp)
                VALUES (?, ?, ?)
            ''', (user_id, item_id, timestamp))
        conn.commit()
    except Exception as e:
        print("Database error: ", e)
    finally:
        conn.close()
        
def update_feedback(cursor, item_id, user_id, action, rating):

    cursor.execute('SELECT * FROM item_ratings WHERE item_id = ?', (item_id,))
    item = cursor.fetchone()

    # Handle likes and ratings for item_ratings table
    if action == 'like':
         if item:
            # Update existing record in item_ratings
            cursor.execute('''
                UPDATE item_ratings 
                SET num_likes = num_likes + 1 
                WHERE item_id = ?
            ''', (item_id,))
         else:
            # Insert new record into item_ratings
            cursor.execute('''
                INSERT INTO item_ratings (item_id, num_likes, average_rating, num_ratings)
                VALUES (?, 1, 0.0, 0)
            ''', (item_id,))

    elif action == 'rate':
         rating = int(data['rating']) if data['rating'].isdigit() else 0
         if item:
            # Update existing record in item_ratings
            cursor.execute('''
                UPDATE item_ratings 
                SET average_rating = ((average_rating * num_ratings) + ?) / (num_ratings + 1),
                    num_ratings = num_ratings + 1
                WHERE item_id = ?
            ''', (rating, item_id))
         else:
            # Insert new record into item_ratings
            cursor.execute('''
                INSERT INTO item_ratings (item_id, num_likes, average_rating, num_ratings)
                VALUES (?, 0, ?, 1)
            ''', (item_id, rating))

    # Check if there is already feedback for the given user-item pair
    cursor.execute('''
        SELECT * FROM feedback 
        WHERE user_id = ? AND recommendation_id = ?
     ''', (user_id, item_id))
    feedback = cursor.fetchone()

    if action == 'like':
         liked = True if action == 'like' else False
         if feedback:
             cursor.execute('''
                 UPDATE feedback 
                 SET liked = ?, 
                     feedback_date = CURRENT_TIMESTAMP
                 WHERE user_id = ? AND recommendation_id = ?
             ''', (liked, user_id, item_id))
         else:
             cursor.execute('''
                 INSERT INTO feedback 
                 (recommendation_id, user_id, rating, liked, feedback_date)
                 VALUES (?, ?, NULL, ?, CURRENT_TIMESTAMP)
             ''', (item_id, user_id, liked))

    elif action == 'rate':
         if feedback:
             cursor.execute('''
                 UPDATE feedback 
                 SET rating = ?, 
                     feedback_date = CURRENT_TIMESTAMP
                 WHERE user_id = ? AND recommendation_id = ?
             ''', (rating, user_id, item_id))
         else:
             cursor.execute('''
                 INSERT INTO feedback 
                (recommendation_id, user_id, rating, liked, feedback_date)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
             ''', (item_id, user_id, rating, feedback['liked'] if feedback else False))
def load_all_data():
    """
    Load feature vectors, image paths, and item IDs for all items.
    This function is hypothetical and needs to be implemented based on your application's specific data storage and organization.
    """
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        query = "SELECT file_path, image_path, item_id FROM embeddings"
        cursor.execute(query)
        paths = cursor.fetchall()
        conn.close()

        feature_list = []
        for embedding_path, _, _ in paths:
            if os.path.exists(embedding_path):
                feature_list.append(np.load(embedding_path))
        feature_list = np.array(feature_list)

        image_paths = [image_path for _, image_path, _ in paths]
        item_ids = [item_id for _, _, item_id in paths]

        return feature_list, image_paths, item_ids
    except Exception as e:
        print(f"Database error in load_all_data: {e}")
        return np.array([]), [], []
    
def get_more_recommendations(selected_item_id):
    """
    Get more recommendations based on a selected item ID.
    """
    try:
        # Fetch the feature vector for the selected item.
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM embeddings WHERE item_id = ?", (selected_item_id,))
        selected_item_path = cursor.fetchone()[0]
        conn.close()

        if not selected_item_path:
            raise Exception("Selected item's feature path not found in the database.")

        # Assuming the selected item's features are stored in a .npy file.
        selected_item_features = np.load(selected_item_path) if os.path.exists(selected_item_path) else None
        if selected_item_features is None:
            raise Exception("Feature file for the selected item does not exist.")

        # Fetch features for all items (or a subset if you want to limit the scope).
        feature_list, image_paths, item_ids = load_all_data()  # Assuming this function fetches data for all items.

        # Recommend items based on the selected item's features.
        recommended_image_paths, recommended_item_ids = recommend(selected_item_features, feature_list, image_paths, item_ids)
        recommendations = [
            (path, id_) for path, id_ in zip(recommended_image_paths, recommended_item_ids)
            if id_ != selected_item_id
        ]

        # If filtering out the selected item results in fewer recommendations, adjust logic accordingly.
        # This part is conceptual; implementation depends on your specific setup.
        # Ensure you have enough recommendations after filtering.
        # If not, you may need to adjust your recommendation logic to account for this scenario.

        return [path for path, _ in recommendations], [id_ for _, id_ in recommendations]

    except Exception as e:
        print(f"Error in get_more_recommendations: {e}")
        return [], []

