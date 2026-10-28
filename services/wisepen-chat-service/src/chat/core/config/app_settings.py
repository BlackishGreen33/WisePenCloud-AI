import asyncio
import threading

import yaml
from chat.core.config.nacos import nacos_client_manager
from chat.core.config.settings_models import ChatSettings
from common.logger import error, info


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


def load_settings() -> ChatSettings:
    try:
        info("nacos app config pulling.")
        raw_yaml = _run_async(nacos_client_manager.pull_config())
        config_dict = yaml.safe_load(raw_yaml) if raw_yaml else {}
        return ChatSettings.model_validate(config_dict or {})
    except Exception as e:
        error("nacos app config pull failed.", exc=e)
        raise


settings = load_settings()
