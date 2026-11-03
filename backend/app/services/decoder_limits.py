"""Per-process admission and Linux decoder limits, not an exploit sandbox."""
import ctypes
import resource
from threading import BoundedSemaphore

decoder_slot = BoundedSemaphore(1)


def worker_limits(memory_mb, cpu_seconds, file_bytes):
    resource.setrlimit(resource.RLIMIT_AS, (memory_mb*1024*1024,)*2)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds,)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes,)*2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    # Prevent setuid/file capabilities granting new privileges to OCR children.
    # This neither denies filesystem access nor filters syscalls/network access.
    if ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) != 0:
        raise OSError('Decoder privilege restriction unavailable')
