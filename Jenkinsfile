pipeline {
  agent any
  options {
    timeout(time: 15, unit: 'MINUTES')
  }
  environment {
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    PIP_NO_CACHE_DIR = '1'
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
              pip install --quiet ruff
              ruff check .
            '''
          }
        }
        stage('Tests') {
          steps {
            script {
              docker.image('postgres:17').withRun('-e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=visits_test') { pg ->
                docker.image('redis:7.2.7-alpine').withRun() { rd ->
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
        echo "Would build an image for build ${env.BUILD_NUMBER}"
      }
    }
  }
}
