# hug_face_service.py
import os
import requests
import json
import re
from django.conf import settings

# ⚠️ Remplacez par votre token Hugging Face
HUGGINGFACE_TOKEN = "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"

class HuggingFaceService:
    """Service pour interagir avec l'API Hugging Face"""

    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {HUGGINGFACE_TOKEN}"
        }
        # Utiliser un modèle plus adapté pour la génération structurée
        self.model = "mistralai/Mistral-7B-Instruct-v0.2"

    def _call_model(self, prompt, max_tokens=1024):
        """Appel générique au modèle HF avec gestion d'erreur améliorée"""
        try:
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": False
                }
            }
            
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{self.model}",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Gestion des différents formats de réponse
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and 'generated_text' in result[0]:
                    return result[0]['generated_text']
                return str(result[0])
            elif isinstance(result, dict) and 'generated_text' in result:
                return result['generated_text']
            
            return str(result)
            
        except requests.exceptions.Timeout:
            return "❌ Timeout: Le modèle met trop de temps à répondre"
        except requests.exceptions.RequestException as e:
            return f"❌ Erreur réseau: {str(e)}"
        except Exception as e:
            return f"❌ Erreur Hugging Face: {str(e)}"

    def _extract_json(self, text):
        """Extraire JSON du texte généré avec plusieurs stratégies"""
        try:
            # Stratégie 1: Chercher des accolades
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # Stratégie 2: Parser directement si c'est déjà du JSON
            return json.loads(text)
            
        except json.JSONDecodeError:
            # Si échec, retourner une structure par défaut
            return None

    def generate_destination_description(self, destination_name, country, category=None):
        """Génération complète d'une destination avec fallback"""
        category_text = f", catégorie {category}" if category else ""
        
        # Prompt optimisé pour Mistral
        prompt = f"""[INST] Tu es un expert en tourisme. Génère une description JSON STRICTE pour cette destination.

Destination: {destination_name}
Pays: {country}{category_text}

Réponds UNIQUEMENT avec ce format JSON (sans texte avant/après):

{{
    "description": "Description attrayante de 3-4 phrases sur {destination_name}",
    "best_time": "Meilleure période (ex: Avril-Octobre)",
    "cultural_significance": "Paragraphe sur l'importance culturelle",
    "famous_foods": "Plat1, Plat2, Plat3, Plat4",
    "activities": "Activité1, Activité2, Activité3, Activité4, Activité5"
}}

JSON: [/INST]"""

        print(f"📤 Envoi prompt à {self.model}...")
        result_text = self._call_model(prompt, max_tokens=1024)
        
        if result_text.startswith("❌"):
            print(f"❌ Erreur API: {result_text}")
            return self._generate_fallback(destination_name, country, category)
        
        print(f"📥 Réponse brute reçue: {result_text[:200]}...")
        
        # Tentative d'extraction JSON
        json_data = self._extract_json(result_text)
        
        if json_data:
            # Validation des clés requises
            required_keys = ["description", "best_time", "cultural_significance", "famous_foods", "activities"]
            if all(key in json_data for key in required_keys):
                print("✅ JSON valide extrait avec succès")
                return {"success": True, "data": json_data}
        
        print("⚠️ JSON invalide, utilisation du fallback")
        return self._generate_fallback(destination_name, country, category)

    def _generate_fallback(self, destination_name, country, category):
        """Génération de données par défaut si l'IA échoue"""
        print(f"🔄 Génération fallback pour {destination_name}")
        
        category_desc = ""
        activities_default = "Visite guidée, Photographie, Gastronomie locale, Shopping, Détente"
        
        if category:
            category_map = {
                "Beach": ("destination balnéaire idéale", "Baignade, Plongée, Sports nautiques, Bronzage, Excursions en bateau"),
                "Mountain": ("destination montagneuse", "Randonnée, Ski, Escalade, VTT, Observation de la nature"),
                "City": ("métropole vibrante", "Visite de musées, Shopping, Vie nocturne, Gastronomie, Architecture"),
                "Cultural": ("haut lieu culturel", "Visite de monuments, Musées, Spectacles, Festivals, Gastronomie"),
                "Adventure": ("destination d'aventure", "Trekking, Rafting, Safari, Parapente, Exploration"),
                "Relaxation": ("havre de paix", "Spa, Yoga, Méditation, Massage, Détente"),
                "Historical": ("site historique majeur", "Visite de sites historiques, Musées, Circuits guidés, Photographie")
            }
            if category in category_map:
                category_desc = category_map[category][0]
                activities_default = category_map[category][1]
        
        fallback_data = {
            "description": f"{destination_name} est une {category_desc or 'magnifique destination'} située en {country}. "
                          f"Cette destination attire des visiteurs du monde entier grâce à son charme unique, "
                          f"son patrimoine culturel riche et ses paysages exceptionnels. "
                          f"Un lieu incontournable pour les voyageurs en quête d'authenticité.",
            
            "best_time": "Avril à Octobre (selon climat local)",
            
            "cultural_significance": f"{destination_name} possède une riche histoire qui se reflète dans son architecture, "
                                    f"ses traditions et son art de vivre. La destination est reconnue pour son importance "
                                    f"culturelle en {country} et représente un symbole fort du patrimoine national.",
            
            "famous_foods": "Cuisine locale, Spécialités régionales, Plats traditionnels, Produits du terroir",
            
            "activities": activities_default
        }
        
        return {
            "success": True, 
            "data": fallback_data,
            "fallback": True,
            "message": "⚠️ Données générées par défaut (l'IA n'a pas pu générer de contenu)"
        }

    def enhance_destination_info(self, destination_name, country):
        """Enrichir les informations d'une destination existante"""
        prompt = f"""[INST] Fournis 3 faits intéressants, des conseils pratiques et un budget estimé pour {destination_name} ({country}).

Format:
- Fait 1: ...
- Fait 2: ...
- Fait 3: ...
- Conseils: ...
- Budget: ... USD/jour [/INST]"""
        
        try:
            result_text = self._call_model(prompt, max_tokens=512)
            if not result_text.startswith("❌"):
                return {"success": True, "data": result_text}
            return {"success": False, "error": result_text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def suggest_similar_destinations(self, destination_name, country, n=3):
        """Suggérer des destinations similaires"""
        prompt = f"""[INST] Suggère {n} destinations similaires à {destination_name} ({country}).

Format:
1. Nom, Pays - Raison
2. Nom, Pays - Raison
3. Nom, Pays - Raison [/INST]"""
        
        try:
            result_text = self._call_model(prompt, max_tokens=512)
            if not result_text.startswith("❌"):
                return {"success": True, "data": result_text}
            return {"success": False, "error": result_text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_connection(self):
        """Teste la connexion à l'API HF"""
        prompt = "[INST] Réponds par 'OK' si tu peux lire ceci. [/INST]"
        result = self._call_model(prompt, max_tokens=10)
        
        if "OK" in result or "ok" in result.lower():
            print("✅ Test de connexion Hugging Face réussi")
            return True
        
        print(f"❌ Test de connexion Hugging Face échoué: {result}")
        return False

# Instance globale
hf_service = HuggingFaceService()