import os
import re
import sys
import requests
import google.generativeai as genai

# ============= CONFIGURATION GEMINI =============
GEMINI_API_KEY = "AIzaSyC-hUbRgnKFpCjK8-8q1AHCvA_l7i8pUEI"  
genai.configure(api_key=GEMINI_API_KEY)


def log_message(message, file):
    print(message)
    file.write(message + '\n')


# ============= ETAPE 1 : SCRAPER LE LOG JENKINS =============
def scrape_jenkins_log(log_path):
    with open(log_path, "w", encoding="utf-8") as logfile:
        jenkins_url = "http://localhost:8081/"
        job_name = os.getenv("JOB_NAME")
        build_number = os.getenv("BUILD_NUMBER")
        jenkins_auth = os.getenv("JENKINS_AUTH")

        if not all([jenkins_url, job_name, build_number, jenkins_auth]):
            log_message("❌ Erreur : variable(s) d'environnement manquante(s).", logfile)
            sys.exit(1)

        try:
            jenkins_user, jenkins_token = jenkins_auth.split(':', 1)
        except ValueError:
            log_message("❌ Erreur : format JENKINS_AUTH invalide. Utilisez user:token.", logfile)
            sys.exit(1)

        if not jenkins_url.endswith('/'):
            jenkins_url += '/'

        url = f"{jenkins_url}job/{job_name}/{build_number}/consoleText"
        log_message(f"📡 Récupération du log : {url}", logfile)

        try:
            response = requests.get(url, auth=(jenkins_user, jenkins_token))
            response.raise_for_status()
            log = response.text
        except requests.RequestException as e:
            log_message(f"⚠️ Échec de la récupération du log Jenkins : {e}", logfile)
            sys.exit(1)

        log_message("🔍 Analyse du log Jenkins...", logfile)

        error_keywords = ["ERROR", "Exception", "Traceback", "FAILURE", "BUILD FAILURE","WARN"]
        error_pattern = re.compile(r"|".join(re.escape(k) for k in error_keywords), re.IGNORECASE)
        error_lines = [line for line in log.splitlines() if error_pattern.search(line)]

        if error_lines:
            log_message(f"\n🚨 {len(error_lines)} ligne(s) d'erreur détectée(s) :", logfile)
            for line in error_lines:
                log_message("> " + line, logfile)
            return "\n".join(error_lines)
        else:
            log_message("✅ Aucun message d'erreur détecté.", logfile)
            return "Aucune erreur détectée."


# ============= ETAPE 2 : ENVOYER À GEMINI =============
def send_to_gemini(log_text):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            f"Voici un log Jenkins, peux-tu m'aider à comprendre et corriger l'erreur ?\n\n{log_text}"
        )

        print("\n🤖 Réponse Gemini :\n")
        print(response.text)

        with open("gemini_response.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("\n✅ Réponse sauvegardée dans gemini_response.txt")

    except Exception as e:
        print("[Erreur Gemini]", str(e))
        sys.exit(1)


# ============= MAIN PRINCIPAL =============
def main():
    log_path = "scrape_result.log"

    print("📥 Étape 1 : Récupération du log Jenkins")
    log_text = scrape_jenkins_log(log_path)

    print("\n📤 Étape 2 : Envoi à Gemini pour analyse")
    send_to_gemini(log_text)


if __name__ == "__main__":
    main()
