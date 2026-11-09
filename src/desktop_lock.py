"""Cross-process exclusion for standalone Windows desktop workers."""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import sys

MUTEX_NAME = r'Local\DIALuxAgent.Desktop.v1'


@contextmanager
def desktop_lease(name=MUTEX_NAME):
    """Fail immediately if another cooperating worker owns the desktop.

    This does not prevent human input or other automation, and is not durable
    transaction/recovery evidence. Keep the handle alive for the entire operation.
    """
    if sys.platform != 'win32':
        raise ValueError('Desktop lease requires Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.ReleaseMutex.argtypes = [wintypes.HANDLE]
    kernel.ReleaseMutex.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateMutexW(None, False, name)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    acquired = False
    try:
        status = kernel.WaitForSingleObject(handle, 0)
        acquired = status in (0, 0x80)
        if status == 0x102:
            raise ValueError('DIALux desktop busy: another agent worker is active; no UI action attempted')
        if status == 0x80:
            raise ValueError('Previous desktop owner exited unexpectedly; inspect operation evidence before retry')
        if status != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        yield
    finally:
        if acquired:
            kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)
