"""
===============================================================
📦 SCRIPT POUR SAUVEGARDER LE MODÈLE LIGHTGBM
À exécuter après l'entraînement du modèle
===============================================================
"""
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import lightgbm as lgb
import warnings
warnings.filterwarnings("ignore")

print("🔄 Chargement et préparation des données...")

# ===============================================================
# 1. CHARGEMENT DES DONNÉES
# ===============================================================
import os

# Chercher le fichier CSV automatiquement
possible_paths = [
    "tourism_activities_world_tunisia_60000.csv",
    "../tourism_activities_world_tunisia_60000.csv",
    "../../tourism_activities_world_tunisia_60000.csv",
    os.path.join(os.path.dirname(__file__), "tourism_activities_world_tunisia_60000.csv"),
    os.path.join(os.path.dirname(__file__), "..", "tourism_activities_world_tunisia_60000.csv")
]

csv_path = None
for path in possible_paths:
    if os.path.exists(path):
        csv_path = path
        break

if csv_path is None:
    # Demander à l'utilisateur
    print("❌ Fichier CSV introuvable. Chemins testés:")
    for p in possible_paths:
        print(f"   - {os.path.abspath(p)}")
    csv_path = input("\n📁 Entrez le chemin complet du fichier CSV : ").strip()

print(f"📂 Utilisation du fichier : {csv_path}")
df = pd.read_csv(csv_path)
df.drop_duplicates(subset=["activity_name", "location"], inplace=True)
df.fillna("", inplace=True)

df['date'] = pd.to_datetime(df.get('date', pd.Series([None] * len(df))), errors='coerce')
df['weekday'] = df['date'].dt.dayofweek.fillna(0).astype(int)
df['month'] = df['date'].dt.month.fillna(1).astype(int)
df['temp'] = df.get('temp', 22)
df['comfort_index'] = (1 - abs(df['temp'] - 22) / 22).clip(0, 1)

df.reset_index(drop=True, inplace=True)
print(f"✅ Dataset chargé : {len(df)} activités\n")

# ===============================================================
# 2. ENCODAGE NLP
# ===============================================================
def enrich_text(row):
    parts = []
    for col, weight in [("activity_name", 10), ("category", 6), ("description", 5), ("location", 2)]:
        val = str(row.get(col, "")).strip()
        if val:
            parts.extend([val] * weight)
    return " ".join(parts)

df["text_rich"] = df.apply(enrich_text, axis=1)
print("🧠 Génération des embeddings NLP...")
nlp_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
embeddings = nlp_model.encode(df["text_rich"].tolist(), show_progress_bar=True)
print(f"✅ Embeddings générés : {embeddings.shape}\n")

# ===============================================================
# 3. PRÉPARATION DES FEATURES
# ===============================================================
price_scaler = MinMaxScaler()
df['price_scaled'] = price_scaler.fit_transform(df[['price']])
df['popularity_scaled'] = df['popularity'] / 100.0

category_encoder = LabelEncoder()
df['category_encoded'] = category_encoder.fit_transform(df['category'])

X_features = np.concatenate([
    embeddings,
    df[['price_scaled']].values,
    df[['popularity_scaled']].values,
    df[['comfort_index']].values,
    df[['weekday']].values,
    df[['month']].values,
    df[['category_encoded']].values
], axis=1)

df['score_target'] = 0.7 * df['popularity_scaled'] + 0.3 * df['comfort_index']

# ===============================================================
# 4. ENTRAÎNEMENT DU MODÈLE LIGHTGBM
# ===============================================================
X_train, X_val, y_train, y_val = (
    X_features[:900],
    X_features[900:],
    df['score_target'][:900],
    df['score_target'][900:]
)

params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'verbose': -1
}

train_data = lgb.Dataset(X_train, label=y_train)
val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

model = lgb.train(
    params,
    train_data,
    num_boost_round=200,
    valid_sets=[val_data],
    callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)]
)
print("✅ Modèle entraîné avec succès.\n")

# ===============================================================
# 5. SAUVEGARDE DU MODÈLE ET DES COMPOSANTS
# ===============================================================
print("💾 Sauvegarde du modèle et des composants...")

model_data = {
    'model': model,                        # Modèle LightGBM
    'df': df,                              # Dataset complet
    'price_scaler': price_scaler,          # Scaler pour les prix
    'category_encoder': category_encoder,  # Encoder pour les catégories
    'model_date': datetime.now(),          # Date de création du modèle
    'embeddings_shape': embeddings.shape,  # Info sur les embeddings
    'features_info': {
        'total_features': X_features.shape[1],
        'embedding_dim': embeddings.shape[1],
        'num_features': 6  # price, popularity, comfort, weekday, month, category
    }
}

# Sauvegarder avec joblib
joblib.dump(model_data, 'activity_model.pkl', compress=3)

print("✅ Modèle sauvegardé dans 'activity_model.pkl'")
print(f"📊 Taille du fichier : {round(os.path.getsize('activity_model.pkl') / (1024*1024), 2)} MB")
print(f"📅 Date de création : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n🎯 Vous pouvez maintenant copier 'activity_model.pkl' dans votre projet Django!")