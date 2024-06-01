import sqlite3
import numpy as np

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
def fetch_num_user_interactions(user_id, db_path='your_database.db'):
    """
    Fetch the total number of interactions a user has had, based on likes and ratings.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count the number of interactions (likes and ratings) for the user
    interactions_query = '''
    SELECT COUNT(*)
    FROM feedback
    WHERE user_id = ? AND (liked = 1 OR rating > 0)
    '''
    cursor.execute(interactions_query, (user_id,))
    num_interactions = cursor.fetchone()[0]

    conn.close()
    return num_interactions


def fetch_item_data(item_ids, db_path='your_database.db'):
    if not item_ids:
        return {}
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    placeholders = ', '.join(['?'] * len(item_ids))
    query = f"SELECT item_id, num_likes, average_rating FROM item_ratings WHERE item_id IN ({placeholders})"
    cursor.execute(query, item_ids)
    items_data = {item_id: {'num_likes': num_likes, 'average_rating': average_rating} for item_id, num_likes, average_rating in cursor.fetchall()}
    
    conn.close()
    return items_data

def calculate_reward(num_likes, average_rating, like_weight=0.7, rating_weight=0.3):
    return (num_likes * like_weight) + (average_rating * rating_weight)

def normalize_rewards(rewards):
    if not rewards:
        return {}
    min_reward = min(rewards.values())
    max_reward = max(rewards.values())
    range_reward = max_reward - min_reward
    if range_reward == 0:
        return {item_id: 1.0 for item_id in rewards}
    else:
        return {item_id: round((reward - min_reward) / range_reward, 4) for item_id, reward in rewards.items()}

def softmax(rewards):
    max_reward = max(rewards.values())
    exp_rewards = {item_id: np.exp(reward - max_reward) for item_id, reward in rewards.items()}
    sum_exp_rewards = sum(exp_rewards.values())
    return {item_id: exp_reward / sum_exp_rewards for item_id, exp_reward in exp_rewards.items()}

def adaptive_epsilon(num_interactions):
    return max(0.01, min(1, 1 - np.log10((num_interactions + 1) / 25)))

def epsilon_greedy_softmax(probabilities, num_interactions):
    epsilon = adaptive_epsilon(num_interactions)
    if np.random.rand() < epsilon:
        return np.random.choice(list(probabilities.keys()))
    else:
        return np.random.choice(list(probabilities.keys()), p=list(probabilities.values()))

def calculate_dcg(scores):
    return np.sum([(2**rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(scores)])

def calculate_ndcg(actual_ranking_order, rewards):
    dcg = calculate_dcg([rewards[item_id] for item_id in actual_ranking_order])
    ideal_ranking_order = sorted(rewards, key=rewards.get, reverse=True)
    idcg = calculate_dcg([rewards[item_id] for item_id in ideal_ranking_order])
    return dcg / idcg if idcg > 0 else 0

if __name__ == "__main__":
    user_id = 6  # Example user ID for demonstration
    db_path = 'your_database.db'  # Path to the SQLite database

    num_interactions = fetch_num_user_interactions(user_id, db_path)
    item_ids = fetch_user_interacted_items(user_id, db_path)
    
    if not item_ids:
        print("No items found for the user.")
    else:
        items_data = fetch_item_data(item_ids, db_path)
        
        items_rewards = {item_id: calculate_reward(data['num_likes'], data['average_rating']) for item_id, data in items_data.items()}

        if not items_rewards:
            print("No rewards calculated for items.")
        else:
            normalized_rewards = normalize_rewards(items_rewards)
            probabilities = softmax(normalized_rewards)

            for item_id in items_rewards:
                print(f"Item ID: {item_id}, Reward: {items_rewards[item_id]}, Normalized Reward: {normalized_rewards[item_id]}, Probability: {probabilities[item_id]}")

            selected_item_id = epsilon_greedy_softmax(probabilities, num_interactions)
            print(f"\nSelected Item ID: {selected_item_id}")

            # Calculate and print NDCG score
            actual_ranking_order = normalized_rewards # Based on normalized rewards
            ndcg_score = calculate_ndcg(actual_ranking_order, normalized_rewards)
            print(f"NDCG Score: {ndcg_score}")
            ideal_ranking_order = sorted(items_rewards, key=items_rewards.get, reverse=True)
            rank_of_highest_reward_item = ideal_ranking_order.index(list(items_rewards.keys())[list(items_rewards.values()).index(max(items_rewards.values()))]) + 1
            rank_of_selected_item = ideal_ranking_order.index(selected_item_id) + 1

            # Calculate the difference in ranks
            rank_difference = abs(rank_of_highest_reward_item - rank_of_selected_item)

            print(f"Rank of highest reward item: {rank_of_highest_reward_item}")
            print(f"Rank of selected item: {rank_of_selected_item}")
            print(f"Rank difference: {rank_difference}")