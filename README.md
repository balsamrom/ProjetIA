# VogueVue - Projet Django

Un projet Django de gestion d'avis de voyage avec analyse d'images par intelligence artificielle.

## 🚀 Installation et Exécution

### Prérequis
- Python 3.8+
- pip

### Installation

1. **Cloner le projet**
   ```bash
   git clone <votre-repo>
   cd ProjetIA
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   ```

3. **Activer l'environnement virtuel**
   
   **Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

4. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

5. **Exécuter les migrations**
   ```bash
   python manage.py migrate
   ```

6. **Créer un superutilisateur (optionnel)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Démarrer le serveur**
   ```bash
   python manage.py runserver
   ```

8. **Accéder à l'application**
   Ouvrez votre navigateur et allez à: `http://127.0.0.1:8000`

## 📁 Structure du Projet

```
ProjetIA/
├── hackathon/           # Configuration Django
├── voguevue/           # Application principale
│   ├── multimedia/     # Module d'analyse d'images IA
│   ├── models.py       # Modèles de données
│   ├── views.py        # Vues de l'application
│   └── urls.py         # URLs de l'application
├── templates/          # Templates HTML
├── static/            # Fichiers statiques (CSS, JS, images)
├── media/             # Fichiers uploadés par les utilisateurs
└── db.sqlite3         # Base de données SQLite
```

## 🎯 Fonctionnalités

- **Page d'accueil** : Interface principale du site
- **Authentification** : Inscription et connexion des utilisateurs
- **Gestion d'avis** : Création, modification et suppression d'avis de voyage
- **Analyse d'images IA** : Classification automatique des images de voyage
- **Multimédia** : Upload et gestion d'images
- **Blog** : Section blog pour les articles de voyage

## 🔧 Configuration

### Base de données
Le projet utilise SQLite par défaut. Pour utiliser MySQL, modifiez `hackathon/settings.py` :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'voguevue_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### Variables d'environnement
- `DEBUG=True` : Mode développement
- `SECRET_KEY` : Clé secrète Django

## 🤖 Intelligence Artificielle

Le projet inclut un module d'analyse d'images utilisant votre modèle IA entraîné (`my_model.h5`) pour classifier automatiquement les images de voyage selon les catégories :
- **Buildings** (Bâtiments)
- **Forest** (Forêt)
- **Glacier** (Glacier)
- **Mountain** (Montagne)
- **Sea** (Mer)
- **Street** (Rue)

### 🔧 Activation du Scanner IA

Pour activer la fonctionnalité d'analyse d'images, suivez les instructions dans `INSTALL_AI.md` :

```bash
# Installer les dépendances IA
pip install tensorflow numpy pillow
```

### 📱 Fonctionnalités IA

- **Scanner d'images** : Analyse automatique des images uploadées
- **Classification multi-label** : Détection de plusieurs classes simultanément
- **Probabilités détaillées** : Affichage des scores de confiance
- **Interface intuitive** : Résultats visuels avec barres de progression

## 📝 Utilisation

1. **Inscription** : Créez un compte utilisateur
2. **Connexion** : Connectez-vous avec vos identifiants
3. **Ajouter un avis** : Uploadez une image et ajoutez un commentaire
4. **Scanner IA** : Cliquez sur "Scanner l'image" pour analyser avec votre modèle IA
5. **Analyse directe** : Utilisez `/analyse/` pour analyser des images directement
6. **Gestion** : Modifiez ou supprimez vos avis

## 🛠️ Développement

### Commandes utiles

```bash
# Vérifier la configuration
python manage.py check

# Créer de nouvelles migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer les tests
python manage.py test
```

### Structure des modèles

- **User** : Utilisateurs Django standard
- **Contact** : Messages de contact
- **Avis** : Avis de voyage avec images
- **register_table** : Informations supplémentaires des utilisateurs

## 📞 Support

Pour toute question ou problème, n'hésitez pas à ouvrir une issue sur le repository.

## 📄 Licence

Ce projet est sous licence MIT.