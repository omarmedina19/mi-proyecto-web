from flask import Flask, render_template, request, redirect, url_for, flash, session
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Configuración de carpeta para subir archivos
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Simulación de base de datos para usuarios
users_db = {}
posts = []  # Lista global para almacenar las publicaciones

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'error')
        elif username in users_db:
            flash('El usuario ya existe.', 'error')
        else:
            users_db[username] = {
                "email": email,
                "password": password,
                "profile_photo": None,
                "cover_photo": None,
                "bio": "",
                "birthday": "",
                "location": "",
                "job": "",
                "hobbies": "",
                "phone": "",
                "friends": [],
                "friend_requests": []
            }
            flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users_db and users_db[username]['password'] == password:
            session['user'] = username
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        flash('Debes iniciar sesión para acceder al inicio.', 'error')
        return redirect(url_for('login'))
    user = session['user']
    query = request.args.get('query')
    friend_matches = [friend for friend in users_db if query and query.lower() in friend.lower()]
    return render_template('dashboard.html', user=user, posts=posts, friends=friend_matches)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        flash('Debes iniciar sesión para acceder al perfil.', 'error')
        return redirect(url_for('login'))
    
    user = session['user']

    if request.method == 'POST':
        if 'profile_photo' in request.files:
            profile_photo = request.files['profile_photo']
            if profile_photo.filename != '':
                photo_filename = f"{user}_profile_{profile_photo.filename}"
                profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                users_db[user]["profile_photo"] = photo_filename
                flash('Foto de perfil actualizada.', 'success')

        bio = request.form.get('bio', users_db[user].get("bio"))
        birthday = request.form.get('birthday', users_db[user].get("birthday"))
        location = request.form.get('location', users_db[user].get("location"))
        job = request.form.get('job', users_db[user].get("job"))
        hobbies = request.form.get('hobbies', users_db[user].get("hobbies"))

        users_db[user].update({
            "bio": bio,
            "birthday": birthday,
            "location": location,
            "job": job,
            "hobbies": hobbies
        })

        flash('Perfil actualizado exitosamente.', 'success')

    return render_template('profile.html', user=user, user_data=users_db[user])

@app.route('/post', methods=['POST'])
def post():
    if 'user' not in session:
        flash('Debes iniciar sesión para publicar.', 'error')
        return redirect(url_for('login'))

    user = session['user']
    content = request.form.get('content')
    photo = request.files.get('photo')

    if not content and not photo:
        flash('No puedes publicar contenido vacío.', 'error')
        return redirect(url_for('dashboard'))

    photo_filename = None
    if photo and photo.filename != '':
        photo_filename = f"{user}_{photo.filename}"
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

    posts.append({'content': content, 'photo': photo_filename, 'user': user})
    flash('Publicación realizada con éxito!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Se ha cerrado sesión correctamente.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Toma el puerto de las variables de entorno de Render
app.run(host="0.0.0.0", port=port)  # Configura Flask para escuchar en todas las interfaces

