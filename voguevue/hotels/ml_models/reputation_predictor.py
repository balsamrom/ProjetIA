import pickle
try:
    import joblib
except Exception:
    joblib = None
import pandas as pd
import numpy as np
import re
import os
from sklearn.pipeline import make_pipeline

class HotelReputationPredictor:
    def __init__(self, model_path=None):
        """
        Charge le modèle .pkl pour l'analyse des avis hôtel
        """
        self.model_loaded = False
        # Résoudre le chemin du modèle
        default_model_path = os.path.join(os.path.dirname(__file__), 'hotel_review_tfidf_logreg.pkl')
        # Autoriser un override via settings si disponible
        try:
            from django.conf import settings as _dj_settings
            settings_model_path = getattr(_dj_settings, 'HOTEL_REPUTATION_MODEL_PATH', None)
        except Exception:
            settings_model_path = None
        model_path = model_path or settings_model_path or default_model_path
        self.model_path = model_path
        print(f"Loading reputation model from: {self.model_path}")
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modèle introuvable: {model_path}")

            # Try pickle first, then joblib as fallback
            try:
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
            except Exception as pe:
                if joblib is not None:
                    try:
                        model_data = joblib.load(model_path)
                    except Exception as je:
                        raise RuntimeError(f"Echec chargement pickle ({pe}) et joblib ({je})")
                else:
                    raise

            # Accepter soit un dict, soit un pipeline direct
            if isinstance(model_data, dict):
                self.accuracy = model_data.get('accuracy')
                self.reputation_labels = model_data.get('classes')
                if 'pipeline' in model_data:
                    self.pipeline = model_data['pipeline']
                elif 'model' in model_data and 'vectorizer' in model_data:
                    self.pipeline = make_pipeline(model_data['vectorizer'], model_data['model'])
                    if self.reputation_labels is None:
                        try:
                            self.reputation_labels = list(model_data['model'].classes_)
                        except Exception:
                            self.reputation_labels = []
                else:
                    raise ValueError("PKL dict must contain 'pipeline' or ('model' and 'vectorizer')")
            else:
                # Modèle/pipeline directement sérialisé
                self.pipeline = model_data
                self.accuracy = None
                # Essayer de récupérer les classes du modèle interne
                try:
                    self.reputation_labels = list(self.pipeline.classes_)
                except Exception:
                    self.reputation_labels = []
            self.model_loaded = True

            if self.accuracy is not None:
                print(f"Model loaded (accuracy: {self.accuracy:.2%})")
            else:
                print("Reputation model loaded")

        except Exception as e:
            # Aucun mode démo: le modèle est requis
            self.pipeline = None
            self.model_loaded = False
            self.last_error = str(e)
            print(f"Error loading reputation model: {e}")

    def preprocess_text(self, text):
        """
        Nettoyage léger: minuscules + espaces
        """
        if not isinstance(text, str):
            text = str(text)
        
        text = text.lower()
        # retirer retours de ligne/espaces multiples, garder tous alphabets (latin/non-latin)
        text = re.sub(r'[\r\n]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def predict_from_reviews(self, reviews_list):
        """
        Prédit la réputation à partir d'une liste d'avis
        Format d'entrée: liste de textes d'avis
        """
        if not reviews_list:
            return self._get_default_analysis()
        
        # Nettoyage des avis
        clean_reviews = []
        for review in reviews_list:
            if review and str(review).strip():
                cleaned = self.preprocess_text(review)
                if cleaned and len(cleaned) > 2:  # Éviter les textes trop courts
                    clean_reviews.append(cleaned)
        
        if not clean_reviews:
            return self._get_default_analysis()
        
        # Vérifier modèle
        if not self.model_loaded:
            return {
                'status': 'error',
                'message': 'Modèle non chargé',
                'overall_reputation': 'Non évalué',
                'confidence': 0,
                'total_reviews': len(clean_reviews)
            }
        
        try:
            # PRÉDICTION AVEC LE VRAI MODÈLE
            individual_predictions = self.pipeline.predict(clean_reviews)
            # Probabilités: fallback si predict_proba indisponible
            if hasattr(self.pipeline, 'predict_proba'):
                probabilities = self.pipeline.predict_proba(clean_reviews)
            else:
                # decision_function -> softmax pour approx des proba
                decision = getattr(self.pipeline, 'decision_function', None)
                if decision is None:
                    # Pas de scores, utiliser confiance neutre
                    probabilities = None
                else:
                    scores = decision(clean_reviews)
                    scores = np.atleast_2d(scores)
                    # Si binaire, shape (n,); convertir en (n,2)
                    if scores.ndim == 2 and scores.shape[1] == 1:
                        scores = np.hstack([-scores, scores])
                    # softmax
                    exp_scores = np.exp(scores - np.max(scores, axis=1, keepdims=True))
                    probabilities = exp_scores / (np.sum(exp_scores, axis=1, keepdims=True) + 1e-9)

            # Déterminer labels compatibles
            labels = None
            try:
                labels = list(getattr(self.pipeline, 'classes_', []))
            except Exception:
                labels = None
            if (labels is None or len(labels) == 0) and hasattr(self, 'reputation_labels') and self.reputation_labels:
                labels = list(self.reputation_labels)
            if probabilities is not None and (labels is None or len(labels) != probabilities.shape[1]):
                # Générer des labels génériques si mismatch
                labels = [f'class_{i}' for i in range(probabilities.shape[1])]

            # Confiance alignée Colab: proportion de la classe majoritaire (majority ratio)
            # On calcule d'abord la série des prédictions, puis la classe majoritaire et son ratio

            # Réputation globale (mode)
            pred_series = pd.Series(individual_predictions)
            value_counts = pred_series.value_counts()
            overall_reputation = value_counts.index[0]

            # Analyse détaillée
            breakdown = {}
            total_reviews = len(individual_predictions)
            for category in pd.unique(pred_series):
                count = int((pred_series == category).sum())
                percentage = round((count / total_reviews) * 100, 1) if total_reviews > 0 else 0
                breakdown[str(category)] = {'count': count, 'percentage': percentage}

            # Confiance finale = ratio de la classe majoritaire
            majority_count = int(value_counts.iloc[0]) if total_reviews > 0 else 0
            majority_ratio = (majority_count / total_reviews) if total_reviews > 0 else 0.0

            # Prédictions individuelles avec scores
            detailed_predictions = []
            for i, pred in enumerate(individual_predictions):
                if probabilities is not None:
                    prob_row = probabilities[i]
                    all_probs = {str(labels[j]): round(float(prob_row[j]) * 100, 1) for j in range(len(prob_row))}
                    pred_confidence = float(np.max(prob_row))
                else:
                    all_probs = {}
                    pred_confidence = confidence_scores[i]
                detailed_predictions.append({
                    'review_text': reviews_list[i] if i < len(reviews_list) else clean_reviews[i],
                    'prediction': str(pred),
                    'confidence': round(pred_confidence, 3),
                    'all_probabilities': all_probs
                })

            return {
                'status': 'success',
                'overall_reputation': str(overall_reputation),
                'confidence': round(majority_ratio, 3),
                'total_reviews_analyzed': total_reviews,
                'breakdown': breakdown,
                'individual_analyses': detailed_predictions,
                'model_accuracy': round(self.accuracy, 3) if self.accuracy is not None else None
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'overall_reputation': 'Erreur',
                'confidence': 0,
                'total_reviews': len(clean_reviews)
            }
    
    def _get_default_analysis(self):
        """Retourne une analyse par défaut"""
        return {
            'status': 'no_reviews',
            'overall_reputation': 'Non évalué',
            'confidence': 0,
            'total_reviews_analyzed': 0,
            'breakdown': {},
            'individual_analyses': []
        }

# Initialisation globale
reputation_predictor = HotelReputationPredictor()