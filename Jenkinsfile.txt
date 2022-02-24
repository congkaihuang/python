def git_url="git@github.com:congkaihuang/python.git"
def git_auth="4937f99f-e590-456e-abcb-73410c2172e0"
def projectname="build-test"
def tag="v2"
def register="47.103.2.253:5000" //harbor

pipeline {
    agent any

    stages {
        stage('clone code') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '*/dev']], extensions: [], userRemoteConfigs: [[credentialsId: "${git_auth}", url: "${git_url}"]]])
            }
        }


	    stage('build docker image , push to harbor')	{
        	steps {
	           sh """ 
                   docker build --no-cache -t ${projectname}:${tag} -f  Dockerfile .
                   docker tag ${projectname}:${tag} ${register}/gpu-team/${projectname}:${tag}
                   docker rmi ${projectname}:${tag}
                   docker login ${register} -u admin -p Harbor12345
                   docker push ${register}/gpu-team/${projectname}:${tag}
                   sed -i 's@app-name@${projectname}@g' test.yaml
                   sed -i 's@tag@${tag}@g' test.yaml
                   kubectl apply -f test.yaml
                   """
 			}
        }
}
}
