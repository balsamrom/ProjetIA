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
            MODEL_PATH = os.path.join(BASE_DIR, "best_classifier_model.h5")
            # Charger sans recompilation pour éviter les soucis d'optimiseur/version
            _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
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

        # Déterminer dynamiquement la taille d'entrée du modèle
        input_shape = getattr(model, 'input_shape', None)
        if input_shape is not None and len(input_shape) >= 3:
            # input_shape format typique: (None, H, W, C) pour channels_last
            # ou (None, C, H, W) pour channels_first
            if input_shape[-1] in (1, 3):
                target_h, target_w = input_shape[1], input_shape[2]
            else:
                # channels_first
                target_h, target_w = input_shape[-2], input_shape[-3]
        else:
            target_h, target_w = 150, 150

        # Prétraitement
        img = image.load_img(img_path, target_size=(target_h, target_w))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # Prédiction
        pred = model.predict(img_array, verbose=0)[0]

        # Appliquer un seuil pour multi-label
        threshold = 0.4
        predicted_labels = [CLASSES[i] for i in range(min(len(CLASSES), len(pred))) if pred[i] > threshold]

        # Si le modèle est softmax (somme proche de 1) et qu'aucune proba ne dépasse le seuil,
        # on sélectionne la meilleure classe unique.
        if not predicted_labels:
            try:
                if abs(float(np.sum(pred)) - 1.0) < 1e-3:
                    top_idx = int(np.argmax(pred))
                    if top_idx < len(CLASSES):
                        predicted_labels = [CLASSES[top_idx]]
            except Exception:
                pass

        # Si aucune classe ne dépasse le seuil
        if not predicted_labels:
            predicted_labels = ["Aucune classe reconnue"]

        # Dictionnaire résultat
        result = {CLASSES[i]: float(pred[i]) for i in range(min(len(CLASSES), len(pred)))}

        return {
            "predicted_labels": predicted_labels,
            "probabilities": result,
            "success": True
        }

    except Exception as e:
        return {"error": str(e), "success": False}
