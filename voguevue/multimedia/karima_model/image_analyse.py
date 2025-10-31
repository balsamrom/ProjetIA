import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import os

# 🔹 Les classes du modèle
CLASSES = ['buildings', 'forest', 'glacier', 'mountain', 'sea', 'street']

# Variable globale pour le modèle (chargé de manière paresseuse)
_model = None

def get_model():
    """Charge le modèle de manière paresseuse"""
    global _model
    if _model is None:
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            MODEL_PATH = os.path.join(BASE_DIR, "my_model.h5")
            _model = tf.keras.models.load_model(MODEL_PATH)
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            _model = None
    return _model

# 🔹 Fonction d'analyse d'une image
def analyse_image(img_path):
    """
    Prend le chemin d'une image, la prétraite et renvoie les classes prédites.
    """
    try:
        # Charger le modèle
        model = get_model()
        if model is None:
            return {"error": "Modèle IA non disponible"}

        # Prétraitement
        img = image.load_img(img_path, target_size=(150, 150))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Prédiction
        pred = model.predict(img_array, verbose=0)[0]

        # Appliquer un seuil pour multi-label
        threshold = 0.4
        predicted_labels = [CLASSES[i] for i in range(len(CLASSES)) if pred[i] > threshold]

        # Si aucune classe ne dépasse le seuil
        if not predicted_labels:
            predicted_labels = ["Aucune classe reconnue"]

        # Dictionnaire résultat
        result = {CLASSES[i]: float(pred[i]) for i in range(len(CLASSES))}

        return {
            "predicted_labels": predicted_labels,
            "probabilities": result,
            "success": True
        }

    except Exception as e:
        return {"error": str(e), "success": False}
