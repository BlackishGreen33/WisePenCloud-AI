pipeline {
    agent any

    environment {
        PROJECT_NAME = 'wisepencloud'
        DOCKER_REGISTRY = 'local'
        IMAGE_TAG = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
        COMPOSE_FILE_PATH = 'docker-compose-app.yml'
    }

    parameters {
        string(name: 'BRANCH_NAME', defaultValue: 'main', description: '选择需要构建的 Git 分支')
        string(name: 'PYPI_INDEX_URL', defaultValue: 'https://mirrors.aliyun.com/pypi/simple/', description: 'Python 包索引地址，默认使用中国大陆镜像')
        booleanParam(name: 'DEPLOY_CHAT_SERVICE', defaultValue: true, description: '构建并部署 chat-service')
        booleanParam(name: 'DEPLOY_MCP_SERVICE', defaultValue: true, description: '构建并部署 mcp-service')
        booleanParam(name: 'DEPLOY_SANDBOX_SERVICE', defaultValue: true, description: '构建并部署 sandbox-service')
        choice(name: 'SANDBOX_RUNTIME_TARGET', choices: ['LOCAL', 'REMOTE'], description: '沙箱容器运行位置；仅在部署 sandbox-service 时生效')
        string(name: 'SANDBOX_REMOTE_DOCKER_HOST', defaultValue: '', description: 'REMOTE 时必填，例如 tcp://10.0.0.22:2375')
        string(name: 'SANDBOX_REMOTE_HTTP_HOST', defaultValue: '', description: 'REMOTE 时必填，只填 IP 或主机名，例如 10.0.0.22')
    }

    stages {
        stage('1. 拉取代码 (Checkout)') {
            steps {
                echo "开始拉取 ${params.BRANCH_NAME} 分支代码..."
                checkout scm
                echo "代码拉取成功，当前构建版本 TAG: ${IMAGE_TAG}"
            }
        }

        stage('1.5 确认部署服务 (Select Services)') {
            steps {
                script {
                    def selectedServices = []
                    if (params.DEPLOY_CHAT_SERVICE) {
                        selectedServices << 'chat-service'
                    }
                    if (params.DEPLOY_MCP_SERVICE) {
                        selectedServices << 'mcp-service'
                    }
                    if (params.DEPLOY_SANDBOX_SERVICE) {
                        selectedServices << 'sandbox-service'
                    }
                    if (selectedServices.isEmpty()) {
                        error '至少需要选择一个要构建并部署的服务。'
                    }
                    env.SELECTED_COMPOSE_SERVICES = selectedServices.join(' ')
                    echo "本次选择构建并部署的服务: ${env.SELECTED_COMPOSE_SERVICES}"
                }
            }
        }

        stage('1.6 预检远程沙箱节点 (Preflight Remote Sandbox)') {
            when {
                expression {
                    return params.DEPLOY_SANDBOX_SERVICE && params.SANDBOX_RUNTIME_TARGET == 'REMOTE'
                }
            }
            steps {
                sh '''
                    set -eu

                    case "${SANDBOX_REMOTE_DOCKER_HOST}" in
                        tcp://*) ;;
                        *)
                            echo "SANDBOX_REMOTE_DOCKER_HOST 必须使用 tcp://host:port 格式"
                            exit 1
                            ;;
                    esac

                    remote_endpoint="${SANDBOX_REMOTE_DOCKER_HOST#tcp://}"
                    remote_docker_host="${remote_endpoint%:*}"
                    remote_docker_port="${remote_endpoint##*:}"
                    if [ -z "${remote_docker_host}" ] || [ "${remote_docker_host}" = "${remote_endpoint}" ]; then
                        echo "SANDBOX_REMOTE_DOCKER_HOST 缺少主机或端口"
                        exit 1
                    fi
                    case "${remote_docker_host}" in
                        *[!A-Za-z0-9.-]*)
                            echo "SANDBOX_REMOTE_DOCKER_HOST 的主机格式无效"
                            exit 1
                            ;;
                    esac
                    case "${remote_docker_port}" in
                        ''|*[!0-9]*)
                            echo "SANDBOX_REMOTE_DOCKER_HOST 的端口格式无效"
                            exit 1
                            ;;
                    esac
                    case "${SANDBOX_REMOTE_HTTP_HOST}" in
                        ''|*[!A-Za-z0-9.-]*)
                            echo "SANDBOX_REMOTE_HTTP_HOST 只能填写 IP 或主机名，不含协议和端口"
                            exit 1
                            ;;
                    esac

                    echo "检查远程 Docker API: ${SANDBOX_REMOTE_DOCKER_HOST}"
                    docker_daemon_id=$(docker --host "${SANDBOX_REMOTE_DOCKER_HOST}" info --format '{{.ID}}')

                    http_route_docker_host="tcp://${SANDBOX_REMOTE_HTTP_HOST}:${remote_docker_port}"
                    echo "检查沙箱 HTTP 主机到远程节点的网络路径: ${http_route_docker_host}"
                    http_route_daemon_id=$(docker --host "${http_route_docker_host}" info --format '{{.ID}}')

                    if [ -z "${docker_daemon_id}" ] || [ "${docker_daemon_id}" != "${http_route_daemon_id}" ]; then
                        echo "两个远程地址未连接到同一个 Docker daemon"
                        exit 1
                    fi
                    echo "远程沙箱节点预检通过，Docker daemon ID: ${docker_daemon_id}"
                '''
            }
        }

        stage('2. 构建 Docker 镜像') {
            failFast true

            parallel {
                stage('Chat Service') {
                    when {
                        expression { return params.DEPLOY_CHAT_SERVICE }
                    }
                    steps {
                        script {
                            sh """
                                docker build \\
                                    -t ${DOCKER_REGISTRY}/${PROJECT_NAME}-chat:${IMAGE_TAG} \\
                                    --build-arg SERVICE_DIR=wisepen-chat-service \\
                                    --build-arg SERVICE_PKG=chat \\
                                    --build-arg SERVICE_PORT=19904 \\
                                    --build-arg SERVICE_PROJECT=wisepen-chat-service \\
                                    --build-arg PYPI_INDEX_URL="\${PYPI_INDEX_URL}" \\
                                    -f Dockerfile .
                            """
                        }
                    }
                }
                stage('MCP Service') {
                    when {
                        expression { return params.DEPLOY_MCP_SERVICE }
                    }
                    steps {
                        script {
                            sh """
                                docker build \\
                                    -t ${DOCKER_REGISTRY}/${PROJECT_NAME}-mcp:${IMAGE_TAG} \\
                                    --build-arg SERVICE_DIR=wisepen-mcp-service \\
                                    --build-arg SERVICE_PKG=wisepen_mcp \\
                                    --build-arg SERVICE_PORT=19911 \\
                                    --build-arg SERVICE_PROJECT=wisepen-mcp-service \\
                                    --build-arg PYPI_INDEX_URL="\${PYPI_INDEX_URL}" \\
                                    -f Dockerfile .
                            """
                        }
                    }
                }
                stage('Sandbox Service') {
                    when {
                        expression { return params.DEPLOY_SANDBOX_SERVICE }
                    }
                    steps {
                        script {
                            sh """
                                docker build \\
                                    -t ${DOCKER_REGISTRY}/${PROJECT_NAME}-sandbox:${IMAGE_TAG} \\
                                    --build-arg SERVICE_DIR=wisepen-sandbox-service \\
                                    --build-arg SERVICE_PKG=sandbox \\
                                    --build-arg SERVICE_PORT=19915 \\
                                    --build-arg SERVICE_PROJECT=wisepen-sandbox-service \\
                                    --build-arg PYPI_INDEX_URL="\${PYPI_INDEX_URL}" \\
                                    -f Dockerfile .
                            """
                        }
                    }
                }

            }
        }

        stage('3. 部署 (Deploy)') {
            environment {
                NACOS_USER = credentials('nacos-username')
                NACOS_PWD  = credentials('nacos-password')
            }
            steps {
                script {
                    echo "开始部署最新版本: ${IMAGE_TAG}，服务: ${env.SELECTED_COMPOSE_SERVICES} ..."
                    sh """
                    if ! command -v docker-compose &> /dev/null; then
                        echo "容器内缺失 docker-compose，正在自动下载..."
                        curl -L -# -o /usr/local/bin/docker-compose "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)"
                        chmod +x /usr/local/bin/docker-compose
                    fi

                    export APP_VERSION=${IMAGE_TAG}
                    export DOCKER_REGISTRY=${DOCKER_REGISTRY}
                    export NACOS_USERNAME=\${NACOS_USER}
                    export NACOS_PASSWORD=\${NACOS_PWD}

                    if [ "\${DEPLOY_SANDBOX_SERVICE}" = "true" ]; then
                        case "\${SANDBOX_RUNTIME_TARGET}" in
                            LOCAL)
                                export SANDBOX_DOCKER_API_HOST="unix:///var/run/docker.sock"
                                export SANDBOX_DOCKER_HTTP_HOST="host.docker.internal"
                                ;;
                            REMOTE)
                                export SANDBOX_DOCKER_API_HOST="\${SANDBOX_REMOTE_DOCKER_HOST}"
                                export SANDBOX_DOCKER_HTTP_HOST="\${SANDBOX_REMOTE_HTTP_HOST}"
                                ;;
                            *)
                                echo "无效的 SANDBOX_RUNTIME_TARGET: \${SANDBOX_RUNTIME_TARGET}"
                                exit 1
                                ;;
                        esac
                        echo "沙箱容器运行位置: \${SANDBOX_RUNTIME_TARGET}"
                    fi

                    # 网络兼容
                    # 检测到遗留 cloud-infra_cloud-net 时叠加 legacy-net overlay
                    # 老中间件全部下线后，本脚本可以与docker-compose-app.legacy-net.yml文件、部署脚本中的探测分支一并删除
                    docker network create wisepen-net 2>/dev/null || true
                    COMPOSE_FILES="-f ${COMPOSE_FILE_PATH}"
                    if docker network inspect cloud-infra_cloud-net >/dev/null 2>&1; then
                        echo "检测到遗留网络 cloud-infra_cloud-net，叠加 docker-compose-app.legacy-net.yml"
                        COMPOSE_FILES="\$COMPOSE_FILES -f docker-compose-app.legacy-net.yml"
                    fi

                    docker-compose \$COMPOSE_FILES up -d --no-build --remove-orphans ${env.SELECTED_COMPOSE_SERVICES}

                    if [ "\${DEPLOY_SANDBOX_SERVICE}" = "true" ]; then
                        echo "验证 sandbox-service 的 Docker daemon 连接..."
                        docker exec wisepen-sandbox-service docker info --format 'Server={{.Name}} Docker={{.ServerVersion}} Containers={{.Containers}}'
                    fi
                    """
                }
            }
        }
    }

    post {
        always {
            echo "执行 Docker 垃圾回收..."
            sh 'docker image prune -f'
        }
        success {
            echo "构建与部署完成！版本: ${IMAGE_TAG}"
        }
        failure {
            echo "流水线执行失败，请检查 Jenkins 控制台报错日志！"
        }
    }
}
