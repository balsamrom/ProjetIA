import requests
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image

class UnsplashService:
    def __init__(self):
        # 🔑 TON ACCESS KEY UNSPLASH (gratuit sur unsplash.com/developers)
        self.access_key = "GWRESKq_cNIDHxj96zm1RZ76v5AAOR9v0rDZzIIa914" 
        self.base_url = "https://api.unsplash.com"
    
    def search_photo(self, query, orientation='landscape'):
        """
        Recherche une photo sur Unsplash
        
        Args:
            query: Terme de recherche (ex: "Paris France")
            orientation: 'landscape', 'portrait', ou 'squarish'
            
        Returns:
            dict: {'success': True/False, 'photo_url': url, 'photo_data': data, 'error': message}
        """
        try:
            print(f"🔍 Recherche photo Unsplash: {query}")
            
            # Endpoint de recherche
            url = f"{self.base_url}/search/photos"
            
            # Paramètres de la requête
            params = {
                'query': query,
                'per_page': 1,  # On prend la meilleure photo
                'orientation': orientation,
                'order_by': 'relevant',  # Les plus pertinentes
                'content_filter': 'high'  # Contenu de haute qualité
            }
            
            # Headers avec ton Access Key
            headers = {
                'Authorization': f'Client-ID {self.access_key}'
            }
            
            # Faire la requête
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['results'] and len(data['results']) > 0:
                    photo = data['results'][0]
                    
                    # Récupérer l'URL de la photo en qualité régulière
                    photo_url = photo['urls']['regular']  # Qualité moyenne (bonne pour le web)
                    # Alternatives: 'full', 'raw', 'small', 'thumb'
                    
                    # Informations supplémentaires
                    photographer = photo['user']['name']
                    photographer_url = photo['user']['links']['html']
                    
                    print(f"✅ Photo trouvée par {photographer}")
                    
                    return {
                        'success': True,
                        'photo_url': photo_url,
                        'photo_data': photo,
                        'photographer': photographer,
                        'photographer_url': photographer_url,
                        'description': photo.get('description', query)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Aucune photo trouvée pour cette recherche'
                    }
            
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': '❌ Access Key invalide. Vérifie ton token Unsplash.'
                }
            
            elif response.status_code == 403:
                return {
                    'success': False,
                    'error': '❌ Limite de requêtes atteinte (50/heure en mode démo)'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Erreur API: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur: {str(e)}'
            }
    
    def download_photo(self, photo_url):
        """
        Télécharge une photo depuis son URL
        
        Args:
            photo_url: URL de la photo
            
        Returns:
            BytesIO: Fichier image téléchargé
        """
        try:
            print(f"📥 Téléchargement de la photo...")
            
            response = requests.get(photo_url, timeout=30)
            
            if response.status_code == 200:
                # Ouvrir l'image avec Pillow pour vérifier qu'elle est valide
                image = Image.open(BytesIO(response.content))
                
                # Redimensionner si trop grande (optionnel, pour économiser l'espace)
                max_width = 1920
                if image.width > max_width:
                    ratio = max_width / image.width
                    new_height = int(image.height * ratio)
                    image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Convertir en BytesIO
                img_io = BytesIO()
                image.save(img_io, format='JPEG', quality=85)
                img_io.seek(0)
                
                print(f"✅ Photo téléchargée avec succès")
                return img_io
            else:
                print(f"❌ Erreur téléchargement: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return None
    
    def get_photo_for_destination(self, destination_name, country):
        """
        Recherche et télécharge une photo pour une destination
        
        Args:
            destination_name: Nom de la destination (ex: "Paris")
            country: Pays (ex: "France")
            
        Returns:
            dict: {'success': True/False, 'image_file': BytesIO, 'filename': str, 'error': message}
        """
        # Créer une requête optimisée
        search_query = f"{destination_name} {country} travel destination"
        
        # Rechercher la photo
        result = self.search_photo(search_query)
        
        if result['success']:
            # Télécharger la photo
            image_file = self.download_photo(result['photo_url'])
            
            if image_file:
                # Créer un nom de fichier propre
                filename = f"{destination_name.replace(' ', '_').lower()}.jpg"
                
                return {
                    'success': True,
                    'image_file': image_file,
                    'filename': filename,
                    'photographer': result['photographer'],
                    'photographer_url': result['photographer_url']
                }
            else:
                return {
                    'success': False,
                    'error': 'Erreur lors du téléchargement de l\'image'
                }
        else:
            return result

# Instance globale
unsplash_service = UnsplashService()