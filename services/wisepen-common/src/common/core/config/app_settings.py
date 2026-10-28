from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _to_kebab_case(field_name: str) -> str:
    return field_name.replace("_", "-")


class ConfigModel(BaseModel):
    """Nacos 业务配置模型基类。"""

    model_config = ConfigDict(
        alias_generator=_to_kebab_case,
        extra="forbid",
        validate_by_alias=True,
        validate_by_name=False,
    )


class InternalSecuritySettings(ConfigModel):
    from_source_secret: str = Field(min_length=1)


class RpcSettings(ConfigModel):
    lb_strategy: Literal["weighted_random", "round_robin", "random"] = "weighted_random"
    default_timeout_seconds: float = Field(default=5.0, gt=0)
    default_retries: int = Field(default=2, ge=0)


class ServiceDiscoverySettings(ConfigModel):
    cache_ttl_seconds: float = Field(default=30.0, gt=0)
