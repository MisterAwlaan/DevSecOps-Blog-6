from flask import Flask, render_template

app = Flask(__name__)

# Route pour la page d'accueil
@app.route('/')
def home():
    # Flask va chercher automatiquement dans le dossier 'templates'
    return render_template('accueil.html')

if __name__ == '__main__':
    # Le mode debug permet de voir les erreurs et de redémarrer 
    # automatiquement le serveur quand tu modifies le code.
    app.run(debug=True)