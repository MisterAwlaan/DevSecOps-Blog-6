from flask import Flask, render_template
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de l'objet SQLAlchemy
db = SQLAlchemy(app)

# --- Modèles ---

class recettes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')

    def __repr__(self):
        return f'<recette {self.titre}>'

# Route pour la page d'accueil
@app.route('/')
def home():

    all_recettes= recettes.query.all()
    # Flask va chercher automatiquement dans le dossier 'templates'
    return render_template('accueil.html', recettes=all_recettes)

if __name__ == '__main__':
    # Le mode debug permet de voir les erreurs et de redémarrer 
    # automatiquement le serveur quand tu modifies le code.
    app.run(debug=True)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de l'objet SQLAlchemy
db = SQLAlchemy(app)

# --- Modèles ---

class recettes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')

    def __repr__(self):
        return f'<recette {self.titre}>'