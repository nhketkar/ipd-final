import sqlite3

# Path to your database file
DATABASE_PATH = 'your_database.db'

def connect_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def create_embeddings_table():
    """Create the embeddings table if it doesn't exist."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY,
            occasion TEXT,
            item_id INTEGER,
            file_path TEXT,
            image_path TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_embeddings(occasion):
    """Retrieve embedding data for a given occasion from the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT file_path, image_path, item_id FROM embeddings WHERE occasion=?', (occasion,))
    data = cursor.fetchall()
    conn.close()
    return data

def save_embedding(occasion, item_id, embedding_file_path, image_path):
    """Save embedding data to the database."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO embeddings (occasion, item_id, file_path, image_path) VALUES (?, ?, ?, ?)', 
                   (occasion, item_id, embedding_file_path, image_path))
    conn.commit()
    conn.close()
