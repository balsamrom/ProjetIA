# Installation des Dépendances IA

Pour activer la fonctionnalité d'analyse d'images avec votre modèle IA entraîné (`my_model.h5`), vous devez installer les dépendances suivantes :

## 🚀 Installation Rapide

```bash
# Activer l'environnement virtuel
.\venv_new\Scripts\activate

# Installer les dépendances IA
pip install tensorflow numpy pillow

# Redémarrer le serveur
python manage.py runserver
```

## 📋 Dépendances Requises

- **TensorFlow** : Framework d'apprentissage automatique pour charger votre modèle
- **NumPy** : Bibliothèque de calcul numérique
- **Pillow** : Traitement d'images pour Django ImageField

## 🔧 Vérification de l'Installation

Après installation, testez que tout fonctionne :

```bash
python manage.py check
```

Vous devriez voir : `System check identified no issues (0 silenced).`

## 🤖 Utilisation du Scanner IA

Une fois les dépendances installées :

1. **Accédez à la section Multimédia** : `http://127.0.0.1:8000/multimedia`
2. **Ajoutez un avis avec une image**
3. **Cliquez sur "Scanner l'image"** pour analyser avec votre modèle IA
4. **Utilisez la page d'analyse directe** : `http://127.0.0.1:8000/analyse/`

## 📊 Classes Détectées par votre Modèle

Votre modèle `my_model.h5` peut détecter :
- **Buildings** (Bâtiments)
- **Forest** (Forêt) 
- **Glacier** (Glacier)
- **Mountain** (Montagne)
- **Sea** (Mer)
- **Street** (Rue)

## 🛠️ Dépannage

Si vous rencontrez des erreurs :

1. **Vérifiez que votre modèle `my_model.h5` est dans** : `voguevue/multimedia/karima_model/`
2. **Vérifiez les permissions du fichier**
3. **Redémarrez le serveur après installation**

## 📝 Note

Le projet fonctionne sans les dépendances IA, mais la fonctionnalité de scanner d'images affichera un message d'erreur indiquant que le module IA n'est pas disponible.
