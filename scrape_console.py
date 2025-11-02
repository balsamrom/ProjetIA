# -*- coding: utf-8 -*-
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
            log_message("ERROR: Missing one or more environment variables.", logfile)
            sys.exit(1)

        try:
            jenkins_user, jenkins_token = jenkins_auth.split(':', 1)
        except ValueError:
            log_message("ERROR: Invalid JENKINS_AUTH format. Expected user:token.", logfile)
            sys.exit(1)

        if not jenkins_url.endswith('/'):
            jenkins_url += '/'

        url = f"{jenkins_url}job/{job_name}/{build_number}/consoleText"
        log_message(f"Fetching Jenkins log from: {url}", logfile)

        try:
            response = requests.get(url, auth=(jenkins_user, jenkins_token))
            response.raise_for_status()
            log = response.text
        except requests.RequestException as e:
            log_message(f"ERROR: Failed to retrieve Jenkins log: {e}", logfile)
            sys.exit(1)

        log_message("Scanning Jenkins log for errors...", logfile)

        error_keywords = ["ERROR", "Exception", "Traceback", "FAILURE", "BUILD FAILURE", "WARN"]
        error_pattern = re.compile(r"|".join(re.escape(k) for k in error_keywords), re.IGNORECASE)
        error_lines = [line for line in log.splitlines() if error_pattern.search(line)]

        if error_lines:
            log_message(f"\nDetected {len(error_lines)} error line(s):", logfile)
            for line in error_lines:
                log_message("> " + line, logfile)
            return "\n".join(error_lines)
        else:
            log_message("No errors found in Jenkins log.", logfile)
            return "No errors detected."


# ============= ETAPE 2 : ENVOI À GEMINI =============
def send_to_gemini(log_text):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            f"Here is a Jenkins log. Help me identify and fix the error:\n\n{log_text}"
        )

        print("\n--- Gemini Response ---\n")
        print(response.text)

        with open("gemini_response.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("\nGemini analysis saved to gemini_response.txt")

    except Exception as e:
        print("[Gemini API Error]", str(e))
        sys.exit(1)


# ============= MAIN PRINCIPAL =============
def main():
    log_path = "scrape_result.log"

    print("Step 1: Fetching Jenkins log")
    log_text = scrape_jenkins_log(log_path)

    print("\nStep 2: Sending log to Gemini for analysis")
    send_to_gemini(log_text)


if __name__ == "__main__":
    main()
