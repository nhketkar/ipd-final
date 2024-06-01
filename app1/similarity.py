import sqlite3
import numpy as np
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
        # Extract item ID from file name, adjusting for the 'party_X.npy' format
        filename = path.split('/')[-1]  # Get the filename ('party_0.npy')
        item_id_str = filename.split('_')[-1].replace('.npy', '')  # Extract '0' from 'party_0.npy'
        item_id = int(item_id_str)+1  # Convert to integer
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
def load_similarity_matrix(save_path):
    return np.load(save_path)

def similar(db_path, target_item_id, gender):
    """
    Fetch similar item IDs and filter image paths by specified gender.
    """
    # Your existing logic to get similar item IDs
    paths = get_embedding_paths(db_path)
    embeddings = load_embeddings(paths)
    similarity_matrix = load_similarity_matrix('similarity_matrix.npy')
    id_to_index, index_to_id = create_id_index_mapping(paths)
    similar_item_ids = get_similar_items_by_id(target_item_id, similarity_matrix, id_to_index, index_to_id)
    print(f"Items similar to item ID {target_item_id} are: {similar_item_ids}")

    # New logic to fetch image paths for the similar items from the database with a gender filter
    image_paths = fetch_image_paths_for_items(db_path, similar_item_ids, gender)
    return image_paths, similar_item_ids

def fetch_image_paths_for_items(db_path, item_ids, gender):
    """
    Fetch the image paths for given item IDs from the embeddings table in the database,
    filtered by the specified gender.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prepare a query that selects image paths for all similar item IDs filtered by gender
    placeholders = ','.join('?' for _ in item_ids)  # Adjust placeholder generation
    query = f"""
    SELECT item_id, image_path 
    FROM embeddings 
    WHERE item_id IN ({placeholders}) AND Gender = ?
    """
    # Execute the query with item IDs and the gender filter
    cursor.execute(query, item_ids + [gender])
    result = cursor.fetchall()

    # Mapping of item ID to its image path
    item_id_to_path = {item_id: image_path for item_id, image_path in result}

    conn.close()
    return [item_id_to_path[item_id] for item_id in item_ids if item_id in item_id_to_path]


# Example usage
if __name__ == "__main__":
    db_path = 'your_database.db'
    target_item_id = 123  # Example target item ID
    similar_image_paths = similar(db_path, target_item_id)
    print(f"Image paths of items similar to item ID {target_item_id}: {similar_image_paths}")

