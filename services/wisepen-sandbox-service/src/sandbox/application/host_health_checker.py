from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import StrEnum

from sandbox.core.config.app_settings import settings


class PressureState(StrEnum):
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True)
class HostSnapshot:
    disk_usage: DiskUsageSnapshot
    state: PressureState

@dataclass(frozen=True)
class DiskUsageSnapshot:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float


class HostHealthChecker:

    def __init__(self) -> None:
        self._under_pressure = False

    def checker(self) -> HostSnapshot:
        return HostSnapshot(
            disk_usage=self.disk_uasge_checker(),
            state=PressureState.HIGH if self._under_pressure else PressureState.NORMAL,
        )

    def disk_uasge_checker(self) -> DiskUsageSnapshot:
        usage = shutil.disk_usage(settings.SANDBOX_DISK_CHECK_PATH)
        used_percent = usage.used * 100 / usage.total if usage.total else 100.0

        if self._under_pressure:
            self._under_pressure = not (
                used_percent < settings.SANDBOX_DISK_LOW_WATERMARK_PERCENT
                and usage.free > settings.SANDBOX_DISK_MIN_FREE_BYTES
            )
        else:
            self._under_pressure = (
                used_percent >= settings.SANDBOX_DISK_HIGH_WATERMARK_PERCENT
                or usage.free <= settings.SANDBOX_DISK_MIN_FREE_BYTES
            )

        return DiskUsageSnapshot(
            total_bytes=usage.total,
            used_bytes=usage.used,
            free_bytes=usage.free,
            used_percent=used_percent,
        )
