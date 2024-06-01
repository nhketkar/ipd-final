import sqlite3

def get_most_liked_items_by_gender(db_path, gender):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQL query to join embeddings and item_ratings tables,
    # filter by gender, and order by num_likes
    query = '''
    SELECT e.item_id, e.occasion, e.file_path, e.image_path, e.Gender, e.bodytype, i.num_likes, i.average_rating, i.num_ratings
    FROM embeddings e
    JOIN item_ratings i ON e.item_id = i.item_id
    WHERE e.Gender = ?
    ORDER BY i.num_likes DESC
    '''

    # Execute the query and fetch the results
    cursor.execute(query, (gender,))
    items = cursor.fetchall()

    # Close the database connection
    conn.close()

    return items

if __name__ == "__main__":
    db_path = 'your_database.db'  # Path to your SQLite database
    gender = 'Female'  # Example gender to filter by

    # Get the most liked items for the specified gender
    most_liked_items = get_most_liked_items_by_gender(db_path, gender)
    
    # Print the results
    for item in most_liked_items:
        print(f"Item ID: {item[0]}, Occasion: {item[1]}, File Path: {item[2]}, Image Path: {item[3]}, Gender: {item[4]}, Bodytype: {item[5]}, Num Likes: {item[6]}, Average Rating: {item[7]}, Num Ratings: {item[8]}")
