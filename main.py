import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash
from sqlCommands import MySql

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

crsr = MySql()

logged_in = False

UPLOAD_FOLDER = os.path.join('static', 'covers')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def sanitize_filename(filename):
    # Remove any characters that are not alphanumeric, underscores, hyphens, or spaces
    sanitized_filename = re.sub(r'[^\w\s-]', '', filename)
    # Replace consecutive spaces with a single space
    sanitized_filename = re.sub(r'\s+', ' ', sanitized_filename)
    # Strip leading and trailing spaces
    sanitized_filename = sanitized_filename.strip()
    return sanitized_filename


def game_in_library(game_id):
    if logged_in:
        user_id = session['user_id']
        owned_games = crsr.get_owned_games(user_id)
        if owned_games:
            return any(game['game_id'] == game_id for game in owned_games)
    return False


app.jinja_env.globals.update(game_in_library=game_in_library)


@app.template_filter('truncate_text')
def truncate_text(text, max_words=15, suffix='...'):
    words = text.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + suffix
    return text


@app.route('/')
def landing_page():
    return render_template('landing_page.html')


@app.route('/home')
def home():
    games = crsr.get_games_by_platform(platform='pc')
    platforms = ['PC', 'PS5', 'Xbox X', 'Nintendo Switch']
    return render_template('home.html', games=games,
                           platforms=platforms, cur_platform="PC", logged_in=logged_in)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = crsr.authenticate_user(username, password)
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            flash('Logged in successfully', 'success')
            global logged_in
            logged_in = True
            if user['user_id'] == 1:
                return redirect(url_for('admin'))
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    return redirect(url_for('home'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if crsr.get_user_by_username(username):
            flash('Username already exists', 'error')
        else:
            hashed_password = generate_password_hash(password)
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            user = []
            user.extend((username, hashed_password, phone, address, email))
            var = crsr.create_user(user)
            if var:
                user = crsr.get_user_by_username(username)
                session['user_id'] = user['user_id']
                session['username'] = username
                flash('Created Account successfully', 'Success')
                global logged_in
                logged_in = True
                return redirect(url_for('home'))
        flash('Error creating account', 'error')
    return redirect(url_for('home'))


@app.route('/filter', methods=['POST'])
def filter_games():
    platform = request.form['platform']
    games = crsr.get_games_by_platform(platform=platform)
    platforms = ['PC', 'PS5', 'Xbox X', 'Nintendo Switch']
    return render_template('home.html', games=games, platforms=platforms, cur_platform=platform, logged_in=logged_in)


@app.route('/game/<int:game_id>')
def game_details(game_id):
    game = crsr.get_game_by_id(game_id)
    if game:
        return render_template('game.html', game=game, logged_in=logged_in)
    else:
        return "Game not found", 404


@app.route('/profile')
def profile():
    user = crsr.get_user_by_username(session['username'])
    user_id = user['user_id']
    owned_games = crsr.get_owned_games(user_id)
    return render_template('profile.html', user=user, owned_games=owned_games, logged_in=logged_in)


@app.route('/buyGame', methods=['POST'])
def buyGame():
    if request.method == "POST":
        gameID = request.form.get('gameID')  # Retrieve game ID from the form
        if gameID:
            if 'username' in session:
                username = session['username']
                user = crsr.get_user_by_username(username)
                if user:
                    user_id = user['user_id']
                    order_id = crsr.add_game_to_bought(gameID, user_id)
                    if order_id:
                        flash('Game purchased successfully!', 'success')
                        order_details = crsr.get_order_details(order_id)
                        return render_template('orderScreen.html', order_details=order_details)

    return redirect(url_for('home'))


@app.route('/admin')
def admin():
    if not session['user_id'] == 1:
        abort(403)
    games = crsr.get_all_games()
    return render_template('admin.html', games=games, logged_in=logged_in)


@app.route('/delete_game', methods=['POST'])
def delete_game():
    if request.method == "POST":
        game_id = request.form.get('game_id')
        if game_id:
            # Implement the code to delete the game from the database using its ID
            if crsr.delete_game(game_id):
                flash('Game deleted successfully!', 'success')
            else:
                flash('Error deleting game!', 'error')
    return redirect(url_for('admin'))


@app.route('/addItem', methods=['POST', 'GET'])
def addItem():
    if request.method == 'POST':
        game_name = request.form['game_name']
        details = request.form['details']
        developer = request.form['developer']
        publisher = request.form['publisher']
        platform = request.form['platform']
        price = request.form['price']
        count = request.form['count']

        # Handling file upload
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('admin'))
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('admin'))
        if file and file.filename.endswith('.jpg'):
            filename = sanitize_filename(game_name) + '.jpg'
            # Save the file with the modified filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash('Invalid file format. Please upload a JPG file', 'error')
            return redirect(url_for('admin'))

        game = [game_name, details, developer, publisher, platform, price, count]
        if crsr.add_game_to_list(game):
            flash('Game added successfully!', 'success')
        else:
            flash('Error adding game', 'error')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    global logged_in
    logged_in = False
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
