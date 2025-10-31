import pickle
import pandas as pd
import numpy as np
import re
import os

class HotelReputationPredictor:
    def __init__(self, model_path='hotel_review_tfidf_logreg.pkl'):
        """
        Charge le modèle .pkl pour l'analyse des avis hôtel
        """
        self.model_loaded = False
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modèle {model_path} introuvable")
            
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.pipeline = model_data['pipeline']
            self.accuracy = model_data['accuracy']
            self.reputation_labels = model_data['classes']
            self.model_loaded = True
            
            print(f"✅ Modèle de réputation chargé (précision: {self.accuracy:.2%})")
            
        except Exception as e:
            print(f"❌ Erreur chargement modèle: {e}")
            self.pipeline = None
            self.model_loaded = False
    
    def preprocess_text(self, text):
        """
        Nettoyage identique à l'entraînement Colab
        """
        if not isinstance(text, str):
            text = str(text)
        
        text = text.lower()
        text = re.sub(r'[^a-zàâäéèêëïîôöùûüÿçñ\s]', '', text)
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
            probabilities = self.pipeline.predict_proba(clean_reviews)
            
            # Calculs
            confidence_scores = [np.max(probs) for probs in probabilities]
            avg_confidence = np.mean(confidence_scores)
            
            # Réputation globale (mode)
            pred_series = pd.Series(individual_predictions)
            overall_reputation = pred_series.mode()[0]
            if len(pred_series.mode()) > 1:
                # En cas d'égalité, prendre la meilleure réputation
                overall_reputation = pred_series.value_counts().index[0]
            
            # Analyse détaillée
            breakdown = {}
            total_reviews = len(individual_predictions)
            
            for category in self.reputation_labels:
                count = (pred_series == category).sum()
                percentage = round((count / total_reviews) * 100, 1) if total_reviews > 0 else 0
                breakdown[category] = {
                    'count': int(count),
                    'percentage': percentage
                }
            
            # Prédictions individuelles avec scores
            detailed_predictions = []
            for i, (pred, prob) in enumerate(zip(individual_predictions, probabilities)):
                pred_confidence = np.max(prob)
                pred_index = np.argmax(prob)
                detailed_predictions.append({
                    'review_text': reviews_list[i] if i < len(reviews_list) else clean_reviews[i],
                    'prediction': pred,
                    'confidence': round(pred_confidence, 3),
                    'all_probabilities': {
                        self.reputation_labels[j]: round(prob[j] * 100, 1) 
                        for j in range(len(prob))
                    }
                })
            
            return {
                'status': 'success',
                'overall_reputation': overall_reputation,
                'confidence': round(avg_confidence, 3),
                'total_reviews_analyzed': total_reviews,
                'breakdown': breakdown,
                'individual_analyses': detailed_predictions,
                'model_accuracy': round(self.accuracy, 3)
            }
            
        except Exception as e:
            print(f"❌ Erreur prédiction: {e}")
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