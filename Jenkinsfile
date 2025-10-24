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
            environment {
                PATH = "${env.PATH};${env.WORKSPACE}\\${env.VENV}\\Scripts"
            }
            steps {
                withSonarQubeEnv('sonar') {
                    bat '''
                    call %VENV%\\Scripts\\activate
                    sonar-scanner ^
                        -Dsonar.projectKey=ProjetIA ^
                        -Dsonar.sources=. ^
                        -Dsonar.language=python ^
                        -Dsonar.host.url=%SONAR_HOST_URL% ^
                        -Dsonar.login=%SONAR_AUTH_TOKEN%
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 1, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
}
