# Tracao Backend - API de Traçabilité

Ce projet est le backend de la plateforme **Tracao**, une application dédiée à la traçabilité des filières cacao et café. Il est construit avec **Django** et **Django REST Framework**.

## 🚀 Technologies utilisées

- **Langage** : Python 3.x
- **Framework** : Django 5.x / 6.x
- **API** : Django REST Framework (DRF)
- **Authentification** : JWT (SimpleJWT)
- **Base de données** : PostgreSQL (configuré via `DATABASE_URL`)
- **Documentation** : drf-spectacular (Swagger/OpenAPI)

## 🛠️ Installation et Configuration

### 1. Cloner le dépôt
```bash
git clone <url-du-repo>
cd app2/backend
```

### 2. Créer l'environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/macOS
# ou
venv\Scripts\activate     # Sur Windows
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration des variables d'environnement
Copiez le fichier d'exemple et remplissez-le avec vos accès :
```bash
cp mysite/.env.example mysite/.env
```
Éditez le fichier `mysite/.env` pour configurer votre `DATABASE_URL` et votre `SECRET_KEY`.

### 5. Appliquer les migrations
```bash
python mysite/manage.py migrate
```

### 6. Créer un super-utilisateur (Admin)
```bash
python mysite/manage.py createsuperuser
```

## 🏃 Lancement du serveur
```bash
python mysite/manage.py runserver
```
Le serveur sera accessible sur `http://127.0.0.1:8000`.

## 📖 Documentation de l'API
Une fois le serveur lancé, vous pouvez accéder à la documentation interactive :
- **Swagger UI** : `http://127.0.0.1:8000/api/schema/swagger-ui/`
- **Redoc** : `http://127.0.0.1:8000/api/schema/redoc/`

## 📂 Structure du projet
- `mysite/` : Configuration principale du projet Django.
- `api/` : Application principale contenant les modèles, les sérialiseurs et les vues de l'API.
- `requirements.txt` : Liste des dépendances Python.
- `.env` : Variables d'environnement (non inclut dans Git).
- `.gitignore` : Fichiers et dossiers à exclure du versionnage.
