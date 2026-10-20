from common.core.domain import IErrorCode


class SandboxErrorCode(IErrorCode):

    POOL_EMPTY = (46001, "沙箱池中没有可用的 READY 容器")
    DOCKER_RUNTIME_FAILED = (46002, "docker 命令运行错误")
    SANDBOX_UNAVAILABLE = (46003, "沙箱不可用")
    SANDBOX_BUSY = (46004, "沙箱忙，请重试")
    TASK_UNAVAILABLE = (46005, "任务不可用")
