pipeline {
    agent any

    environment {
        SONARQUBE = 'sonar' // Nom du serveur Sonar configuré dans Jenkins
        VENV = 'venv'
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/balsamrom/ProjetIA.git'
            }
        }

        stage('Create & Activate Virtual Env') {
            steps {
                bat '''
                if not exist %VENV% (
                    echo Creating virtual environment...
                    python -m venv %VENV%
                ) else (
                    echo Virtualenv already exists.
                )

                call %VENV%\\Scripts\\activate
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Python Script') {
            steps {
                withCredentials([string(credentialsId: 'jenkins-auth', variable: 'JENKINS_AUTH')]) {
                    bat '''
                    call %VENV%\\Scripts\\activate
                    python scrape_console.py
                    '''
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonar') {
                    bat '''
                    call %VENV%\\Scripts\\activate
                    "C:\\sonar-scanner-7.3.0.5189-windows-x64\\bin\\sonar-scanner.bat" ^
                        -Dsonar.projectKey=ProjetIA ^
                        -Dsonar.sources=. ^
                        -Dsonar.host.url=%SONAR_HOST_URL% ^
                        -Dsonar.login=%SONAR_AUTH_TOKEN%
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline succeeded."
        }
        failure {
            echo "❌ Pipeline failed."
        }
    }
}
