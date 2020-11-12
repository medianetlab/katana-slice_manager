pipeline {
    agent any

    environment {
        MAJOR_RELEASE="${sh(script:'git fetch --tags && git tag --sort version:refname | tail -1', returnStdout: true).trim()}"
        TAG_NUMBER="${MAJOR_RELEASE}.jenkins_${env.BRANCH_NAME}_${env.BUILD_NUMBER}"
        DOCKER_USER='mnlab'
        DOCKER_PASSWORD=credentials("mnlab_dockerhub")
    }

    stages {
        // *********************************
        // *** BUILD & UNIT TESTS STAGES ***
        // *********************************

        // **** Build & Test katana-mngr container ****
        stage("katana-mngr-Build") {
            when {
                changeset "**/katana-mngr/**"
            }
            steps{
                echo "**** Building katana-mngr container ****"
                sh 'jenkins/build/service_build.sh katana-mngr'
            }
        }
        // Any katana-mngr unit tests should go here

        // **** Build & Test katana-nbi container ****
        stage("katana-nbi-Build") {
            when {
                changeset "**/katana-nbi/**"
            }
            steps{
                echo "**** Building katana-nbi container ****"
                sh 'jenkins/build/service_build.sh katana-nbi'
            }
        }
        // Any katana-nbi unit tests should go here

        // **** Build & Test katana-cli container ****
        stage("katana-cli-Build") {
            when {
                changeset "**/katana-cli/**"
            }
            steps{
                echo "**** Building katana-cli container ****"
                sh 'jenkins/build/service_build.sh katana-cli'
            }
        }
        // Any katana-cli unit tests should go here

        // **** Build & Test katana-swagger container ****
        stage("katana-swagger-Build") {
            when {
                changeset "**/katana-swagger/**"
            }
            steps{
                echo "**** Building katana-swagger container ****"
                sh 'jenkins/build/service_build.sh katana-swagger'
            }
        }
        // Any katana-swagger unit tests should go here

        // **** Build & Test katana-prometheus container ****
        stage("katana-prometheus-Build") {
            when {
                changeset "**/katana-prometheus/**"
            }
            steps{
                echo "**** Building katana-prometheus container ****"
                sh 'jenkins/build/service_build.sh katana-prometheus'
            }
        }
        // Any katana-prometheus unit tests should go here

        // **** Build & Test katana-grafana container ****
        stage("katana-grafana-Build") {
            when {
                changeset "**/katana-grafana/**"
            }
            steps{
                echo "**** Building katana-grafana container ****"
                sh 'jenkins/build/service_build.sh katana-grafana'
            }
        }
        // Any katana-grafana unit tests should go here

        // **** Build & Test katana-nfv_mon container ****
        stage("katana-nfv_mon-Build") {
            when {
                changeset "**/katana-nfv_mon/**"
            }
            steps{
                echo "**** Building katana-nfv_mon container ****"
                sh 'jenkins/build/service_build.sh katana-nfv_mon'
            }
        }
        // Any katana-nfv_mon unit tests should go here

        // *******************************
        // *** INTEGRATION TESTS STAGE ***
        // *******************************

        // **** Integration test ****
        stage("Integration_Test"){
            steps{
                echo "**** Running integration test ****"
                sh './start.sh -m'
                sh './jenkins/test/initial_test.sh'
                sh './stop.sh -c'
            }
        }

        // *******************************
        // *** DOCKER IMAGE PUSH STAGE ***
        // *******************************

        // **** Push katana-mngr image ****
        stage("katana-mngr-Push") {
            when {
                changeset "**/katana-mngr/**"
                branch "master"
            }
            steps{
                echo "**** Pushing katana-mngr image to docker hub ****"
                sh 'jenkins/package/push_docker_image.sh -u ${DOCKER_USER} -p ${DOCKER_PASSWORD} -s katana-mngr -r ${TAG_NUMBER}'
            }
        }

        // **** Push katana-nbi image ****
        stage("katana-nbi-Push") {
            when {
                changeset "**/katana-nbi/**"
                branch "master"
            }
            steps{
                echo "**** Pushing katana-nbi image to docker hub ****"
                sh 'jenkins/package/push_docker_image.sh -u ${DOCKER_USER} -p ${DOCKER_PASSWORD} -s katana-nbi -r ${TAG_NUMBER}'
            }
        }

        // **** Push katana-cli image ****
        stage("katana-cli-Push") {
            when {
                changeset "**/katana-cli/**"
                branch "master"
            }
            steps{
                echo "**** Pushing katana-cli image to docker hub ****"
                sh 'jenkins/package/push_docker_image.sh -u ${DOCKER_USER} -p ${DOCKER_PASSWORD} -s katana-cli -r ${TAG_NUMBER}'
            }
        }

        // **** Push katana-swagger image ****
        stage("katana-swagger-Push") {
            when {
                changeset "**/katana-swagger/**"
                branch "master"
            }
            steps{
                echo "**** Pushing katana-swagger image to docker hub ****"
                sh 'jenkins/package/push_docker_image.sh -u ${DOCKER_USER} -p ${DOCKER_PASSWORD} -s katana-swagger -r ${TAG_NUMBER}'
            }
        }

        // **** Push katana-prometheus image ****
        stage("katana-prometheus-Push") {
            when {
                changeset "**/katana-prometheus/**"
                branch "master"
            }
            steps{
                echo "**** Pushing katana-prometheus image to docker hub ****"
                sh 'jenkins/package/push_docker_image.sh -u ${DOCKER_USER} -p ${DOCKER_PASSWORD} -s katana-prometheus -r ${TAG_NUMBER}'
            }
        }

        // **** Push katana-grafana image ****
        stage("katana-grafana-Push") {
            when {
                changeset "**/katana-grafana/**"
                branch "master"
            }
            steps{
                echo "**** Pushing katana-grafana image to docker hub ****"
                sh 'jenkins/package/push_docker_image.sh -u ${DOCKER_USER} -p ${DOCKER_PASSWORD} -s katana-grafana -r ${TAG_NUMBER}'
            }
        }

        // **** Push katana-nfv_mon image ****
        stage("katana-nfv_mon-Push") {
            when {
                changeset "**/katana-nfv_mon/**"
                branch "master"
            }
            steps{
                echo "**** Pushing katana-nfv_mon image to docker hub ****"
                sh 'jenkins/package/push_docker_image.sh -u ${DOCKER_USER} -p ${DOCKER_PASSWORD} -s katana-nfv_mon -r ${TAG_NUMBER}'
            }
        }

        // Uninstall to remove previous images
        stage("Remove_Images") {
            steps{
                sh './uninstall.sh'
            }
        }

        // TODO: CD
    }
    post{
        failure{
            slackSend (color: "#FF0000", message: "Job FAILED: '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }

        success{
            slackSend (color: "#008000", message: "Job SUCCESSFUL: '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL})")
        }
    }
}