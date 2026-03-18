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
    recette_id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    difficulte = db.Column(db.String(20), nullable=False)    # Ex: "Facile", "Moyen", "Difficile"
    temps_preparation = db.Column(db.Integer, nullable=False) 
    temps_cuisson = db.Column(db.Integer, nullable=True)     
    ingredients = db.Column(db.Text, nullable=False)          
    instructions = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<recette {self.titre}>'

# Route pour la page d'accueil
@app.route('/')
def home():

    all_recettes= recettes.query.all()
    # Flask va chercher automatiquement dans le dossier 'templates'
    return render_template('accueil.html', recettes=all_recettes)

@app.route('/recettes/<int:recette_id>')
def recettes_page(recette_id):
    recette=recettes.query.get_or_404(recette_id)
    return render_template('recettes.html', recette=recette)


if __name__ == '__main__':
    # Le mode debug permet de voir les erreurs et de redémarrer 
    # automatiquement le serveur quand tu modifies le code.
    app.run(host='0.0.0.0', port=5000, debug=True)

