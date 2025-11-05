
# 🌍 VoyageVue – Module Gestion des Destinations et Recommandation Intelligente

## 🧠 Description du module
Ce module fait partie du projet **VoyageVue**, une plateforme touristique intelligente.  
Il permet à la fois la **gestion complète des destinations** (CRUD) et la **recommandation automatique** de lieux similaires à l’aide d’un modèle d’intelligence artificielle.  
Le but est d’offrir une expérience utilisateur moderne, personnalisée et enrichie grâce à la combinaison de **Machine Learning** et d’**APIs externes**.

---

## 🎯 Objectifs du projet
- Automatiser la création et la gestion des fiches touristiques.
- Générer automatiquement du contenu descriptif et des images de haute qualité.
- Recommander des destinations similaires selon les préférences utilisateur.
- Démontrer l’utilisation concrète de l’intelligence artificielle dans le domaine du tourisme.

---

## ⚙️ Fonctionnalités principales
1. **Gestion des destinations (CRUD)** :  
   Création, consultation, modification et suppression de fiches touristiques avec validation et pagination.

2. **Recommandation intelligente** :  
   Un modèle de Machine Learning basé sur **Random Forest** suggère des destinations similaires selon les caractéristiques textuelles et numériques.

3. **Génération automatique de contenu** :  
   Intégration de deux APIs externes :
   - **Unsplash API** : récupération d’une image selon le nom et le pays de la destination.
   - **Hugging Face API** : génération du texte descriptif, de la meilleure période de visite, des plats typiques et des éléments culturels.

Grâce à ces intégrations, chaque destination devient une fiche complète, cohérente et illustrée automatiquement.

---

## 🧩 Technologies utilisées
- **Backend :** Django / Python  
- **IA & Machine Learning :** Scikit-learn, Pandas, NumPy, Imbalanced-learn  
- **NLP :** TF-IDF Vectorizer  
- **APIs externes :** Hugging Face API, Unsplash API  
- **Stockage du modèle :** Joblib  
- **Environnement :** Google Colab, VS Code  

---

## 🤖 Système d’intelligence artificielle

Le modèle de recommandation est basé sur un **Random Forest Classifier** entraîné sur un dataset de **175 destinations** après nettoyage et préparation des données.  
Le texte des destinations est vectorisé grâce à **TF-IDF** pour représenter le contenu de chaque fiche sous forme numérique.  
Les caractéristiques catégorielles (pays, catégorie, sécurité, coût de vie, région) sont également encodées et combinées aux features textuelles.

- **Nombre total de features :** 805  
  (800 textuelles + 5 numériques)  
- **Split :** 80 % entraînement / 20 % test  
- **Rééquilibrage :** SMOTE  
- **Validation croisée :** 5-fold  

### Résultats obtenus :
- Accuracy (test) : **82.86 %**  
- F1-score (test) : **0.7754**  
- Validation croisée moyenne : **99.18 %**

Ces résultats démontrent une excellente capacité de généralisation et une grande stabilité du modèle.

---

## 🔍 Fonctionnement du moteur de recommandation
1. L’utilisateur saisit une destination de référence (exemple : *Paris*).  
2. Le modèle calcule la **similarité cosinus** entre cette destination et toutes les autres.  
3. Les 5 destinations les plus proches sont affichées (par exemple : *Nice, Cannes, Milan, Bordeaux, Venise*).  

Les scores de similarité varient entre 0 et 1, indiquant le niveau de proximité entre les destinations.

---

## 🖼️ Intégration visuelle
Chaque fiche de destination est automatiquement enrichie :
- d’un **visuel haute qualité** via **Unsplash API**  
- d’un **texte généré** via **Hugging Face API**  
- d’informations complémentaires comme la **meilleure période de visite**, les **plats locaux**, et des **éléments culturels**.

Ces ajouts permettent d’offrir des fiches dynamiques et complètes sans saisie manuelle.

---

## 💾 Sauvegarde et intégration
Le modèle entraîné est sauvegardé sous le format `.joblib` puis intégré au backend Django.  
Les utilisateurs peuvent accéder aux recommandations directement via la page **/recommendation/** de l’application.

---
## 🏁 Conclusion
Le module **Gestion des Destinations et Recommandation Intelligente** démontre comment l’IA peut enrichir l’expérience touristique :
- Automatisation complète des fiches grâce aux APIs.  
- Recommandations personnalisées via un modèle Random Forest performant.  
- Intégration fluide dans une application Django responsive.
  
---
  ## 🧠 Auteur du module
**Amira laffet**  
Étudiante en Génie Logiciel – Spécialité Intelligence Artificielle  
📅 Novembre 2025  


Ce projet illustre concrètement l’application du **Machine Learning** dans un contexte réel, en rendant la découverte de destinations plus intuitive, intelligente et inspirante.
