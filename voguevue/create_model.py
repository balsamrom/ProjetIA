# create_model.py
import pickle
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import numpy as np

# Données d'exemple - remplacez par vos vraies données
data = np.random.rand(10, 5)  # 10 destinations, 5 caractéristiques

# Créez un modèle simple
model = NearestNeighbors(n_neighbors=3, metric='cosine')
model.fit(data)

# Sauvegardez le modèle
with open('tourism_recommendation_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("✅ Modèle créé et sauvegardé!")