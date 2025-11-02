pipeline {
    agent any

    environment {
        SONARQUBE = 'sonar'
        VENV = 'venv'
        JENKINS_AUTH = credentials('jenkins-auth') // secret text required
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/balsamrom/ProjetIA.git'
            }
        }

        stage('Setup Virtualenv') {
            steps {
                bat '''
                if not exist %VENV% (
                    python -m venv %VENV%
                )
                call %VENV%\\Scripts\\activate
                pip install -r requirements.txt
                '''
            }
        }

        

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonar') {
                    bat '''
                    "C:\\sonar-scanner-7.3.0.5189-windows-x64\\bin\\sonar-scanner.bat" ^
                        -Dsonar.projectKey=ProjetIA ^
                        -Dsonar.sources=. ^
                        -Dsonar.host.url=%SONAR_HOST_URL% ^
                        -Dsonar.login=%SONAR_AUTH_TOKEN%
                    '''
                }
            }
        }
        stage('Run Python Script') {
            steps {
                bat '''
                call %VENV%\\Scripts\\activate
                python scrape_console.py
                '''
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
