import pandas as pd
import numpy as np
import pickle
import os
from django.conf import settings

class DestinationRecommender:
    def __init__(self):
        self.model_loaded = False
        self.load_model()
    
    def load_model(self):
        """Charge le modèle depuis les fichiers sauvegardés"""
        try:
            model_path = os.path.join(settings.BASE_DIR, 'model')
            print(f"📁 Chargement du modèle depuis: {model_path}")
            
            # Vérifier si les fichiers existent
            required_files = [
                'destinations_final.csv',
                'tfidf_vectorizer.pkl', 
                'global_similarity.pkl',
                'label_encoders.pkl'
            ]
            
            for file in required_files:
                file_path = os.path.join(model_path, file)
                if not os.path.exists(file_path):
                    print(f"❌ Fichier manquant: {file}")
                    return
            
            # Charger les données
            self.df = pd.read_csv(os.path.join(model_path, 'destinations_final.csv'))
            print(f"✅ Dataset chargé: {self.df.shape}")
            
            # Charger le modèle TF-IDF
            with open(os.path.join(model_path, 'tfidf_vectorizer.pkl'), 'rb') as f:
                self.tfidf = pickle.load(f)
            print("✅ TF-IDF chargé")
            
            # Charger la matrice de similarité
            with open(os.path.join(model_path, 'global_similarity.pkl'), 'rb') as f:
                self.global_sim = pickle.load(f)
            print("✅ Matrice de similarité chargée")
            
            # Charger les encodeurs
            with open(os.path.join(model_path, 'label_encoders.pkl'), 'rb') as f:
                self.encoders = pickle.load(f)
            print("✅ Encodeurs chargés")
            
            self.model_loaded = True
            print("🎉 Modèle de recommandation chargé avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            import traceback
            traceback.print_exc()
            self.model_loaded = False
    
    def recommend(self, destination_name, n_recommendations=5):
        """
        Recommande des destinations similaires
        """
        if not self.model_loaded:
            return {"error": "Modèle non chargé"}
        
        destination_name = destination_name.strip().lower()
        print(f"🔍 Recherche de: {destination_name}")
        
        # Chercher la destination
        destination_match = self.df[self.df['Destination'].str.lower() == destination_name]
        
        if destination_match.empty:
            # Essayer une recherche partielle
            partial_matches = self.df[self.df['Destination'].str.lower().str.contains(destination_name)]
            if not partial_matches.empty:
                suggestions = partial_matches['Destination'].head(3).tolist()
                return {"error": f"Destination '{destination_name}' non trouvée. Suggestions: {', '.join(suggestions)}"}
            return {"error": f"Destination '{destination_name}' non trouvée"}
        
        idx = destination_match.index[0]
        destination_data = self.df.loc[idx]
        
        print(f"✅ Destination trouvée: {destination_data['Destination']} (index: {idx})")
        
        # Calculer les similarités
        scores = list(enumerate(self.global_sim[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        
        # Ignorer la destination elle-même et prendre les N meilleures
        recommendations = []
        for i, (index, score) in enumerate(scores[1:n_recommendations+1], 1):
            rec_destination = self.df.loc[index]
            
            recommendations.append({
                'rank': i,
                'destination': rec_destination['Destination'],
                'country': rec_destination['Country'],
                'category': rec_destination['Category'],
                'cost_of_living': rec_destination['Cost of Living'],
                'safety': rec_destination['Safety'],
                'similarity_score': round(float(score), 3)
            })
        
        result = {
            'original_destination': {
                'name': destination_data['Destination'],
                'country': destination_data['Country'],
                'category': destination_data['Category'],
                'cost_of_living': destination_data['Cost of Living'],
                'safety': destination_data['Safety']
            },
            'recommendations': recommendations
        }
        
        print(f"✅ {len(recommendations)} recommandations générées")
        return result

# Instance globale
recommender = DestinationRecommender()
