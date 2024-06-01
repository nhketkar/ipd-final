import sqlite3

# Connect to your database
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# Update the file paths
cursor.execute("UPDATE embeddings SET item_id=item_id+1")
conn.commit()
conn.close()
