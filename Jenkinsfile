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
    }



        stage('Setup Python Environment') {
            steps {
                sh '''
                python3 -m venv $VENV
                source $VENV/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                source $VENV/bin/activate
                python manage.py test --noinput
                '''
            }
            post {
                always {
                    junit '**/test-results.xml'
                }
            }
        }

        stage('SonarQube Analysis') {
            environment {
                PATH = "${env.PATH}:${env.WORKSPACE}/$VENV/bin"
            }
            steps {
                withSonarQubeEnv('SonarQubeServer') {
                    sh '''
                    source $VENV/bin/activate
                    sonar-scanner \
                        -Dsonar.projectKey=ProjetIA \
                        -Dsonar.sources=. \
                        -Dsonar.language=python \
                        -Dsonar.host.url=$SONAR_HOST_URL \
                        -Dsonar.login=$SONAR_AUTH_TOKEN
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
