from __future__ import annotations

from common.core.config.bootstrap_settings import BootstrapSettings


class SandboxBootstrapSettings(BootstrapSettings):
    """沙箱 core 启动前即可读取的最小配置"""

    APP_NAME: str = "WisePen Sandbox Core Service"
    SERVICE_NAME: str = "wisepen-sandbox-service"
    SERVICE_PORT: int = 19915

    # 容器内访问 Docker host 发布端口的地址，由部署环境决定。
    SANDBOX_DOCKER_HOST: str | None = None


bootstrap_settings = SandboxBootstrapSettings()
