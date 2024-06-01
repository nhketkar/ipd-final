import numpy as np
import os
import sqlite3
from sklearn.metrics.pairwise import cosine_similarity

def load_embeddings_and_paths(embeddings_dir):
    embedding_files = [os.path.join(embeddings_dir, f) for f in os.listdir(embeddings_dir) if f.endswith('.npy')]
    embeddings = []
    file_names = []
    for file_path in embedding_files:
        embedding = np.load(file_path)
        embeddings.append(embedding)
        file_names.append(os.path.basename(file_path))
    embeddings_array = np.stack(embeddings)
    return embeddings_array, file_names

def identify_duplicate_embeddings(embeddings_array, threshold=0.99):
    similarities = cosine_similarity(embeddings_array)
    duplicate_indices = []
    for i in range(len(similarities)):
        for j in range(i+1, len(similarities)):
            if similarities[i, j] > threshold:
                duplicate_indices.append((i, j))
    return duplicate_indices

def delete_duplicate_entries(db_path, duplicate_file_names):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for file_name in duplicate_file_names:
        embedding_path = f'embeddings/{file_name}'  # Adjust based on how paths are stored
        cursor.execute("DELETE FROM embeddings WHERE file_path = ?", (embedding_path,))
    conn.commit()
    conn.close()

def main():
    embeddings_dir = 'embeddings'
    db_path = 'your_database.db'
    
    embeddings_array, file_names = load_embeddings_and_paths(embeddings_dir)
    duplicate_indices = identify_duplicate_embeddings(embeddings_array)
    
    # Extract filenames of the duplicate embeddings
    duplicate_file_names = [file_names[j] for _, j in duplicate_indices]
    
    # Print duplicate filenames before proceeding with deletion
    print("Duplicate filenames identified for removal:")
    for filename in duplicate_file_names:
        print(filename)

    # Optionally, add a prompt or logging mechanism here if manual verification is needed
    # Example: input("Proceed with deletion? (y/n): ")

    delete_duplicate_entries(db_path, duplicate_file_names)

    print("Duplicate entries removal complete.")
if __name__ == "__main__":
    main()
