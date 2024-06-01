import sqlite3
def update_impressions(user_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Increment total_impressions for the user
    cursor.execute('''
        INSERT INTO user_ctr (user_id, total_impressions, total_clicks, ctr) 
        VALUES (?, 1, 0, 0.0) 
        ON CONFLICT(user_id) 
        DO UPDATE SET total_impressions = total_impressions + 1;
    ''', (user_id,))
    conn.commit()
    conn.close()

def update_clicks_and_ctr(user_id, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Increment total_clicks and update CTR for the user
    cursor.execute('''
        UPDATE user_ctr 
        SET total_clicks = total_clicks + 1,
            ctr = CAST(total_clicks AS REAL) / total_impressions 
        WHERE user_id = ?;
    ''', (user_id,))
    conn.commit()
    conn.close()
