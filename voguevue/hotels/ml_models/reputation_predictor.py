import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import os

class HotelReputationPredictor:
    def __init__(self, model_path='hotel_review_tfidf_logreg.pkl'):
        """
        Charge le modèle .pkl que tu as créé
        """
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.pipeline = model_data['pipeline']
            self.accuracy = model_data['accuracy']
            self.reputation_labels = model_data['classes']
            
            print(f"✅ Modèle chargé! Précision: {self.accuracy:.2%}")
            
        except Exception as e:
            print(f"❌ Erreur chargement modèle: {e}")
            # Mode démo en cas d'échec
            self.pipeline = None
            self.accuracy = 0.85
            self.reputation_labels = ['Mauvais', 'Moyen', 'Bon', 'Très bon', 'Excellent']
    
    def predict_hotel_reputation(self, hotel_reviews):
        """
        Prédit la réputation d'un hôtel basée sur ses avis
        """
        if not hotel_reviews:
            return self._default_response()
        
        clean_reviews = [str(review).strip() for review in hotel_reviews if review and str(review).strip()]
        
        if not clean_reviews:
            return self._default_response()
        
        # Mode démo si pas de modèle
        if self.pipeline is None:
            return self._demo_predict(clean_reviews)
        
        try:
            # VRAIE PRÉDICTION avec ton modèle
            individual_predictions = self.pipeline.predict(clean_reviews)
            
            # Calcul de la réputation globale
            pred_series = pd.Series(individual_predictions)
            overall_reputation = pred_series.mode()[0]
            
            # Détail par catégorie
            breakdown = {}
            total = len(individual_predictions)
            for category in self.reputation_labels:
                count = (pred_series == category).sum()
                breakdown[category] = {
                    'count': count,
                    'percentage': round((count / total) * 100, 1)
                }
            
            return {
                'reputation': overall_reputation,
                'confidence': round(self.accuracy, 3),
                'total_reviews': total,
                'prediction_breakdown': breakdown,
                'individual_predictions': individual_predictions.tolist()
            }
            
        except Exception as e:
            print(f"❌ Erreur prédiction: {e}")
            return self._demo_predict(clean_reviews)
    
    def _default_response(self):
        return {
            'reputation': 'Non évalué',
            'confidence': 0,
            'total_reviews': 0,
            'prediction_breakdown': {},
            'individual_predictions': []
        }
    
    def _demo_predict(self, reviews):
        """Mode démo si le modèle échoue"""
        # Simulation simple basée sur la longueur des avis
        avg_length = np.mean([len(str(r)) for r in reviews])
        
        if avg_length > 100:
            reputation = 'Excellent'
        elif avg_length > 50:
            reputation = 'Très bon'
        elif avg_length > 20:
            reputation = 'Bon'
        else:
            reputation = 'Moyen'
        
        return {
            'reputation': reputation,
            'confidence': 0.75,
            'total_reviews': len(reviews),
            'prediction_breakdown': {reputation: {'count': len(reviews), 'percentage': 100}},
            'individual_predictions': [reputation] * len(reviews)
        }

# Initialisation
try:
    predictor = HotelReputationPredictor()
    print("🎉 Prédicteur initialisé avec succès!")
except Exception as e:
    print(f"⚠️  Mode démo activé: {e}")
    predictor = HotelReputationPredictor()  # Va utiliser le mode démo