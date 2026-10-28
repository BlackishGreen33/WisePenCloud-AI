from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from common.core.exceptions import ServiceException

from sandbox.application.container_manager import ContainerManager
from sandbox.core.config.app_settings import settings
from sandbox.domain.error_codes import SandboxErrorCode


class PressureState(StrEnum):
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True)
class HostSnapshot:
    disk_usage: DiskUsageSnapshot
    cpu_usage_percent: float
    disk_state: PressureState
    cpu_state: PressureState

    @property
    def state(self) -> PressureState:
        return (
            PressureState.HIGH
            if self.disk_state == PressureState.HIGH or self.cpu_state == PressureState.HIGH
            else PressureState.NORMAL
        )


@dataclass(frozen=True)
class DiskUsageSnapshot:
    total_bytes: int
    used_bytes: int
    free_bytes: int
    used_percent: float


class HostHealthChecker:


    # 该脚本在 DOCKER_HOST 指向的 daemon 上运行
    _HOST_RESOURCE_PROBE_SCRIPT = r"""
# df 统计 $2 所在文件系统的容量
df -Pk "$2" | awk 'END { printf "DISK %s %s %s\n", $2, $3, $4 }'

# 从宿主机 /proc/stat 的 cpu 汇总行读取累计总时间与累计空闲时间
read_cpu() {
    # 累加 user 到 steal 字段；guest 和 guest_nice 已包含在 user/nice 中，不重复计算
    awk '$1 == "cpu" { total = 0; for (i = 2; i <= 9; i++) total += $i; idle = $5 + $6; printf "%.0f %.0f\n", total, idle }' /host-proc-stat
}

# 保存调用方传入的采样时间，避免后续 set -- 覆盖位置参数后丢失
sample_seconds=$1
# 读取自系统启动以来的累计 CPU 计数
set -- $(read_cpu)
# 保存第一次采样的累计总时间
total_before=$1
# 保存第一次采样的累计空闲时间
idle_before=$2
# 等待一个采样窗口，使两次累计计数之间产生可计算的差值
sleep "$sample_seconds"
# 第二次读取累计 CPU 计数，并重新写入位置参数
set -- $(read_cpu)
# 两次累计总时间之差表示采样窗口内所有 CPU 核心经过的时间
total_delta=$(($1 - total_before))
# 两次累计空闲时间之差表示采样窗口内未被使用的 CPU 时间
idle_delta=$(($2 - idle_before))
# 拒绝倒退、无增量或空闲时间大于总时间的异常计数，避免产生无意义的百分比
if [ "$total_delta" -le 0 ] || [ "$idle_delta" -lt 0 ] || [ "$idle_delta" -gt "$total_delta" ]; then
    echo "invalid host CPU counters" >&2
    exit 1
fi
# CPU 使用率 = 采样窗口内的非空闲时间 / 总时间。
awk -v total="$total_delta" -v idle="$idle_delta" 'BEGIN { printf "CPU %.2f\n", (total - idle) * 100 / total }'
"""

    def __init__(self, container_manager: ContainerManager) -> None:
        self._container_manager = container_manager
        self._disk_under_pressure = False
        self._cpu_under_pressure = False

    async def checker(self) -> HostSnapshot:
        disk_usage, cpu_usage_percent = await self._probe_host()
        self._update_disk_pressure(disk_usage)
        self._update_cpu_pressure(cpu_usage_percent)
        return HostSnapshot(
            disk_usage=disk_usage,
            cpu_usage_percent=cpu_usage_percent,
            disk_state=PressureState.HIGH if self._disk_under_pressure else PressureState.NORMAL,
            cpu_state=PressureState.HIGH if self._cpu_under_pressure else PressureState.NORMAL,
        )

    async def _probe_host(self) -> tuple[DiskUsageSnapshot, float]:
        """采集当前 Docker daemon 宿主机的容器存储空间与 CPU 使用情况"""

        # 第一个挂载把 daemon 宿主机的容器存储目录映射到探针容器的 /probe
        storage_mount = (
            f"type=bind,source={settings.resource_protection.host_container_storage_path},"
            "target=/probe,readonly"
        )
        # 第二个挂载提供宿主机 CPU 累计计数，避免误读探针容器自身的 /proc/stat
        cpu_stat_mount = "type=bind,source=/proc/stat,target=/host-proc-stat,readonly"

        # docker run 创建一次性探针容器
        args = [
            "run",
            # 脚本退出后自动删除探针容器，避免产生停止状态的容器残留
            "--rm",
            # 资源采集不需要联网，禁用网络可缩小探针权限和攻击面
            "--network", "none",
            # 根文件系统只读；宿主机的两个挂载也分别显式声明为只读
            "--read-only",
            # 探针只需执行 df、awk、sleep 和读取文件，不需要 Linux capabilities
            "--cap-drop", "ALL",
            # 禁止探针进程及其子进程通过 setuid/setgid 等方式获取额外权限
            "--security-opt", "no-new-privileges=true",
            # 挂载 daemon 宿主机上的容器存储目录，用于查询承载它的文件系统
            "--mount", storage_mount,
            # 挂载 daemon 宿主机的 CPU 累计计数文件，用于两次采样
            "--mount", cpu_stat_mount,
            # 使用 shell 执行内嵌的组合探针脚本
            "--entrypoint", "sh",
            # 镜像必须提供 POSIX shell、df、awk 与 sleep；默认使用 BusyBox
            settings.resource_protection.probe_image,
            # 告诉 shell 从下一个参数读取脚本文本
            "-c", self._HOST_RESOURCE_PROBE_SCRIPT,
            # sh -c 后的第一个参数作为 $0，仅用于标识脚本名称
            "host-resource-probe",
            # 脚本的 $1，控制两次 /proc/stat 采样之间的等待时间
            str(settings.resource_protection.cpu.sample_seconds),
            # 脚本的 $2，是容器内用于执行 df 的挂载点
            "/probe",
        ]

        # 执行 Docker CLI；REMOTE 模式下 Docker 客户端通过 DOCKER_HOST 调用远端 daemon
        returncode, stdout, stderr = await self._container_manager.run_docker_command(*args)

        # 非零退出码表示镜像、挂载、脚本或 daemon 调用失败
        if returncode != 0:
            raise ServiceException(
                SandboxErrorCode.DOCKER_RUNTIME_FAILED,
                "docker host resource probe failed: "
                f"exit_code={returncode}, stdout={stdout!r}, stderr={stderr!r}",
            )

        # DISK 行解析为三个 KiB 数值；None 表示尚未收到合法格式的行
        disk_fields: list[str] | None = None
        # CPU 行解析为浮点百分比；None 表示缺失或无法转换
        cpu_usage_percent: float | None = None

        # 逐行解析脚本的稳定输出协议，忽略无法识别的额外输出
        for line in stdout.splitlines():
            # 按空白切分，兼容 BusyBox 输出中的连续空格
            fields = line.split()
            # DISK 后应当依次是文件系统总量、已用量和可用量
            if fields and fields[0] == "DISK":
                disk_fields = fields[1:]
            # CPU 后只允许一个使用率字段
            elif fields and fields[0] == "CPU" and len(fields) == 2:
                try:
                    # 将 shell 输出的百分比转换为 Python 浮点数。
                    cpu_usage_percent = float(fields[1])
                except ValueError:
                    cpu_usage_percent = None

        # 磁盘协议必须且只能提供三个数值字段
        if disk_fields is None or len(disk_fields) != 3:
            raise ServiceException(
                SandboxErrorCode.DOCKER_RUNTIME_FAILED,
                f"docker host disk probe returned unexpected output: {stdout!r}",
            )
        try:
            # df -P -k 以 KiB 返回总量、已用量和可用量
            total_kib, used_kib, free_kib = map(int, disk_fields)
        except ValueError as exc:
            # 任一字段不是整数都说明输出协议不可用
            raise ServiceException(
                SandboxErrorCode.DOCKER_RUNTIME_FAILED,
                f"docker host disk probe returned invalid sizes: {stdout!r}",
            ) from exc
        # 总量必须为正数，已用量与可用量不能为负数
        if total_kib <= 0 or used_kib < 0 or free_kib < 0:
            raise ServiceException(
                SandboxErrorCode.DOCKER_RUNTIME_FAILED,
                f"docker host disk probe returned invalid sizes: {stdout!r}",
            )
        # CPU 使用率必须存在，并落在闭区间 [0, 100]
        if cpu_usage_percent is None or not 0 <= cpu_usage_percent <= 100:
            raise ServiceException(
                SandboxErrorCode.DOCKER_RUNTIME_FAILED,
                f"docker host CPU probe returned invalid usage: {stdout!r}",
            )

        # 将 df 返回的 KiB 统一换算为领域对象使用的字节数
        total_bytes = total_kib * 1024
        used_bytes = used_kib * 1024
        free_bytes = free_kib * 1024
        disk_usage = DiskUsageSnapshot(
            total_bytes=total_bytes,
            used_bytes=used_bytes,
            free_bytes=free_bytes,
            used_percent=used_bytes * 100 / total_bytes,
        )
        # 返回同一采样轮次的磁盘与 CPU 指标
        return disk_usage, cpu_usage_percent

    def _update_disk_pressure(self, usage: DiskUsageSnapshot) -> None:
        # 已处于高压时，必须同时低于低水位且恢复最小剩余空间才解除
        if self._disk_under_pressure:
            self._disk_under_pressure = not (
                usage.used_percent < settings.resource_protection.disk.low_watermark_percent
                and usage.free_bytes > settings.resource_protection.disk.min_free_bytes
            )
        # 正常状态下，达到高水位或剩余空间不足任一条件即进入高压
        else:
            self._disk_under_pressure = (
                usage.used_percent >= settings.resource_protection.disk.high_watermark_percent
                or usage.free_bytes <= settings.resource_protection.disk.min_free_bytes
            )

    def _update_cpu_pressure(self, usage_percent: float) -> None:
        # 已处于高压时，CPU 必须回落到低水位以下才解除高压
        if self._cpu_under_pressure:
            self._cpu_under_pressure = usage_percent >= settings.resource_protection.cpu.low_watermark_percent
        # 正常状态下，CPU 达到高水位才进入高压
        else:
            self._cpu_under_pressure = usage_percent >= settings.resource_protection.cpu.high_watermark_percent
