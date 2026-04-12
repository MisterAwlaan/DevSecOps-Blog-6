import pytest
from app import app, db, User, recettes, Comment
from werkzeug.security import generate_password_hash


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.drop_all()
        db.create_all()

        # Créer un utilisateur de test
        user = User(
            username='testuser',
            password=generate_password_hash('testpass')
        )
        db.session.add(user)
        db.session.commit()

        # Créer une recette de test
        recette = recettes(
            titre='Recette Test',
            description='Une description',
            difficulte='Facile',
            temps_preparation=10,
            temps_cuisson=5,
            ingredients='oeuf, farine',
            instructions='Mélanger; Cuire',
            statut='public',
            auteur_id=user.id
        )
        db.session.add(recette)
        db.session.commit()

    with app.test_client() as client:
        yield client


def login(client):
    return client.post('/connexion', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)


# --- Tests ---

def test_page_recette_accessible(client):
    """La page recette est accessible sans être connecté"""
    response = client.get('/recettes/1')
    assert response.status_code == 200


def test_commenter_sans_connexion(client):
    """Un utilisateur non connecté est redirigé vers la page de connexion"""
    response = client.post('/recettes/1/commenter', data={
        'contenu': 'Super recette !'
    }, follow_redirects=True)
    assert 'connexion' in response.data.decode('utf-8').lower()


def test_commenter_connecte(client):
    """Un utilisateur connecté peut poster un commentaire"""
    login(client)
    response = client.post('/recettes/1/commenter', data={
        'contenu': 'Délicieux !'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Délicieux' in response.data.decode('utf-8')


def test_commentaire_vide_refuse(client):
    """Un commentaire vide est refusé et ne s'enregistre pas en BDD"""
    login(client)
    client.post('/recettes/1/commenter', data={
        'contenu': '   '
    }, follow_redirects=True)
    with app.app_context():
        total = Comment.query.count()
        assert total == 0


def test_xss_commentaire(client):
    """Un commentaire avec du HTML est échappé (protection XSS)"""
    login(client)
    payload = '<script>alert("xss")</script>'
    response = client.post('/recettes/1/commenter', data={
        'contenu': payload
    }, follow_redirects=True)
    assert '<script>' not in response.data.decode('utf-8')