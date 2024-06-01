import sqlite3

# Create or connect to a database
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# Execute a query to create the embeddings table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY,
        occasion TEXT,
        item_id INTEGER,
        file_path TEXT,
        FOREIGN KEY (item_id) REFERENCES items(id)
    )
''')
conn.commit()
