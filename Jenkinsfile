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
        stage('Audit') {
          agent {
            docker {
              image 'python:3.13-slim'
              reuseNode true
            }
          }
          steps {
            sh '''
              python -m venv .venv-audit
              . .venv-audit/bin/activate
              pip install --quiet -r requirements-audit.txt
              pip-audit --cache-dir .pip-audit-cache -r requirements-dev.txt
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
        script {
          env.IMAGE_TAG = "1.0.${env.BUILD_NUMBER}-${env.GIT_COMMIT.take(7)}"
        }
        sh 'docker build -t cicd-sandbox:$IMAGE_TAG .'
        sh 'docker image ls cicd-sandbox'
        sh 'docker run --rm cicd-sandbox:$IMAGE_TAG "  Smoke Test "'
      }
    }
    stage('Scan') {
      steps {
        sh '''
          docker save -o image.tar cicd-sandbox:$IMAGE_TAG
          docker run --rm -v "$WORKSPACE":/work -v trivy-cache:/root/.cache \
            aquasec/trivy@sha256:af6acf9a6b85dfe389a1941505c0ce9efef52a4719635e1a962f022a3d855daa \
            image --input /work/image.tar --quiet --skip-version-check --scanners vuln \
            --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1
        '''
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
    stage('Deploy') {
      when {
        expression { env.GIT_BRANCH == 'origin/main' }
      }
      steps {
        input message: 'Deploy this image to production?', ok: 'Deploy'
        sh '''
          REF=$(docker image inspect --format '{{index .RepoDigests 0}}' ghcr.io/kwamib/cicd-sandbox-jenkins:$IMAGE_TAG)
          echo "Deploying $REF"
          docker image rm cicd-sandbox:$IMAGE_TAG ghcr.io/kwamib/cicd-sandbox-jenkins:$IMAGE_TAG
          docker pull "$REF"
          docker run --rm "$REF" "  Jenkins Production "
        '''
      }
    }
  }
  post {
    always {
      sh 'docker logout ghcr.io || true'
    }
    cleanup {
      deleteDir()
    }
  }
}
