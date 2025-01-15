# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_secreta'

DB_FILE = 'social_app.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de la base de datos
DB_FILE = 'social_app.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Crear tablas si no existen
with get_db_connection() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_photo TEXT,
            cover_photo TEXT,
            bio TEXT,
            birthday TEXT,
            location TEXT,
            job TEXT,
            hobbies TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            photo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'accepted',
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(friend_id) REFERENCES users(id)
        )
    ''')
    conn.commit()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'error')
        else:
            try:
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
                with get_db_connection() as conn:
                    conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                                 (username, email, hashed_password))
                    conn.commit()
                flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('El usuario o correo ya existe.', 'error')
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder al inicio.', 'error')
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    # Contar mensajes no leídos
    with get_db_connection() as conn:
        unread_messages_count = conn.execute('''
            SELECT COUNT(*) 
            FROM messages 
            WHERE receiver_id = ? AND is_read = 0
        ''', (current_user_id,)).fetchone()[0]

    # Obtener publicaciones
    with get_db_connection() as conn:
        posts = conn.execute('''
            SELECT posts.*, users.username, users.profile_photo
            FROM posts
            JOIN users ON posts.user_id = users.id
            ORDER BY created_at DESC
        ''').fetchall()

    return render_template(
        'dashboard.html',
        user=session['username'],
        posts=posts,
        unread_messages_count=unread_messages_count
    )

@app.route('/messages', methods=['GET'])
def message_list():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a los mensajes.', 'error')
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    with get_db_connection() as conn:
        contacts = conn.execute('''
            SELECT DISTINCT u.id AS contact_id, u.username, u.profile_photo,
                            (SELECT m.message
                             FROM messages m
                             WHERE (m.sender_id = u.id AND m.receiver_id = ?)
                                OR (m.sender_id = ? AND m.receiver_id = u.id)
                             ORDER BY m.timestamp DESC LIMIT 1) AS last_message,
                            (SELECT m.timestamp
                             FROM messages m
                             WHERE (m.sender_id = u.id AND m.receiver_id = ?)
                                OR (m.sender_id = ? AND m.receiver_id = u.id)
                             ORDER BY m.timestamp DESC LIMIT 1) AS last_message_time
            FROM users u
            LEFT JOIN messages m ON u.id = m.sender_id OR u.id = m.receiver_id
            WHERE u.id != ?
            ORDER BY last_message_time DESC
        ''', (current_user_id, current_user_id, current_user_id, current_user_id, current_user_id)).fetchall()

    return render_template('message_list.html', contacts=contacts)

@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
def chat_with_user(user_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a los mensajes.', 'error')
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    with get_db_connection() as conn:
        recipient = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not recipient:
            flash('El usuario no existe.', 'error')
            return redirect(url_for('message_list'))

    with get_db_connection() as conn:
        chat = conn.execute('''
            SELECT m.*, u.username AS sender_username
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.timestamp ASC
        ''', (current_user_id, user_id, user_id, current_user_id)).fetchall()

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash('El mensaje no puede estar vacío.', 'error')
            return redirect(url_for('chat_with_user', user_id=user_id))

        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO messages (sender_id, receiver_id, message)
                VALUES (?, ?, ?)
            ''', (current_user_id, user_id, content))
            conn.commit()
        flash('Mensaje enviado con éxito.', 'success')
        return redirect(url_for('chat_with_user', user_id=user_id))
    
    return render_template('messages.html', chat=chat, recipient=recipient)

@app.route('/search', methods=['GET'])
def search():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para buscar usuarios.', 'error')
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip()
    results = []
    if query:
        with get_db_connection() as conn:
            results = conn.execute('SELECT * FROM users WHERE username LIKE ?', ('%' + query + '%',)).fetchall()

    return render_template('search.html', results=results)


@app.route('/friends', methods=['GET'])
def friends():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tus amigos.', 'error')
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    with get_db_connection() as conn:
        friends_list = conn.execute('''
            SELECT id, username, profile_photo 
            FROM users 
            WHERE id IN (SELECT friend_id FROM friendships WHERE user_id = ?)
        ''', (current_user_id,)).fetchall()

    return render_template('friends.html', friends=friends_list)

# Lista de mensajes


@app.route('/photos', methods=['GET'])
def photos():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a tus fotos.', 'error')
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        photos_list = conn.execute('''
            SELECT photo, created_at
            FROM posts
            WHERE user_id = ? AND photo IS NOT NULL
            ORDER BY created_at DESC
        ''', (session['user_id'],)).fetchall()

    return render_template('photos.html', photos=photos_list)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a la configuración.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Procesa los cambios en la configuración (puedes personalizar esta lógica)
        flash('Configuración actualizada con éxito.', 'success')

    return render_template('settings.html')

@app.route('/events', methods=['GET'])
def events():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a los eventos.', 'error')
        return redirect(url_for('login'))

    # Ejemplo: Lista de eventos simulados
    events_list = [
        {'name': 'Evento 1', 'date': '2025-01-20', 'location': 'Ciudad A'},
        {'name': 'Evento 2', 'date': '2025-02-15', 'location': 'Ciudad B'},
    ]

    return render_template('events.html', events=events_list)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder al perfil.', 'error')
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        posts = conn.execute('''
            SELECT * FROM posts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (session['user_id'],)).fetchall()

    if request.method == 'POST':
        # Publicar una nueva foto desde el perfil
        content = request.form.get('content')
        photo = request.files.get('photo')

        photo_filename = None
        if photo and photo.filename != '':
            photo_filename = secure_filename(f"profile_{session['user_id']}_{photo.filename}")
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        with get_db_connection() as conn:
            conn.execute('INSERT INTO posts (user_id, content, photo) VALUES (?, ?, ?)',
                         (session['user_id'], content, photo_filename))
            conn.commit()
        flash('Publicación realizada con éxito.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user, posts=posts)

@app.route('/update_profile_photo', methods=['POST'])
def update_profile_photo():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para realizar esta acción.', 'error')
        return redirect(url_for('login'))

    photo = request.files.get('profile_photo')
    content = request.form.get('content', '')

    if photo and photo.filename != '':
        filename = secure_filename(f"profile_{session['user_id']}_{photo.filename}")
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with get_db_connection() as conn:
            # Actualizar la foto de perfil del usuario
            conn.execute('UPDATE users SET profile_photo = ? WHERE id = ?', (filename, session['user_id']))

            # Crear una publicación si se añade contenido
            if content.strip():
                conn.execute('INSERT INTO posts (user_id, content, photo) VALUES (?, ?, ?)',
                             (session['user_id'], content, filename))

            conn.commit()

        flash('Foto de perfil actualizada exitosamente.', 'success')

    return redirect(url_for('profile'))


@app.route('/update_cover_photo', methods=['POST'])
def update_cover_photo():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para realizar esta acción.', 'error')
        return redirect(url_for('login'))

    photo = request.files.get('cover_photo')
    content = request.form.get('content', '')

    if photo and photo.filename != '':
        filename = secure_filename(f"cover_{session['user_id']}_{photo.filename}")
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with get_db_connection() as conn:
            # Actualizar la foto de portada del usuario
            conn.execute('UPDATE users SET cover_photo = ? WHERE id = ?', (filename, session['user_id']))

            # Crear una publicación si se añade contenido
            if content.strip():
                conn.execute('INSERT INTO posts (user_id, content, photo) VALUES (?, ?, ?)',
                             (session['user_id'], content, filename))

            conn.commit()

        flash('Foto de portada actualizada exitosamente.', 'success')

    return redirect(url_for('profile'))

@app.route('/profile/<int:user_id>', methods=['GET'])
def view_user_profile(user_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder a los perfiles.', 'error')
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        # Obtener información del usuario por su ID
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('El perfil que intentas visitar no existe.', 'error')
            return redirect(url_for('dashboard'))

        # Obtener publicaciones del usuario
        posts = conn.execute('''
            SELECT * FROM posts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,)).fetchall()

    return render_template('profile.html', user=user, posts=posts)



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Se ha cerrado sesión correctamente.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)