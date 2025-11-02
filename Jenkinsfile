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

        stage('Setup Python Environment') {
            steps {
                bat '''
                python -m venv %VENV%
                call %VENV%\\Scripts\\activate
                python -m pip install --upgrade pip
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

        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
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
}
