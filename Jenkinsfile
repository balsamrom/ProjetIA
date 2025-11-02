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

        stage('Run Python Script') {
            steps {
                withCredentials([string(credentialsId: 'jenkins-auth', variable: 'JENKINS_AUTH')]) {
                    bat '''
                    call venv\\Scripts\\activate
                    python scrape_console.py
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

        
       
    }
}
