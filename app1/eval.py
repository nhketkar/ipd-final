import sqlite3
def fetch_user_interacted_items(user_id, db_path='your_database.db'):
    """
    Fetch item IDs of items liked and/or rated by the user.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    liked_items_query = '''
    SELECT e.item_id
    FROM feedback f
    JOIN embeddings e ON f.recommendation_id = e.item_id
    WHERE f.user_id = ? AND f.liked = 1
    '''
    cursor.execute(liked_items_query, (user_id,))
    liked_items = cursor.fetchall()

    rated_items_query = '''
    SELECT e.item_id
    FROM feedback f
    JOIN embeddings e ON f.recommendation_id = e.item_id
    WHERE f.user_id = ? AND f.rating > 0
    '''
    cursor.execute(rated_items_query, (user_id,))
    rated_items = cursor.fetchall()

    # Combine and remove duplicates
    item_ids = set([item[0] for item in liked_items + rated_items])

    conn.close()
    return list(item_ids)
import sqlite3

def calculate_repeated_recommendation_percentage_all(user_id, db_path='your_database.db'):
    """
    Calculate the percentage of items displayed in all recommendations that the user has already interacted with.
    
    :param user_id: ID of the user
    :param db_path: Path to the SQLite database
    :return: Percentage of recommended items that were previously liked or rated by the user
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Fetch user-interacted items
    user_interacted_items = set(fetch_user_interacted_items(user_id, db_path))
    
    # Fetch all recommended item IDs for the user from recommendation_displays
    cursor.execute('''
    SELECT item_ids FROM recommendation_displays
    WHERE user_id = ?''', (user_id,))
    all_results = cursor.fetchall()
    
    # Flatten the list of all recommended item IDs
    all_recommended_item_ids = set()
    for result in all_results:
        item_ids = [int(item_id) for item_id in result[0].split(',')]
        all_recommended_item_ids.update(item_ids)
    
    # Calculate the intersection of interacted and recommended items
    interacted_recommended_intersection = user_interacted_items.intersection(all_recommended_item_ids)
    
    # Calculate the percentage
    if all_recommended_item_ids:
        percentage = (len(interacted_recommended_intersection) / len(all_recommended_item_ids)) * 100
    else:
        percentage = 0  # Avoid division by zero if there are no recommended items
    
    conn.close()
    return percentage

# Example usage
user_id = 9# Example user ID
db_path = 'your_database.db'  # Path to your SQLite database

percentage = calculate_repeated_recommendation_percentage_all(user_id, db_path)
print(f"Percentage of recommended items already interacted with (across all recommendations): {percentage}%")
