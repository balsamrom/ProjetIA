import pandas as pd
import joblib
import os
from datetime import datetime
from django.conf import settings
from sklearn.metrics.pairwise import cosine_similarity
from .models import Activity
import requests


class HybridRecommendationEngine:
    """
    Moteur hybride amélioré :
    - Combine modèle ML (PKL) ET base MySQL
    - Vectorise les nouvelles activités à la volée
    - Gère les villes absentes du modèle
    """

    def __init__(self):
        """Charge le modèle PKL au démarrage"""
        model_path = os.path.join(settings.BASE_DIR, 'tourism_recommendation_model.pkl')

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"❌ Fichier modèle introuvable : {model_path}\n"
                "📥 Place 'tourism_recommendation_model.pkl' dans le dossier racine du projet."
            )

        print("🔄 Chargement du modèle ML...")
        self.model_data = joblib.load(model_path)

        # Extraire les composants du modèle
        self.df_trained = self.model_data['df']
        self.tfidf = self.model_data['tfidf']
        self.X_tfidf = self.model_data['X_tfidf']
        self.kmeans = self.model_data['kmeans']
        self.available_cities = self.model_data['available_cities']
        self.weather_map = self.model_data['weather_map']

        # Date du modèle (utilisée uniquement pour identifier les "nouvelles" activités)
        self.model_date = self.model_data.get('model_date', datetime(2025, 1, 1))

        print(f"✅ Modèle chargé : {len(self.df_trained)} activités historiques")
        print(f"📅 Date du modèle : {self.model_date.strftime('%Y-%m-%d')}\n")

    # ==============================
    # 🔹 Étape 1 : Récupérer TOUTES les activités de la DB pour une ville
    # ==============================
    def get_activities_from_db(self, city_normalized):
        """
        Récupère TOUTES les activités pour une ville depuis la DB
        (pas seulement les nouvelles)
        """
        activities_qs = Activity.objects.filter(
            location__icontains=city_normalized
        ).values(
            'activity_name', 'category', 'location', 'description',
            'weather', 'popularity', 'duration', 'price', 'profile', 'created_at'
        )

        df_db = pd.DataFrame(list(activities_qs))
        
        if len(df_db) > 0:
            # Marquer les activités ajoutées après la génération du modèle
            df_db['is_new'] = df_db['created_at'] > self.model_date
            print(f"💾 {len(df_db)} activités trouvées en DB (dont {df_db['is_new'].sum()} nouvelles)")
        else:
            print("ℹ️ Aucune activité trouvée en DB pour cette ville")

        return df_db

    # ==============================
    # 🔹 Étape 2 : Vectorisation des activités DB
    # ==============================
    def vectorize_db_activities(self, df_db):
        """Vectorise et calcule la similarité sémantique pour les activités DB"""
        if df_db.empty:
            return df_db

        # Créer le texte pour TF-IDF
        df_db['text'] = df_db['description'].fillna('') + ' ' + df_db['category'].fillna('')
        X_db_tfidf = self.tfidf.transform(df_db['text'])

        # Calculer la similarité moyenne avec le modèle ML
        cosine_sim = cosine_similarity(X_db_tfidf, self.X_tfidf)
        df_db['semantic_similarity'] = cosine_sim.mean(axis=1)

        print("📐 Similarité sémantique calculée pour activités DB")
        return df_db

    # ==============================
    # 🔹 Étape 3 : Calcul du score (amélioré)
    # ==============================
    def calculate_activity_score(self, row, weather, is_new=False, is_from_db=False):
        """
        Calcule le score d'une activité
        - is_new : activité ajoutée après la génération du modèle
        - is_from_db : activité provenant de la DB (peut être ancienne ou nouvelle)
        """
        base_score = row.get('popularity', 50) / 100

        # Bonus pour nouvelles activités
        if is_new:
            base_score *= 1.3  # +30% pour les nouvelles activités

        # Bonus léger pour les activités DB (même anciennes)
        if is_from_db and not is_new:
            base_score *= 1.1  # +10% pour assurer qu'elles apparaissent

        # Compatibilité météo
        if weather and weather.get('success'):
            user_weather = weather['category']
            activity_weather = self.weather_map.get(str(row.get('weather', '')).lower().strip(), 'unknown')

            if user_weather == activity_weather:
                base_score *= 2.5  # Match parfait
            elif user_weather in ['hot', 'sunny'] and activity_weather in ['hot', 'sunny']:
                base_score *= 2.0
            elif user_weather in ['cold', 'rainy'] and activity_weather in ['cold', 'rainy']:
                base_score *= 1.8
            else:
                base_score *= 0.8  # Météo incompatible

        # Bonus de similarité sémantique (pour activités DB uniquement)
        if is_from_db and 'semantic_similarity' in row:
            base_score *= (1 + row['semantic_similarity'] * 0.5)

        return base_score

    # ==============================
    # 🔹 Étape 4 : Recommandation finale (LOGIQUE HYBRIDE)
    # ==============================
    def get_recommendations(self, city_name, weather, top_n=20):
        city_normalized = city_name.lower().strip()
        print(f"\n🔍 Recherche hybride pour : {city_name.title()}")
        print(f"🌤️ Météo : {weather.get('category', 'unknown')} ({weather.get('temp', 'N/A')}°C)")

        all_activities = []

        # --- SOURCE 1 : Modèle ML (activités historiques) ---
        ml_activities = self.df_trained[
            self.df_trained['location_normalized'].str.contains(city_normalized, na=False)
        ].copy()

        if len(ml_activities) > 0:
            ml_activities['score'] = ml_activities.apply(
                lambda row: self.calculate_activity_score(row, weather, is_new=False, is_from_db=False),
                axis=1
            )
            ml_activities['source'] = 'Modèle ML'
            print(f"✅ {len(ml_activities)} activités du modèle ML")
            
            for _, row in ml_activities.iterrows():
                all_activities.append({
                    'activity_name': row['activity_name'],
                    'category': row['category'],
                    'location': row['location'],
                    'description': row['description'],
                    'weather': row.get('weather', 'unknown'),
                    'popularity': row.get('popularity', 50),
                    'duration': row.get('duration', 'N/A'),
                    'price': row.get('price', 'N/A'),
                    'score': row['score'],
                    'source': row['source']
                })
        else:
            print("⚠️ Aucune activité trouvée dans le modèle ML pour cette ville")

        # --- SOURCE 2 : Base de données (TOUTES les activités) ---
        db_activities = self.get_activities_from_db(city_normalized)
        
        if len(db_activities) > 0:
            db_activities = self.vectorize_db_activities(db_activities)
            db_activities['location_normalized'] = db_activities['location'].str.lower()
            db_activities['weather_clean'] = db_activities['weather'].apply(
                lambda x: self.weather_map.get(str(x).lower().strip(), 'unknown')
            )
            
            for _, row in db_activities.iterrows():
                is_new = row.get('is_new', False)
                score = self.calculate_activity_score(row, weather, is_new=is_new, is_from_db=True)
                
                source_label = 'DB (NOUVEAU ⭐)' if is_new else 'Base de données'
                
                all_activities.append({
                    'activity_name': row['activity_name'],
                    'category': row['category'],
                    'location': row['location'],
                    'description': row['description'],
                    'weather': row.get('weather', 'unknown'),
                    'popularity': row.get('popularity', 50),
                    'duration': row.get('duration', 'N/A'),
                    'price': row.get('price', 'N/A'),
                    'score': score,
                    'source': source_label
                })

        # --- Fusion et dédoublonnage ---
        if not all_activities:
            print("❌ Aucune activité trouvée pour cette ville (ni ML, ni DB)")
            return []

        # Tri par score décroissant
        all_activities.sort(key=lambda x: x['score'], reverse=True)
        
        # Supprimer les doublons (même activité = même nom + même lieu)
        seen = set()
        unique_activities = []
        for a in all_activities:
            key = (a['activity_name'].lower().strip(), a['location'].lower().strip())
            if key not in seen:
                seen.add(key)
                unique_activities.append(a)

        print(f"✅ {len(unique_activities[:top_n])} recommandations générées (après dédoublonnage)\n")
        return unique_activities[:top_n]


# ==============================
# 🌦️ Fonction Météo (inchangée)
# ==============================
def get_weather_for_city(city_name, api_key="73f4a7564f5417d8d9928fbc4c39159d"):
    """Récupère la météo actuelle via OpenWeather"""
    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}"
        geo_res = requests.get(geo_url, timeout=8).json()
        if not geo_res:
            raise ValueError("Ville non trouvée")

        lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}&lang=fr"
        weather_res = requests.get(weather_url, timeout=10).json()

        if weather_res.get("cod") == 200:
            temp = weather_res["main"]["temp"]
            description = weather_res["weather"][0]["description"]
            main_weather = weather_res["weather"][0]["main"]
            wind_speed = weather_res.get("wind", {}).get("speed", 0)

            category = "sunny"
            if "rain" in description.lower() or main_weather == "Rain":
                category = "rainy"
            elif "snow" in description.lower() or main_weather == "Snow":
                category = "snowy"
            elif wind_speed > 10:
                category = "windy"
            elif temp >= 32:
                category = "hot"
            elif temp < 10:
                category = "cold"

            return {
                "temp": round(temp, 1),
                "description": description,
                "main": main_weather,
                "category": category,
                "success": True,
                "humidity": weather_res["main"]["humidity"],
                "wind_speed": wind_speed
            }

    except Exception as e:
        print(f"⚠️ Erreur météo : {e}")

    return {
        "success": False,
        "category": "sunny",
        "temp": 22,
        "description": "ensoleillé",
        "humidity": 60,
        "wind_speed": 3.0
    }