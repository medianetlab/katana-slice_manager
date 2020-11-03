pipeline {
    agent any

    environment {
        MAJOR_RELEASE="2.3"
        TAG_NUMBER="${MAJOR_RELEASE}.${BUILD_NUMBER}"
    }

    stages {
        // **** Build & Test katana-mngr container ****
        stage("katana-mngr-Build") {
            // when {
            //     changeset "**/katana-mngr/**"
            // }
            steps{
                echo "**** Building katana-mngr container ****"
                sh 'jenkins/build/service_build.sh katana-mngr'
            }
        }
        // Any katana-mngr unit tests should go here

        // **** Build & Test katana-nbi container ****
        stage("katana-nbi-Build") {
            // when {
            //     changeset "**/katana-nbi/**"
            // }
            steps{
                echo "**** Building katana-nbi container ****"
                sh 'jenkins/build/service_build.sh katana-nbi'
            }
        }
        // Any katana-nbi unit tests should go here

        // **** Build & Test katana-cli container ****
        stage("katana-cli-Build") {
            // when {
            //     changeset "**/katana-cli/**"
            // }
            steps{
                echo "**** Building katana-cli container ****"
                sh 'jenkins/build/service_build.sh katana-cli'
            }
        }
        // Any katana-cli unit tests should go here

        // **** Integration test ****
        stage("Integration_Test"){
            steps{
                echo "**** Running integration test ****"
                sh './build.sh'
                sh './start.sh'
                sh './jenkins/test/initial_test.sh'
                // sh 'stop.sh -c'
            }
        }
        // TODO: CD
        // TODO: Notification
        // TODO: Create new tag
    }
}