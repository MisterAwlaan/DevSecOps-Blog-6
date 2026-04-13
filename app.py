from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import logging
import random
import socket
import sys
from dotenv import load_dotenv
from PIL import Image
import socket
import sys
import platform

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration du logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Extensions et signatures MIME autorisées ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_PIL_FORMATS = {'PNG', 'JPEG', 'GIF', 'WEBP'}

def extension_autorisee(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def type_mime_autorise(filepath):
    try:
        with Image.open(filepath) as img:
            return img.format in ALLOWED_PIL_FORMATS
    except Exception:
        return False

def sauvegarder_image(file, dossier, prefixe):
    if not file or file.filename == '':
        return None

    filename = secure_filename(file.filename)

    if not extension_autorisee(filename):
        flash("Format de fichier non autorisé. Seuls PNG, JPG, GIF et WEBP sont acceptés.", "danger")
        return None

    unique_filename = f"{prefixe}_{filename}"
    filepath = os.path.join(dossier, unique_filename)
    file.save(filepath)

    if not type_mime_autorise(filepath):
        os.remove(filepath)  
        flash("Le fichier uploadé n'est pas une image valide.", "danger")
        return None

    return unique_filename


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_key_fallback')

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(basedir, 'static', 'img')
PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')
app.config['PROFILE_FOLDER'] = PROFILE_FOLDER
os.makedirs(PROFILE_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# --- Modèles ---
class recettes(db.Model):
    recette_id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    difficulte = db.Column(db.String(20), nullable=False)
    temps_preparation = db.Column(db.Integer, nullable=False)
    temps_cuisson = db.Column(db.Integer, nullable=True)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    statut = db.Column(db.String(20), nullable=False, default='public')
    auteur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(120), nullable=False, default='default_user.png')
    recettes = db.relationship('recettes', backref='auteur', lazy=True)
    commentaires = db.relationship('Comment', back_populates='auteur', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recette_id = db.Column(db.Integer, db.ForeignKey('recettes.recette_id'), nullable=False)
    auteur = db.relationship('User', back_populates='commentaires')

with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
def health_check():
    # 1. Ajout d'un log à chaque appel avec l'IP
    logger.info(f"Endpoint /health appelé à {datetime.now().isoformat()} par {request.remote_addr}")

    try:
        # À terme : Vérification de la connexion BDD (ex: faire une requête simple)
        # db.session.execute('SELECT 1') 
        
        # 2 & 3. Code HTTP 200 et retour JSON obligatoire
        return jsonify({
            "status": "UP",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        # 4. Gérer les erreurs 500
        logger.error(f"Erreur critique healthcheck (500) : {str(e)}")
        return jsonify({
            "status": "DOWN",
            "detail": "Internal Server Error"
        }), 500

@app.route('/info', methods=['GET'])
def info():
    logger.info(f"Endpoint /info appelé à {datetime.now().isoformat()} par {request.remote_addr}")

    mode = os.getenv('FLASK_ENV', os.getenv('APP_MODE', 'dev'))

    return jsonify({
        "app": os.getenv('APP_NAME', 'flask-recettes'),
        "version": os.getenv('APP_VERSION', '1.0'),
        "mode": mode,
        "config": {
            "port": int(os.getenv('FLASK_RUN_PORT', 5000)),
            "host": os.getenv('FLASK_RUN_HOST', '127.0.0.1'),
            "debug": os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
            "database": app.config['SQLALCHEMY_DATABASE_URI']
        },
        "runtime": {
            "python_version": sys.version,
            "platform": platform.system(),
            "hostname": socket.gethostname()
        },
        "timestamp": datetime.now().isoformat()
    }), 200

# --- Routes ---
@app.route('/')
def home():
    recettes_publiques = recettes.query.filter_by(statut='public').all()
    return render_template('accueil.html', recettes=recettes_publiques)

@app.route('/recettes/<int:recette_id>')
def recettes_page(recette_id):
    recette = recettes.query.get_or_404(recette_id)
    if recette.statut == 'prive' and session.get('user_id') != recette.auteur_id:
        flash("Cette recette est privée.", "danger")
        return redirect(url_for('home'))
    commentaires = Comment.query.filter_by(recette_id=recette_id).all()
    return render_template('recettes.html', recette=recette, commentaires=commentaires)

@app.route('/ajouter_recette', methods=['GET', 'POST'])
def ajouter_recette():
    if 'user_id' not in session:
        flash("Tu dois être connecté pour publier une recette.", "warning")
        return redirect(url_for('connexion'))

    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        difficulte = request.form.get('difficulte')
        temps_preparation = request.form.get('temps_preparation')
        temps_cuisson = request.form.get('temps_cuisson')
        ingredients = request.form.get('ingredients')
        instructions = request.form.get('instructions')
        statut = request.form.get('statut')

        image_file = 'default.jpg'
        if 'image' in request.files:
            fichier_sauve = sauvegarder_image(
                request.files['image'],
                UPLOAD_FOLDER,
                f"user{session['user_id']}"
            )
            if fichier_sauve is None and request.files['image'].filename != '':
                return render_template('ajouter_post.html')
            if fichier_sauve:
                image_file = fichier_sauve

        nouvelle_recette = recettes(
            titre=titre, description=description, image_file=image_file,
            difficulte=difficulte, temps_preparation=temps_preparation,
            temps_cuisson=temps_cuisson, ingredients=ingredients,
            instructions=instructions, statut=statut, auteur_id=session['user_id']
        )
        db.session.add(nouvelle_recette)
        db.session.commit()
        flash("Ta recette a été ajoutée avec succès ! 🍲", "success")
        return redirect(url_for('home'))

    return render_template('ajouter_post.html')

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash("Ce nom d'utilisateur est déjà pris !", "danger")
            return redirect(url_for('inscription'))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Inscription réussie ! Connectez-vous.", "success")
        return redirect(url_for('connexion'))
    return render_template('creation_de_compte.html')

@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('profil'))
        else:
            flash("Identifiants incorrects.", "danger")
    return render_template('connexion.html')

@app.route('/modifier_recette/<int:recette_id>', methods=['GET', 'POST'])
def modifier_recette(recette_id):
    if 'user_id' not in session:
        flash("Tu dois être connecté pour modifier une recette.", "warning")
        return redirect(url_for('connexion'))

    recette = recettes.query.get_or_404(recette_id)
    if recette.auteur_id != session['user_id']:
        flash("Tu ne peux modifier que tes propres recettes !", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        recette.titre = request.form.get('titre')
        recette.description = request.form.get('description')
        recette.difficulte = request.form.get('difficulte')
        recette.temps_preparation = request.form.get('temps_preparation')
        recette.temps_cuisson = request.form.get('temps_cuisson')
        recette.ingredients = request.form.get('ingredients')
        recette.instructions = request.form.get('instructions')
        recette.statut = request.form.get('statut')

        if 'image' in request.files:
            fichier_sauve = sauvegarder_image(
                request.files['image'],
                UPLOAD_FOLDER,
                f"user{session['user_id']}"
            )
            if fichier_sauve is None and request.files['image'].filename != '':
                return render_template('modifier_post.html', recette=recette)
            if fichier_sauve:
                recette.image_file = fichier_sauve

        db.session.commit()
        flash("Ta recette a été modifiée avec succès ! ✨", "success")
        return redirect(url_for('recettes_page', recette_id=recette.recette_id))

    return render_template('modifier_post.html', recette=recette)

@app.route('/supprimer_recette/<int:recette_id>', methods=['POST'])
def supprimer_recette(recette_id):
    if 'user_id' not in session:
        flash("Tu dois être connecté pour faire cela.", "warning")
        return redirect(url_for('connexion'))

    recette = recettes.query.get_or_404(recette_id)
    if recette.auteur_id != session['user_id']:
        flash("Tu ne peux supprimer que tes propres recettes !", "danger")
        return redirect(url_for('home'))

    db.session.delete(recette)
    db.session.commit()
    flash("Ta recette a été supprimée définitivement 🗑️.", "success")
    return redirect(url_for('profil'))

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('connexion'))

    if request.method == 'POST':
        if 'new_password' in request.form:
            new_password = request.form.get('new_password')
            if new_password:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash("Mot de passe mis à jour avec succès !", "success")

        if 'profile_pic' in request.files:
            fichier_sauve = sauvegarder_image(
                request.files['profile_pic'],
                app.config['PROFILE_FOLDER'],
                f"user_{user.id}"
            )
            if fichier_sauve:
                user.profile_pic = fichier_sauve
                db.session.commit()
                flash("Photo de profil mise à jour !", "success")

        return redirect(url_for('profil'))

    mes_recettes = recettes.query.filter_by(auteur_id=user.id).all()
    return render_template('profil.html', user=user, mes_recettes=mes_recettes)

@app.route('/recettes/<int:recette_id>/commenter', methods=['POST'])
def commenter(recette_id):
    if 'user_id' not in session:
        flash("Tu dois être connecté pour commenter.", "warning")
        return redirect(url_for('recettes_page', recette_id=recette_id))

    contenu = request.form.get('contenu', '').strip()
    if not contenu:
        flash("Le commentaire ne peut pas être vide.", "danger")
        return redirect(url_for('recettes_page', recette_id=recette_id))

    recette = recettes.query.get_or_404(recette_id)

    comment = Comment(
        contenu=contenu,
        auteur_id=session['user_id'],
        recette_id=recette.recette_id
    )
    db.session.add(comment)
    db.session.commit()
    flash("Commentaire ajouté !", "success")
    return redirect(url_for('recettes_page', recette_id=recette_id))

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect(url_for('home'))


# --- Feature 1 ---
@app.route('/health')
def health():
    logger.info("GET /health - vérification de l'état de l'application")
    return jsonify({
        "status": "ok",
        "message": "L'application fonctionne correctement"
    }), 200


# --- Feature 2 ---
@app.route('/info')
def info():
    logger.info("GET /info - consultation de la configuration")
    return jsonify({
        "app": "mon-api",
        "version": "1.0",
        "mode": os.getenv("APP_MODE", "dev"),
        "port": int(os.getenv("PORT", 5000)),
        "python_version": sys.version,
        "hostname": socket.gethostname(),
        "debug": os.getenv("FLASK_DEBUG", "false")
    }), 200


# --- Feature 3 ---
@app.route('/random-fail')
def random_fail():
    try:
        # Réussit 2 fois sur 3, échoue 1 fois sur 3
        if random.randint(1, 3) == 1:
            raise ValueError("Simulation d'une erreur aléatoire en production")

        logger.info("GET /random-fail - succès")
        return jsonify({"status": "ok", "message": "Tout s'est bien passé !"}), 200

    except Exception as e:
        logger.error(f"GET /random-fail - ERREUR : {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Une erreur est survenue (simulée)",
            "detail": str(e)
        }), 500


# --- Feature 4 ---
@app.route('/logs-demo')
def logs_demo():
    logger.info("GET /logs-demo - démonstration des niveaux de logs")

    logger.info("INFO  [200] : Requête reçue et traitée avec succès")
    logger.warning("WARNING [400] : Paramètre manquant ou valeur suspecte détectée")
    logger.error("ERROR   [500] : Simulation d'une erreur critique serveur")

    return jsonify({
        "status": "ok",
        "logs_generes": [
            {"niveau": "INFO",    "code_http_associé": 200, "message": "Requête traitée avec succès"},
            {"niveau": "WARNING", "code_http_associé": 400, "message": "Paramètre suspect détecté"},
            {"niveau": "ERROR",   "code_http_associé": 500, "message": "Erreur critique simulée"}
        ]
    }), 200


if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    host_ip = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    app.run(host=host_ip, port=5000, debug=debug_mode)


MON_SUPER_SECRET_LOCAL = "root" 