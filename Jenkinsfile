pipeline {
    agent any

    stages {
        // **** Build - Test - Package katana-mngr container ****
        stage("katana-mngr-Build") {
            when {
                changeset "**/katana-mngr/**"
            }
            steps{
                echo "**** Building katana-mngr container ****"
            }
        }
        stage("katana-mngr-Test") {
            when {
                changeset "**/katana-mngr/**"
            }
            steps{
                echo "**** Testing katana-mngr container ****"
            }
        }

        // **** Build - Test - Package katana-nbi container ****
        stage("katana-nbi-Build") {
            when {
                changeset "**/katana-nbi/**"
            }
            steps{
                echo "**** Building katana-nbi container ****"
            }
        }
        stage("katana-nbi-Test") {
            when {
                changeset "**/katana-nbi/**"
            }
            steps{
                echo "**** Testing katana-nbi container ****"
            }
        }

        // **** Build - Test - Package katana-cli container ****
        stage("katana-cli-Build") {
            when {
                changeset "**/katana-cli/**"
            }
            steps{
                echo "**** Building katana-cli container ****"
            }
        }
        stage("katana-cli-Test") {
            when {
                changeset "**/katana-cli/**"
            }
            steps{
                echo "**** Testing katana-cli container ****"
            }
        }

        // TODO: Integration test
        // TODO: CD
        // TODO: Notification
        // TODO: Create new tag
    }
}