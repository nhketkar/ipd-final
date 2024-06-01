import sqlite3
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity

# Function to retrieve embedding paths from the database
def get_embedding_paths(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM embeddings")
    paths = [row[0] for row in cursor.fetchall()]
    conn.close()
    return paths

# Function to load embeddings given a list of file paths
def load_embeddings(paths):
    embeddings = [np.load(path) for path in paths]
    return np.array(embeddings)

# Function to calculate the cosine similarity matrix
def calculate_similarity_matrix(embeddings):
    similarity_matrix = cosine_similarity(embeddings)
    return similarity_matrix

# Function to create mappings between item IDs and matrix indices
def create_id_index_mapping(paths):
    id_to_index = {}
    index_to_id = {}
    for index, path in enumerate(paths):
        # Cross-platform way to get the filename
        filename = os.path.basename(path)
        item_id_str = filename.split('_')[-1].replace('.npy', '')  # Extract the item ID
        item_id = int(item_id_str)
        id_to_index[item_id] = index
        index_to_id[index] = item_id
    return id_to_index, index_to_id

# Function to find similar items based on an item ID
def get_similar_items_by_id(item_id, similarity_matrix, id_to_index, index_to_id, top_n=5):
    item_index = id_to_index[item_id]
    similarities = similarity_matrix[item_index]
    most_similar_indices = np.argsort(-similarities)[1:top_n+1]  # Exclude the item itself
    most_similar_ids = [index_to_id[index] for index in most_similar_indices]
    return most_similar_ids

# Function to save the similarity matrix to a file
def save_similarity_matrix(matrix, filename='app1/similarity_matrix.npy'):
    np.save(filename, matrix)
    print(f"Similarity matrix saved to {filename}")

# Main code to tie everything together
def main(db_path, target_item_id):
    paths = get_embedding_paths(db_path)
    embeddings = load_embeddings(paths)
    similarity_matrix = calculate_similarity_matrix(embeddings)
    id_to_index, index_to_id = create_id_index_mapping(paths)

    # Save the similarity matrix for future use
    save_similarity_matrix(similarity_matrix)

    similar_item_ids = get_similar_items_by_id(target_item_id, similarity_matrix, id_to_index, index_to_id)
    print(f"Items similar to item ID {target_item_id} are: {similar_item_ids}")

# Example usage
if __name__ == "__main__":
    db_path = 'your_database.db'  # Update this with your actual database path
    target_item_id = 6  # Specify the item ID you're interested in
    main(db_path, target_item_id)
