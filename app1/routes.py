from flask import request, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from .forms import LoginForm, RegisterForm
from .reco import get_recommendations,insert_recommendations,get_more_recommendations
from .classify import classify_body_type
from .rl import fetch_user_interacted_items,fetch_item_data,calculate_reward,normalize_rewards,epsilon_greedy_softmax,softmax,fetch_num_user_interactions,calculate_ndcg
from .similarity import similar
from .mostliked import get_most_liked_items_by_gender
from .ctr import update_clicks_and_ctr,update_impressions
import os
import sqlite3
import datetime
from flask import jsonify

def create_routes(app):

    def allowed_file(filename):
        """Check if the uploaded file has an allowed extension."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def get_db_connection():
        conn = sqlite3.connect('your_database.db')
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d
        conn.row_factory = dict_factory
        return conn

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            occasion = request.form.get('occasion')
            session['selected_occasion'] = occasion
            file = request.files.get('image')
            user_gender = session.get('user_gender')  # Assume this is already set in the session

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(img_path)

                try:
                    user_id = session.get('user_id')
                    # user_gender is already fetched above, no need to fetch again
                    bodytype = session.get('bodytype')  # This may not be necessary for males

                    # Adjust the condition based on gender
                    if user_id and user_gender:
                        if user_gender == 'Female' and not bodytype:
                            flash("Please classify your body type to get recommendations", "warning")
                            return redirect(url_for('classify'))  # Assuming 'classify' is the route to classify body type
                        else:
                            # For male users, bodytype can be None
                            recommended_image_paths, recommended_item_ids = get_recommendations(img_path, occasion, user_gender, bodytype if user_gender == 'Female' else None)
                            recommendations = list(zip(recommended_image_paths, recommended_item_ids))

                            # Insert recommendations into the database
                            insert_recommendations(user_id, recommended_item_ids)

                            return render_template('results.html', recommendations=recommendations)
                    else:
                        flash("You need to log in and have gender information to get recommendations", "warning")
                        return redirect(url_for('login'))
                except Exception as e:
                    print(e)
                    return render_template('error.html', message="Error in processing the image.")
        else:
            # GET request handling, if necessary
            return render_template('index.html')

    @app.route('/more_like_this', methods=['GET'])

    def more_like_this():
        item_id = request.args.get('item_id')
        if item_id:
            try:
                item_id = int(item_id)  # Convert item_id to int
                
                # Fetch more recommendations based on the selected item_id
                recommended_image_paths, recommended_item_ids = get_more_recommendations(item_id)
                
                # Prepare the recommendations to pass to the template
                recommendations = list(zip(recommended_image_paths, recommended_item_ids))
                
                # Render a new template with the recommendations
                return render_template('new_recommendations.html', recommendations=recommendations)
            except ValueError:
                # Handle the case where item_id is not convertible to the right type
                flash("Invalid item ID format.", "warning")
                return redirect(url_for('index'))  # Redirect to the index or another appropriate page
            except Exception as e:
                # Log the exception details here to debug issues
                print(f"Error fetching more like this recommendations: {e}")
                flash("Internal Server Error", "warning")
                return redirect(url_for('index'))  # Redirect to the index or another appropriate page
        else:
            flash("No item ID provided", "warning")
            return redirect(url_for('index'))  # Redirect to the index or another appropriate page

    
    @app.route('/classify', methods=['GET', 'POST'])
    def classify():
     if request.method == 'POST':
        # Retrieve measurements from the form
        bust = int(request.form.get('bust'))
        cup=request.form.get('cup')
        waist = int(request.form.get('waist'))
        hip = int(request.form.get('hip'))
        bodytype = classify_body_type(bust, waist, hip)

        session['bodytype'] = bodytype

        # Provide feedback to the user or redirect as needed
        flash(f'Your body type is classified as: {bodytype}', 'info')

        return redirect(url_for('index'))
     else:
        return render_template('classify.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
     form = LoginForm()
     if form.validate_on_submit():
         conn = get_db_connection()
         cursor = conn.cursor()
         cursor.execute("SELECT * FROM users WHERE username = ?", (form.username.data,))
         user = cursor.fetchone()
         conn.close()

         if user and check_password_hash(user['password_hash'], form.password.data):
             flash('You have successfully logged in!', 'success')
             session['user_id'] = user['id']
             session['username'] = user['username']
             session['user_gender'] = user['gender']  # Store user's gender in the session
             return redirect(url_for('index'))
         else:
             flash('Invalid username or password', 'error')
             return redirect(url_for('login'))

     return render_template('login.html', form=form)


    @app.route('/register', methods=['GET', 'POST'])
    def register():
       form = RegisterForm()
       conn = None  # Initialize conn here
       try:
           if form.validate_on_submit():
               conn = get_db_connection()
               cursor = conn.cursor()
               # Check if username already exists
               cursor.execute('SELECT * FROM users WHERE username = ?', (form.username.data,))
               user = cursor.fetchone()
               if user:
                   flash('Username already exists. Please choose a different one.', 'danger')
                   return render_template('register.html', form=form)

               hashed_password = generate_password_hash(form.password.data)
               cursor.execute('''
                   INSERT INTO users (username, password_hash, age, gender, profession)
                   VALUES (?, ?, ?, ?, ?)
               ''', (form.username.data, hashed_password, form.age.data, form.gender.data, form.profession.data))
               conn.commit()
               flash('Registration successful!', 'success')
               return redirect(url_for('login'))
           else:
               if form.errors != {}:
                   for err_msg in form.errors.values():
                       flash(f'There was an error with creating a user: {err_msg}', 'danger')
       finally:
           if conn:
               conn.close()
       return render_template('register.html', form=form)
    @app.route('/browse')
    def browse():
        db_path = 'your_database.db'  # Specify the path to your SQLite database
        gender = session.get('user_gender')  # Assume gender is stored in session, change as needed
        most_liked_items = get_most_liked_items_by_gender(db_path, gender)    
        # Transform the items to ensure image paths use forward slashes
        items_formatted = [
            {
                'item_id': item[0],
                'occasion': item[1],
                'file_path': item[2].replace('\\', '/'),  # Ensure file paths use forward slashes
                'image_path': item[3].replace('\\', '/'),  # Ensure image paths use forward slashes
                'gender': item[4],
                'bodytype': item[5],
                'num_likes': item[6],
                'average_rating': item[7],
                'num_ratings': item[8]
            } for item in most_liked_items
        ]
        return render_template('browse.html', most_liked_items=items_formatted)



    @app.route('/user//feedback')
    def user_feedback():
        user_id = session.get('user_id')
        conn = sqlite3.connect('your_database.db')
        cursor = conn.cursor()

        # Fetch liked items
        liked_items_query = '''
        SELECT e.image_path, e.item_id
        FROM feedback f
        JOIN embeddings e ON f.recommendation_id = e.item_id
        WHERE f.user_id = ? AND f.liked = 1
        ORDER BY f.feedback_date DESC
        '''
        cursor.execute(liked_items_query, (user_id,))
        liked_items = cursor.fetchall()

        # Fetch rated items
        rated_items_query = '''
        SELECT e.image_path, e.item_id, f.rating
        FROM feedback f
        JOIN embeddings e ON f.recommendation_id = e.item_id
        WHERE f.user_id = ? AND f.rating > 0
        ORDER BY f.feedback_date DESC
        '''
        cursor.execute(rated_items_query, (user_id,))
        rated_items = cursor.fetchall()

        conn.close()

        return render_template('myaccount.html', liked_items=liked_items, rated_items=rated_items)

    @app.route('/myrecommendation')
    def my_recommendation():
        user_id = session.get('user_id')
        user_gender = session.get('user_gender')
        if not user_id:
            return "Please log in to see recommendations.", 403

        db_path = 'your_database.db'
        
        num_interactions = fetch_num_user_interactions(user_id, db_path)
        item_ids = fetch_user_interacted_items(user_id, db_path=db_path)
        if not item_ids:
            return "No interactions found for user.", 404
        
        items_data = fetch_item_data(item_ids, db_path=db_path)
        items_rewards = {item_id: calculate_reward(data['num_likes'], data['average_rating']) for item_id, data in items_data.items()}
        
        if not items_rewards:
            return "Could not calculate rewards for items.", 404
        
        normalized_rewards = normalize_rewards(items_rewards)
        probabilities = softmax(normalized_rewards)
        
        selected_item_id = epsilon_greedy_softmax(probabilities, num_interactions)
        
        # Calculate rank difference here
        ideal_ranking_order = sorted(items_rewards, key=items_rewards.get, reverse=True)
        rank_of_selected_item = ideal_ranking_order.index(selected_item_id) + 1
        rank_difference = abs(1 - rank_of_selected_item)  # Assuming the highest reward item has a rank of 1
        actual_ranking_order = normalized_rewards
        ndcg_score = calculate_ndcg(actual_ranking_order, normalized_rewards)
        
        image_paths, similar_item_ids = similar(db_path=db_path, target_item_id=selected_item_id, gender=user_gender)
        
        recommendations = list(zip(similar_item_ids, image_paths))
        
        # Updated to include rank_difference
        display_id = log_display(user_id, [item[0] for item in recommendations], ndcg_score, rank_difference, db_path)
        
        return render_template('recommendations.html', recommendations=recommendations, display_id=display_id)


    def log_display(user_id, item_ids, ndcg_score, rank_difference, db_path='your_database.db'):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        item_ids_str = ','.join(map(str, item_ids))
        
        user_interacted_items = set(fetch_user_interacted_items(user_id, db_path))
        
        recommended_item_ids = set(item_ids)
        interacted_recommended_intersection = user_interacted_items.intersection(recommended_item_ids)
        interaction_percentage = (len(interacted_recommended_intersection) / len(recommended_item_ids)) * 100 if recommended_item_ids else 0
        
        cursor.execute('''
        INSERT INTO recommendation_displays (user_id, item_ids, ndcg_score, interaction_percentage, rank_difference) 
        VALUES (?, ?, ?, ?, ?)''', (user_id, item_ids_str, ndcg_score, interaction_percentage, rank_difference))
        
        display_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return display_id

    @app.route('/logout')
    def logout():
        session.clear()  # Clear the session
        flash("You have been logged out.", "success")
        return redirect(url_for('index'))

    @app.route('/rate_item', methods=['POST'])
    def rate_item():
     data = request.json
     item_id = data['itemID']
     action = data['action']
     user_id = session.get('user_id')  # Assumes user ID is stored in the session

     conn = get_db_connection()
     cursor = conn.cursor()

     # Check if the item_id already exists in the item_ratings table
     cursor.execute('SELECT * FROM item_ratings WHERE item_id = ?', (item_id,))
     item = cursor.fetchone()

    # Handle likes and ratings for item_ratings table
     if action == 'like':
         if item:
            # Update existing record in item_ratings
            cursor.execute('''
                UPDATE item_ratings 
                SET num_likes = num_likes + 1 
                WHERE item_id = ?
            ''', (item_id,))
         else:
            # Insert new record into item_ratings
            cursor.execute('''
                INSERT INTO item_ratings (item_id, num_likes, average_rating, num_ratings)
                VALUES (?, 1, 0.0, 0)
            ''', (item_id,))

     elif action == 'rate':
         rating = int(data['rating']) if data['rating'].isdigit() else 0
         if item:
            # Update existing record in item_ratings
            cursor.execute('''
                UPDATE item_ratings 
                SET average_rating = ((average_rating * num_ratings) + ?) / (num_ratings + 1),
                    num_ratings = num_ratings + 1
                WHERE item_id = ?
            ''', (rating, item_id))
         else:
            # Insert new record into item_ratings
            cursor.execute('''
                INSERT INTO item_ratings (item_id, num_likes, average_rating, num_ratings)
                VALUES (?, 0, ?, 1)
            ''', (item_id, rating))

    # Check if there is already feedback for the given user-item pair
     cursor.execute('''
        SELECT * FROM feedback 
        WHERE user_id = ? AND recommendation_id = ?
     ''', (user_id, item_id))
     feedback = cursor.fetchone()

     if action == 'like':
         liked = True if action == 'like' else False
         if feedback:
             cursor.execute('''
                 UPDATE feedback 
                 SET liked = ?, 
                     feedback_date = CURRENT_TIMESTAMP
                 WHERE user_id = ? AND recommendation_id = ?
             ''', (liked, user_id, item_id))
         else:
             cursor.execute('''
                 INSERT INTO feedback 
                 (recommendation_id, user_id, rating, liked, feedback_date)
                 VALUES (?, ?, NULL, ?, CURRENT_TIMESTAMP)
             ''', (item_id, user_id, liked))

     elif action == 'rate':
         if feedback:
             cursor.execute('''
                 UPDATE feedback 
                 SET rating = ?, 
                     feedback_date = CURRENT_TIMESTAMP
                 WHERE user_id = ? AND recommendation_id = ?
             ''', (rating, user_id, item_id))
         else:
             cursor.execute('''
                 INSERT INTO feedback 
                (recommendation_id, user_id, rating, liked, feedback_date)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
             ''', (item_id, user_id, rating, feedback['liked'] if feedback else False))
     
     conn.commit()
     conn.close()
     return 'Success', 200
    
    



# Don't forget to call create_routes(app) in your main application file