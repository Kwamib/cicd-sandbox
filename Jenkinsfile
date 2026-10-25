pipeline {
  agent any
  options {
    timeout(time: 15, unit: 'MINUTES')
    buildDiscarder(logRotator(numToKeepStr: '10'))
    disableConcurrentBuilds(abortPrevious: true)
  }
  environment {
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    PIP_NO_CACHE_DIR = '1'
    CI = 'true'
  }
  stages {
    stage('Checks') {
      parallel {
        stage('Lint') {
          agent {
            docker {
              image 'python:3.13-slim'
              reuseNode true
            }
          }
          steps {
            sh '''
              python -m venv .venv-lint
              . .venv-lint/bin/activate
              pip install --quiet -r requirements-lint.txt
              ruff check .
            '''
          }
        }
        stage('Tests') {
          steps {
            script {
              docker.image('postgres:17').withRun('--label sandbox-sidecar -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=visits_test') { pg ->
                docker.image('redis:7.2.7-alpine').withRun('--label sandbox-sidecar') { rd ->
                  docker.image('postgres:17').inside("--link ${pg.id}:db") {
                    sh 'until pg_isready -h db -U postgres; do sleep 1; done'
                  }
                  docker.image('python:3.13-slim').inside("--link ${pg.id}:db --link ${rd.id}:cache") {
                    sh '''
                      python -m venv .venv-test
                      . .venv-test/bin/activate
                      pip install --quiet -r requirements-dev.txt
                      export TEST_DATABASE_URL=postgresql://postgres:postgres@db:5432/visits_test
                      export REDIS_TEST_URL=redis://cache:6379/0
                      pytest -q -rs
                    '''
                  }
                }
              }
            }
          }
        }
      }
    }
    stage('Build') {
      steps {
        script {
          env.IMAGE_TAG = "1.0.${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
        }
        sh 'docker build -t cicd-sandbox:$IMAGE_TAG .'
        sh 'docker image ls cicd-sandbox'
        sh 'docker run --rm cicd-sandbox:$IMAGE_TAG "  Smoke Test "'
      }
    }
    stage('Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'ghcr', usernameVariable: 'GHCR_USER', passwordVariable: 'GHCR_TOKEN')]) {
          sh '''
            echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
            docker tag cicd-sandbox:$IMAGE_TAG ghcr.io/kwamib/cicd-sandbox-jenkins:$IMAGE_TAG
            docker push ghcr.io/kwamib/cicd-sandbox-jenkins:$IMAGE_TAG
          '''
        }
      }
    }
  }
  post {
    always {
      sh 'docker logout ghcr.io || true'
      sh 'docker ps -aq --filter label=sandbox-sidecar | xargs -r docker rm -f -v'
      sh 'docker image rm -f cicd-sandbox:$IMAGE_TAG ghcr.io/kwamib/cicd-sandbox-jenkins:$IMAGE_TAG 2>/dev/null || true'
    }
    cleanup {
      deleteDir()
    }
  }
}
