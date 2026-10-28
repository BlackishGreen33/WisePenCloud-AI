import asyncio
import threading

import yaml
from common.logger import error, info
from sandbox.core.config.nacos import nacos_client_manager
from sandbox.core.config.settings_models import SandboxSettings


def _run_async(coro):
    """在新线程的独立事件循环中执行协程，兼容 uvicorn 启动时已有运行中事件循环的场景。"""
    result, exc = None, None

    def _target():
        nonlocal result, exc
        try:
            result = asyncio.run(coro)
        except Exception as e:  # noqa: BLE001
            exc = e

    t = threading.Thread(target=_target)
    t.start()
    t.join()
    if exc:
        raise exc
    return result


def load_settings() -> SandboxSettings:
    """从 Nacos 拉取并校验 Sandbox 运行配置。"""

    try:
        # 当前服务启动严格依赖 Nacos 配置；拉取失败直接暴露启动错误。
        info("nacos app config pulling.")
        raw_yaml = _run_async(nacos_client_manager.pull_config())
        config_dict = yaml.safe_load(raw_yaml) if raw_yaml else {}
        return SandboxSettings.model_validate(config_dict or {})
    except Exception as e:
        error("nacos app config pull failed.", exc=e)
        raise


settings = load_settings()
