"""
===============================================================
🔄 SCRIPT POUR CONVERTIR UN MODÈLE EXISTANT
Prend votre modèle actuel et crée le bon format pour Django
===============================================================
"""
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import warnings
warnings.filterwarnings("ignore")

print("🔄 Conversion du modèle existant...")

# ===============================================================
# 1. CHARGER LE MODÈLE EXISTANT
# ===============================================================
existing_model_path = input("📁 Chemin du fichier .pkl existant (ou ENTER pour 'activity_model.pkl'): ").strip()
if not existing_model_path:
    existing_model_path = "activity_model.pkl"

if not os.path.exists(existing_model_path):
    print(f"❌ Fichier introuvable : {existing_model_path}")
    exit(1)

print(f"📂 Chargement de {existing_model_path}...")
try:
    old_data = joblib.load(existing_model_path)
    print(f"✅ Fichier chargé. Type: {type(old_data)}")
    
    # Afficher le contenu
    if isinstance(old_data, dict):
        print("📋 Clés disponibles:", list(old_data.keys()))
    
except Exception as e:
    print(f"❌ Erreur de chargement: {e}")
    exit(1)

# ===============================================================
# 2. CHARGER LE DATASET
# ===============================================================
csv_paths = [
    "tourism_activities_world_tunisia_60000.csv",
    "../tourism_activities_world_tunisia_60000.csv",
    "../../tourism_activities_world_tunisia_60000.csv",
    "voguevue/tourism_activities_world_tunisia_60000.csv"
]

csv_path = None
for path in csv_paths:
    if os.path.exists(path):
        csv_path = path
        break

if not csv_path:
    csv_path = input("\n📁 Chemin du fichier CSV : ").strip()

print(f"📂 Chargement du dataset depuis {csv_path}...")
df = pd.read_csv(csv_path)
df.drop_duplicates(subset=["activity_name", "location"], inplace=True)
df.fillna("", inplace=True)

# Préparer les colonnes nécessaires
df['date'] = pd.to_datetime(df.get('date', pd.Series([None] * len(df))), errors='coerce')
df['weekday'] = df['date'].dt.dayofweek.fillna(0).astype(int)
df['month'] = df['date'].dt.month.fillna(1).astype(int)
df['temp'] = df.get('temp', 22)
df['comfort_index'] = (1 - abs(df['temp'] - 22) / 22).clip(0, 1)

print(f"✅ Dataset chargé : {len(df)} activités\n")

# ===============================================================
# 3. RECRÉER LES ENCODERS
# ===============================================================
print("🔧 Création des encoders...")

price_scaler = MinMaxScaler()
price_scaler.fit(df[['price']])

category_encoder = LabelEncoder()
category_encoder.fit(df['category'])

print(f"✅ Price scaler créé (min={df['price'].min()}, max={df['price'].max()})")
print(f"✅ Category encoder créé ({len(category_encoder.classes_)} catégories)")

# ===============================================================
# 4. EXTRAIRE LE MODÈLE
# ===============================================================
print("\n🔍 Extraction du modèle LightGBM...")

model = None
if isinstance(old_data, dict):
    # Chercher la clé du modèle
    for key in ['model', 'booster', 'lgb_model', 'lightgbm']:
        if key in old_data:
            model = old_data[key]
            print(f"✅ Modèle trouvé à la clé '{key}'")
            break
else:
    # C'est directement le modèle
    model = old_data
    print("✅ Fichier .pkl contient directement le modèle")

if model is None:
    print("❌ Impossible de trouver le modèle LightGBM")
    print("📋 Contenu du fichier:")
    if isinstance(old_data, dict):
        for k, v in old_data.items():
            print(f"   - {k}: {type(v)}")
    exit(1)

# ===============================================================
# 5. CRÉER LE NOUVEAU FORMAT
# ===============================================================
print("\n💾 Création du nouveau fichier au bon format...")

new_model_data = {
    'model': model,
    'df': df,
    'price_scaler': price_scaler,
    'category_encoder': category_encoder,
    'model_date': datetime.now(),
    'features_info': {
        'embedding_dim': 384,  # SentenceTransformer dimension
        'num_features': 6,
        'total_features': 390  # 384 + 6
    }
}

# Sauvegarder
output_path = 'activity_model_django.pkl'
joblib.dump(new_model_data, output_path, compress=3)

file_size = os.path.getsize(output_path) / (1024*1024)
print(f"\n✅ Nouveau modèle sauvegardé : {output_path}")
print(f"📊 Taille : {round(file_size, 2)} MB")
print(f"📁 Chemin complet : {os.path.abspath(output_path)}")

# ===============================================================
# 6. TEST DE CHARGEMENT
# ===============================================================
print("\n🧪 Test de chargement...")
try:
    test_data = joblib.load(output_path)
    assert 'model' in test_data
    assert 'df' in test_data
    assert 'price_scaler' in test_data
    assert 'category_encoder' in test_data
    print("✅ Test réussi ! Le fichier est au bon format.")
except Exception as e:
    print(f"❌ Erreur lors du test : {e}")
    exit(1)

print("\n🎯 PROCHAINES ÉTAPES:")
print(f"1. Copiez '{output_path}' dans la racine de votre projet Django")
print(f"2. Renommez-le en 'activity_model.pkl'")
print(f"3. Lancez: python manage.py runserver")
print("\nOu utilisez cette commande:")
print(f"   copy {output_path} ..\\activity_model.pkl")