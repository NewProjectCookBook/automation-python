def buildInfo
def additionalMarks
def tagsTO
pipeline {
    agent {
        label 'Autotests'
    }
    options {
        timestamps()
    }
    environment {
        serverId = 'default'
		pathToConfig = "project\\configs"
    }
    stages {
        stage ('GIT') {
            steps {
                    checkout(
                        [$class: 'GitSCM',
                        branches: [[name: "refs/heads/${env.branch}"]],
                        doGenerateSubmoduleConfigurations: false,
                        extensions: [
                            [$class: 'CleanBeforeCheckout'],
                            [$class: 'CloneOption', honorRefspec: true, noTags: true, reference: '', shallow: false, timeout: 20],
                            [$class: 'SparseCheckoutPaths', sparseCheckoutPaths: [[path: 'project/']]]
                            ],
                            submoduleCfg: [],
                            userRemoteConfigs: [[
                                credentialsId: 'bitbucket_cf',
                                refspec: "+refs/heads/${env.branch}:refs/remotes/origin/${env.branch}",
                                url: 'ssh://git@host/project.git'
                                ]]]
                    )
            }
        }
        stage ('Set build info') {
            steps {
                script {
                    def config = readJSON file: "${env.pathToConfig}\\${env.envstand}"
                    buildInfo = httpRequest(url: "http://${config['cache_host']}/endpoint", customHeaders: [[name:'iv-user', value:"user_login"]]).content.replaceAll("^\\{|\\}","")
                    tagsTO = "${env.branch}, ${env.envstand}, ${buildInfo}".replaceAll('"','')
                }
            }

        }
        stage ('filtering domains') {
            steps {
                script {
                    def sep = " and not "
                    def tempMarks = params.findAll{it.key.startsWith('d') && !it.value}?.collect{"$it.key".drop(1)} join sep
                    if (tempMarks) {
                         additionalMarks = sep + tempMarks.toLowerCase()  
                    }
                    else {
                        additionalMarks = ""
                    }
                }
            }
        }
        stage ('Restarting of Setup Module') {
             when {
                expression {
                    return env.ALLURE_JOB_RUN_ID;
                }
            }
            steps {
                catchError(buildResult: currentBuild.currentResult, stageResult: 'FAILURE') {
                    withAllureUpload(projectId: env.project_id, results: [[path: 'target/allure-results']], serverId: env.serverId, tags: tagsTO) {
                    powershell script: "python -m pytest -s -v --stand=${env.envstand} --browser=${env.browser} --auth-type=${env.authorization} --alluredir=target/allure-results project/team/ -m \"test_data ${additionalMarks}\" -k \"not test_enable_consolidation\""
                    }
                }
            }
        }
        stage ('Setup Module') {
             when {
                expression {
                    return !env.ALLURE_JOB_RUN_ID;
                }
            }
            steps {
                withAllureUpload(projectId: env.project_id, results: [[path: 'target/allure-results']], serverId: env.serverId, tags: tagsTO) {
                powershell script: "python -m pytest -s -v --stand=${env.envstand} --browser=${env.browser} --auth-type=${env.authorization} --alluredir=target/allure-results project/team/ -m \"test_data ${additionalMarks}\" -k \"not test_enable_consolidation\""
                }
            }
        }
        stage ('Run Autotests') {
            options {
                timeout(time: 3, unit: 'HOURS')
            }
            parallel {
                stage ('Run smoke dependent tests') {
                    steps {
                        catchError(buildResult: currentBuild.currentResult, stageResult: 'FAILURE') {
                            withAllureUpload(projectId: env.project_id, results: [[path: 'target/allure-results']], serverId: env.serverId, tags: tagsTO) {
                                powershell script: "python -m pytest -s -v --stand=${env.envstand} --browser=${env.browser} --auth-type=${env.authorization} --alluredir=target/allure-results project/team/ -m \"(dependent or excel) and not test_data and not consolidation ${additionalMarks}\""
                            }
                        }
                    }
                }
                stage ('Run smoke independent tests') {
                    steps {
                        catchError(buildResult: currentBuild.currentResult, stageResult: 'FAILURE') {
                            withAllureUpload(projectId: env.project_id, results: [[path: 'target/allure-results']], serverId: env.serverId, tags: tagsTO) {
                                powershell script: "python -m pytest -s -v --stand=${env.envstand} --browser=${env.browser} --auth-type=${env.authorization} --alluredir=target/allure-results project/team/ -m \"not dependent and not excel and not test_data and not consolidation ${additionalMarks}\" -n 4"
                            }
                        }
                    }
                }
            }
        }
        stage ('Consolidation Unit') {
            options {
                timeout(time: 3, unit: 'HOURS')
            }
            when {
                environment name: 'withConsolidation', value: 'true'
            }
            stages {
                stage ('Setup Cons') {
                    steps {
                        catchError(buildResult: currentBuild.currentResult, stageResult: 'FAILURE') {
                            withAllureUpload(projectId: env.project_id, results: [[path: 'target/allure-results']], serverId: env.serverId, tags: tagsTO) {
                                powershell script: "python -m pytest -s -v --stand=${env.envstand} --browser=${env.browser} --auth-type=${env.authorization} --alluredir=target/allure-results project/team/Setup_Modules/test_enable_consolidation.py"
                            }
                        }
                    }
                }
                stage ('Run cons tests') {
                    steps {
                        catchError(buildResult: currentBuild.currentResult, stageResult: 'FAILURE') {
                            withAllureUpload(projectId: env.project_id, results: [[path: 'target/allure-results']], serverId: env.serverId, tags: tagsTO) {
                                powershell script: "python -m pytest -s -v --stand=${env.envstand} --browser=${env.browser} --auth-type=${env.authorization} --alluredir=target/allure-results project/team/ -m \"consolidation and not test_data ${additionalMarks}\" -n 4"
                            }
                        }
                    }
                }
            }
        }
    }
    post('Generate allure in Jenkins') {
        always {
             allure commandline: '2.7.0', includeProperties: false, jdk: '', results: [[path: 'target/allure-results'], [path: 'TFS_allure-results']]
             cleanWs()
        }

    }
}