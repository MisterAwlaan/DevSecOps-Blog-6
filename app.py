from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'cle_secrete_super_securisee_pour_le_dev'

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
    
    # --- NOUVEAUTÉS ---
    statut = db.Column(db.String(20), nullable=False, default='public') # 'public' ou 'prive'
    auteur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Lien avec l'auteur

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_pic = db.Column(db.String(120), nullable=False, default='default_user.png')
    recettes = db.relationship('recettes', backref='auteur', lazy=True)

with app.app_context():
    db.create_all()

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
        
    return render_template('recettes.html', recette=recette)

# --- NOUVELLE ROUTE : Ajouter une recette ---
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
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"user{session['user_id']}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
                image_file = unique_filename

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
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"user{session['user_id']}_{filename}"
                file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
                recette.image_file = unique_filename 
        db.session.commit()
        
        flash("Ta recette a été modifiée avec succès ! ✨", "success")
        return redirect(url_for('recettes_page', recette_id=recette.recette_id))
    return render_template('modifier_post.html', recette=recette)

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
            file = request.files['profile_pic']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"user_{user.id}_{filename}"
                file.save(os.path.join(app.config['PROFILE_FOLDER'], unique_filename))
                user.profile_pic = unique_filename
                db.session.commit()
                flash("Photo de profil mise à jour !", "success")
        return redirect(url_for('profil'))

    # On récupère aussi les recettes de l'utilisateur pour les afficher plus tard !
    mes_recettes = recettes.query.filter_by(auteur_id=user.id).all()
    return render_template('profil.html', user=user, mes_recettes=mes_recettes)

@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)