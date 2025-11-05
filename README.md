# 🌍 Plateforme Touristique Intelligente

## 📋 Description

Application web intelligente combinant gestion événementielle/touristique et intelligence artificielle. Développée dans le cadre du projet académique 2025-2026, cette plateforme offre une expérience utilisateur enrichie par 6 modules IA distincts.

---

## 👥 Équipe de Développement

| Membre | Module Principal |
|--------|------------------|
| **Rima Dhrai** | Hôtels + Analyse de Réputation |
| **Rawen Labaoui** | Activités + Recommandation |
| **Balsam Romdhane** | Utilisateurs + Chatbot BiLSTM |
| **Karima Louhibi** | Contenu + Classification Images |
| **Amira Laffet** | Destinations + Recommandation RF |
| **Fadi Kaabi** | Événements + Génération IA |

---

## 🚀 Fonctionnalités Principales

### 🏨 Module Hôtels
- CRUD complet des hôtels, chambres et réservations
- **IA** : Analyse de réputation (LogisticRegression - 95.7% accuracy)
- Génération automatique de descriptions via API SerpAI
- Recherche avancée multi-critères

### 🎯 Module Activités
- Gestion des activités touristiques
- **IA** : Recommandation contextuelle (LightGBM + météo en temps réel)
- Intégration API OpenWeather
- Génération d'itinéraires personnalisés via API Groq

### 👤 Module Utilisateurs
- Authentification sécurisée
- **IA** : Chatbot voyageur (BiLSTM - 94% accuracy)
- **IA** : Reconnaissance faciale (DeepFace/ArcFace - 97% taux de reconnaissance)
- Classification d'intentions multi-domaines

### 🖼️ Module Contenu et Multimédia
- Gestion centralisée du contenu
- **IA** : Classification multi-labels d'images (CNN - 89% accuracy)
- Intégration API Clarifai pour reconnaissance avancée
- Support de 6 catégories de paysages

### 🗺️ Module Destinations
- CRUD des destinations touristiques
- **IA** : Recommandation intelligente (Random Forest - 82.86% accuracy)
- Enrichissement automatique via API Unsplash + Hugging Face
- Vectorisation TF-IDF (805 features)

### 🎭 Module Événements
- Gestion des événements culturels
- **IA** : Génération d'images (Qwen-Image via Hugging Face)
- **IA** : Prédiction de popularité (Random Forest - R²=0.748)
- Système de badges de tendance

---

## 🛠️ Stack Technique

### Backend & Base de Données
- **Framework** : Django 4.x
- **Base de données** : MySQL
- **Langage** : Python 3.8+

### Intelligence Artificielle
- **Deep Learning** : TensorFlow, Keras
- **ML Classique** : Scikit-learn, LightGBM
- **NLP** : Sentence Transformers, TF-IDF
- **Computer Vision** : OpenCV, DeepFace
- **APIs IA** : Hugging Face, Clarifai, Groq, SerpAI

### DevOps & Tests
- **CI/CD** : Jenkins
- **Tests** : Selenium
- **Qualité** : SonarQube
- **Versioning** : Git
- **Entraînement** : Google Colab

---

## 📦 Installation

### Prérequis
```bash
Python 3.8+
MySQL 8.0+
pip
virtualenv (recommandé)
```

### Étapes d'Installation

#### 1. Cloner le repository
```bash
git clone https://github.com/votre-repo/plateforme-touristique.git
cd plateforme-touristique
```

#### 2. Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

#### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

#### 4. Configurer la base de données
```bash
# Créer la base MySQL
mysql -u root -p
CREATE DATABASE plateforme_touristique CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# Appliquer les migrations
python manage.py makemigrations
python manage.py migrate
```

#### 5. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos clés API
```

#### 6. Charger les modèles IA
```bash
# Placer les modèles dans le dossier models/
# - sentiment_model.pkl (Analyse réputation)
# - lightgbm_model.pkl (Recommandation activités)
# - bilstm_chatbot.h5 (Chatbot)
# - cnn_classifier.h5 (Classification images)
# - rf_destinations.pkl (Recommandation destinations)
# - rf_events.pkl (Prédiction événements)
```

#### 7. Lancer le serveur
```bash
python manage.py runserver
# Accéder à : http://localhost:8000
```

---

## 🔑 Configuration des APIs

Créer un fichier `.env` avec les clés suivantes :
```env
# Base de données
DB_NAME=plateforme_touristique
DB_USER=votre_user
DB_PASSWORD=votre_password
DB_HOST=localhost
DB_PORT=3306

# APIs IA
HUGGINGFACE_API_KEY=your_hf_key
CLARIFAI_API_KEY=your_clarifai_key
GROQ_API_KEY=your_groq_key
SERPAI_API_KEY=your_serpai_key
OPENWEATHER_API_KEY=your_weather_key

# Django
SECRET_KEY=your_secret_key
DEBUG=True
```

---

## 📊 Performances des Modèles IA

| Module | Modèle | Métrique | Score |
|--------|--------|----------|-------|
| Réputation Hôtels | LogisticRegression | Accuracy | 95.7% |
| Chatbot | BiLSTM | Accuracy | 94.0% |
| Reconnaissance Faciale | DeepFace/ArcFace | Taux reconnaissance | 97.0% |
| Classification Images | CNN | Accuracy | 89.0% |
| Recommandation Activités | LightGBM | Contextuel | - |
| Recommandation Destinations | Random Forest | Accuracy | 82.86% |
| Prédiction Événements | Random Forest | R² | 0.748 |

---

## 📁 Structure du Projet
```
plateforme-touristique/
├── apps/
│   ├── hotels/              # Module Hôtels
│   ├── activities/          # Module Activités
│   ├── users/               # Module Utilisateurs
│   ├── content/             # Module Contenu
│   ├── destinations/        # Module Destinations
│   └── events/              # Module Événements
├── models/                  # Modèles IA entraînés (.pkl, .h5)
├── static/                  # Fichiers statiques (CSS, JS, images)
├── templates/               # Templates Django
├── media/                   # Uploads utilisateurs
├── config/                  # Configuration Django
├── requirements.txt         # Dépendances Python
├── manage.py               # Script Django
└── README.md               # Ce fichier
```

---

## 🧪 Tests

### Lancer les tests unitaires
```bash
python manage.py test
```

### Tests Selenium (E2E)
```bash
python manage.py test tests.selenium_tests
```

### Analyse de qualité (SonarQube)
```bash
sonar-scanner
```

---

## 📖 Documentation

- **Rapport technique complet** : `docs/rapport_technique.pdf`
- **Documentation API** : `docs/api_documentation.md`
- **Guide utilisateur** : `docs/guide_utilisateur.pdf`

---

## 🤝 Contribution

Ce projet est académique. Pour toute suggestion :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

---

## 📄 License

Projet académique - ESPRIT 2025-2026
