"""
===============================================================
🤖 MOTEUR DE RECOMMANDATION LIGHTGBM POUR DJANGO
Version : Intégration modèle .pkl + Base de données MySQL
===============================================================
"""
import os
import numpy as np
import pandas as pd
import requests
import joblib
from datetime import datetime
from django.conf import settings
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import warnings
warnings.filterwarnings("ignore")


class LightGBMRecommendationEngine:
    """
    Moteur hybride utilisant LightGBM + MySQL
    - Charge le modèle .pkl entraîné
    - Vectorise les activités à la volée avec SentenceTransformer
    - Combine activités du dataset initial + nouvelles activités DB
    """

    def __init__(self):
        """Initialisation du modèle et des composants"""
        print("🔄 Chargement du moteur LightGBM...")
        
        # Chemin du fichier modèle
        model_pkl_path = os.path.join(settings.BASE_DIR, 'activity_model.pkl')
        
        # 1️⃣ Charger le modèle et les composants
        if not os.path.exists(model_pkl_path):
            raise FileNotFoundError(
                f"❌ Fichier modèle introuvable : {model_pkl_path}\n"
                "📥 Placez 'activity_model.pkl' dans le dossier racine du projet."
            )
        
        model_data = joblib.load(model_pkl_path)
        
        # Gérer différents formats de sauvegarde
        if isinstance(model_data, dict):
            # Format dictionnaire (notre format)
            self.model = model_data.get('model')
            self.df_trained = model_data.get('df')
            self.price_scaler = model_data.get('price_scaler')
            self.category_encoder = model_data.get('category_encoder')
            self.model_date = model_data.get('model_date', datetime(2025, 1, 1))
        else:
            # Format direct (juste le modèle Booster)
            raise ValueError(
                "❌ Format de modèle non reconnu.\n"
                "Le fichier .pkl doit contenir un dictionnaire avec:\n"
                "- 'model': le modèle LightGBM\n"
                "- 'df': le dataset\n"
                "- 'price_scaler': le scaler MinMaxScaler\n"
                "- 'category_encoder': le LabelEncoder\n"
                "- 'model_date': la date de création\n\n"
                "Utilisez le script save_model.py pour créer le bon format."
            )
        
        print(f"✅ Modèle LightGBM chargé")
        print(f"✅ Données chargées : {len(self.df_trained)} activités historiques")
        print(f"📅 Date du modèle : {self.model_date.strftime('%Y-%m-%d')}")
        
        # 2️⃣ Charger le modèle NLP (SentenceTransformer)
        print("🧠 Chargement du modèle NLP...")
        self.nlp_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        print("✅ Modèle NLP prêt\n")

    def enrich_text(self, row):
        """Crée un texte enrichi pour l'embedding"""
        parts = []
        weights = {
            "activity_name": 10,
            "category": 6,
            "description": 5,
            "location": 2
        }
        for col, weight in weights.items():
            val = str(row.get(col, "")).strip()
            if val:
                parts.extend([val] * weight)
        return " ".join(parts)

    def get_weather_for_city(self, city_name, api_key="73f4a7564f5417d8d9928fbc4c39159d"):
        """Récupère la météo actuelle via OpenWeather API"""
        try:
            # Géolocalisation
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}"
            geo_res = requests.get(geo_url, timeout=8).json()
            
            if not geo_res:
                raise ValueError("Ville non trouvée")

            lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
            
            # Données météo
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}&lang=fr"
            weather_res = requests.get(weather_url, timeout=10).json()

            if weather_res.get("cod") == 200:
                temp = weather_res["main"]["temp"]
                description = weather_res["weather"][0]["description"]
                
                # Calculer comfort_index
                comfort = (1 - abs(temp - 22) / 22)
                comfort = float(np.clip(comfort, 0, 1))
                
                return {
                    "temp": round(temp, 1),
                    "description": description,
                    "comfort_index": comfort,
                    "success": True
                }

        except Exception as e:
            print(f"⚠️ Erreur météo : {e}")

        # Valeurs par défaut
        return {
            "success": False,
            "temp": 22,
            "description": "ensoleillé",
            "comfort_index": 1.0
        }

    def get_weather_category_boost(self, weather_desc):
        """
        Retourne les catégories privilégiées selon la météo
        """
        desc_lower = weather_desc.lower()
        
        if "rain" in desc_lower or "storm" in desc_lower or "overcast" in desc_lower:
            return ["culture", "gastronomy", "entertainment"], "🌧️"
        elif "cloud" in desc_lower:
            return ["culture", "nature", "entertainment"], "⛅"
        else:
            return ["adventure", "nature", "entertainment"], "☀️"

    def get_activities_from_db(self, city_normalized):
        """Récupère les activités depuis MySQL"""
        from .models import Activity
        from django.utils import timezone as django_timezone
        
        activities_qs = Activity.objects.filter(
            location__icontains=city_normalized
        ).values(
            'activity_name', 'category', 'location', 'description',
            'weather', 'popularity', 'duration', 'price', 'profile', 'created_at'
        )

        df_db = pd.DataFrame(list(activities_qs))
        
        if len(df_db) > 0:
            # Marquer les nouvelles activités
            model_date_aware = django_timezone.make_aware(self.model_date) if self.model_date.tzinfo is None else self.model_date
            df_db['created_at'] = pd.to_datetime(df_db['created_at'])
            df_db['is_new'] = df_db['created_at'] > model_date_aware
            
            print(f"💾 {len(df_db)} activités trouvées en DB (dont {df_db['is_new'].sum()} nouvelles)")
        else:
            print("ℹ️ Aucune activité trouvée en DB pour cette ville")

        return df_db

    def predict_scores(self, df, weather):
        """Calcule les scores LightGBM pour un DataFrame d'activités"""
        if df.empty:
            return df
        
        # 1️⃣ Embeddings NLP
        df['text_rich'] = df.apply(self.enrich_text, axis=1)
        embeddings = self.nlp_model.encode(df['text_rich'].tolist(), show_progress_bar=False)
        
        # 2️⃣ Features numériques
        try:
            price_scaled = self.price_scaler.transform(
                pd.to_numeric(df['price'], errors='coerce').fillna(0).values.reshape(-1, 1)
            )
        except Exception as e:
            print(f"⚠️ Erreur scaling prix: {e}")
            price_scaled = np.zeros((len(df), 1))
        
        popularity_scaled = (df['popularity'].fillna(50) / 100.0).values.reshape(-1, 1)
        comfort_index = np.full((len(df), 1), weather['comfort_index'])
        weekday = np.full((len(df), 1), datetime.now().weekday())
        month = np.full((len(df), 1), datetime.now().month)
        
        # Encoder les catégories
        try:
            category_encoded = self.category_encoder.transform(df['category'])
        except Exception as e:
            print(f"⚠️ Erreur encoding catégorie: {e}")
            # Catégories inconnues = première catégorie connue
            category_encoded = np.zeros(len(df))
        
        category_encoded = category_encoded.reshape(-1, 1)
        
        # 3️⃣ Concaténation des features (même ordre que l'entraînement)
        X_pred = np.concatenate([
            embeddings,              # 384 dimensions (SentenceTransformer)
            price_scaled,            # 1 dimension
            popularity_scaled,       # 1 dimension
            comfort_index,           # 1 dimension
            weekday,                 # 1 dimension
            month,                   # 1 dimension
            category_encoded         # 1 dimension
        ], axis=1)
        
        # 4️⃣ Prédiction LightGBM
        scores = self.model.predict(X_pred)
        df['score'] = scores
        
        # 5️⃣ Bonus selon météo
        preferred_categories, weather_icon = self.get_weather_category_boost(weather['description'])
        df['score'] = df.apply(
            lambda row: row['score'] + 0.1 if row['category'] in preferred_categories else row['score'] - 0.05,
            axis=1
        )
        
        return df

    def get_recommendations(self, city_name, top_n=20):
        """
        Recommandation finale avec LightGBM
        Combine : modèle historique + base de données
        """
        city_normalized = city_name.lower().strip()
        print(f"\n🔍 Recherche LightGBM pour : {city_name.title()}")
        
        # 1️⃣ Météo
        weather = self.get_weather_for_city(city_name)
        preferred_categories, weather_icon = self.get_weather_category_boost(weather['description'])
        
        print(f"🌤️ Météo : {weather['description']} ({weather['temp']}°C)")
        print(f"{weather_icon} Catégories privilégiées : {', '.join(preferred_categories)}")
        
        all_activities = []
        
        # 2️⃣ Activités historiques (dataset CSV)
        ml_activities = self.df_trained[
            self.df_trained['location'].str.lower().str.contains(city_normalized, na=False)
        ].copy()
        
        if len(ml_activities) > 0:
            ml_activities = self.predict_scores(ml_activities, weather)
            ml_activities['source'] = 'Modèle LightGBM'
            print(f"✅ {len(ml_activities)} activités du modèle historique")
            
            for _, row in ml_activities.iterrows():
                all_activities.append({
                    'activity_name': row['activity_name'],
                    'category': row['category'],
                    'location': row['location'],
                    'description': row.get('description', ''),
                    'weather': row.get('weather', 'unknown'),
                    'popularity': int(row.get('popularity', 50)),
                    'duration': row.get('duration', 'N/A'),
                    'price': row.get('price', 'N/A'),
                    'score': float(row['score']),
                    'source': row['source']
                })
        
        # 3️⃣ Activités de la base de données
        db_activities = self.get_activities_from_db(city_normalized)
        
        if len(db_activities) > 0:
            db_activities = self.predict_scores(db_activities, weather)
            
            for _, row in db_activities.iterrows():
                is_new = row.get('is_new', False)
                
                # Bonus pour nouvelles activités
                score = row['score']
                if is_new:
                    score *= 1.3
                
                source_label = 'DB (NOUVEAU ⭐)' if is_new else 'Base de données'
                
                all_activities.append({
                    'activity_name': row['activity_name'],
                    'category': row['category'],
                    'location': row['location'],
                    'description': row.get('description', ''),
                    'weather': row.get('weather', 'unknown'),
                    'popularity': int(row.get('popularity', 50)),
                    'duration': row.get('duration', 'N/A'),
                    'price': row.get('price', 'N/A'),
                    'score': float(score),
                    'source': source_label
                })
        
        # 4️⃣ Fusion et tri
        if not all_activities:
            print("❌ Aucune activité trouvée")
            return [], weather
        
        all_activities.sort(key=lambda x: x['score'], reverse=True)
        
        # Dédoublonnage
        seen = set()
        unique_activities = []
        for a in all_activities:
            key = (a['activity_name'].lower().strip(), a['location'].lower().strip())
            if key not in seen:
                seen.add(key)
                unique_activities.append(a)
        
        print(f"✅ {len(unique_activities[:top_n])} recommandations générées\n")
        return unique_activities[:top_n], weather


# Instance globale (pour éviter de recharger à chaque requête)
_engine = None

def get_engine():
    """Singleton : retourne l'instance unique du moteur"""
    global _engine
    if _engine is None:
        _engine = LightGBMRecommendationEngine()
    return _engine