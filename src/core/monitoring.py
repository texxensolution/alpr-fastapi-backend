import psutil
from pydantic import BaseModel


class DiskUsage(BaseModel):
    percent: float
    used: int
    free: int
    total: int

    
class CpuUsage(BaseModel):
    avg_load: list[float]


class MemoryUsage(BaseModel):
    percent: float
    used: int
    free: int
    total: int
    

class SystemUsage(BaseModel):
    disk: DiskUsage
    cpu: CpuUsage
    memory: MemoryUsage


def get_disk_usage() -> DiskUsage:
    usage = psutil.disk_usage('/')
    return DiskUsage(
        percent=usage.percent,
        used=usage.used,
        free=usage.free,
        total=usage.total
    )


def get_cpu_usage() -> CpuUsage:
    return CpuUsage(avg_load=psutil.getloadavg())


def get_memory_usage() -> MemoryUsage:
    usage = psutil.virtual_memory()
    return MemoryUsage(
        percent=usage.percent,
        used=usage.used,
        free=usage.free,
        total=usage.total
    )


def get_system_usage() -> SystemUsage:
    return SystemUsage(
        disk=get_disk_usage(),
        cpu=get_cpu_usage(),
        memory=get_memory_usage()
    )