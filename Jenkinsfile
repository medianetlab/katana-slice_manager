pipeline {
    agent any

    stages {
        // **** Build & Test katana-mngr container ****
        stage("katana-mngr-Build") {
            // when {
            //     changeset "**/katana-mngr/**"
            // }
            steps{
                echo "**** Building katana-mngr container ****"
                sh 'docker-compose -f docker-compose.yaml build katana-mngr'
            }
        }
        stage("katana-mngr-Test") {
            // when {
            //     changeset "**/katana-mngr/**"
            // }
            steps{
                echo "**** Testing katana-mngr container ****"
            }
        }

        // **** Build & Test katana-nbi container ****
        stage("katana-nbi-Build") {
            // when {
            //     changeset "**/katana-nbi/**"
            // }
            steps{
                echo "**** Building katana-nbi container ****"
                sh 'docker-compose -f docker-compose.yaml build katana-nbi'
            }
        }
        stage("katana-nbi-Test") {
            // when {
            //     changeset "**/katana-nbi/**"
            // }
            steps{
                echo "**** Testing katana-nbi container ****"
            }
        }

        // **** Build & Test katana-cli container ****
        stage("katana-cli-Build") {
            // when {
            //     changeset "**/katana-cli/**"
            // }
            steps{
                echo "**** Building katana-cli container ****"
                sh 'docker-compose -f docker-compose.yaml build katana-cli'
            }
        }
        stage("katana-cli-Test") {
            // when {
            //     changeset "**/katana-cli/**"
            // }
            steps{
                echo "**** Testing katana-cli container ****"
            }
        }

        // **** Integration test ****
        stage("Integration_Test"){
            steps{
                echo "**** Running integration test ****"
                sh 'start.sh'
                sh 'jenkins/test/initial_test.sh'
                sh 'stop.sh -c'
            }
        }
        // TODO: CD
        // TODO: Notification
        // TODO: Create new tag
    }
}