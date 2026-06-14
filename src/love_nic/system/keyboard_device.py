"""Integracao com API nativa do Windows para controlar teclado interno."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

import wmi

from love_nic.config.constants import FALLBACK_KEYBOARD_ID

CR_SUCCESS = 0
DN_STARTED = 0x00000008
CM_PROB_DISABLED = 22

cfgmgr32 = ctypes.WinDLL("cfgmgr32.dll")

CM_Locate_DevNodeW = cfgmgr32.CM_Locate_DevNodeW
CM_Locate_DevNodeW.argtypes = [ctypes.POINTER(ctypes.c_ulong), wintypes.LPCWSTR, ctypes.c_ulong]
CM_Locate_DevNodeW.restype = ctypes.c_ulong

CM_Disable_DevNode = cfgmgr32.CM_Disable_DevNode
CM_Disable_DevNode.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
CM_Disable_DevNode.restype = ctypes.c_ulong

CM_Enable_DevNode = cfgmgr32.CM_Enable_DevNode
CM_Enable_DevNode.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
CM_Enable_DevNode.restype = ctypes.c_ulong

CM_Get_DevNode_Status = cfgmgr32.CM_Get_DevNode_Status
CM_Get_DevNode_Status.argtypes = [
    ctypes.POINTER(ctypes.c_ulong),
    ctypes.POINTER(ctypes.c_ulong),
    ctypes.c_ulong,
    ctypes.c_ulong,
]
CM_Get_DevNode_Status.restype = ctypes.c_ulong


def is_admin() -> bool:
    """Verifica se o processo atual possui privilegios de administrador."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_admin() -> None:
    """Relanca o aplicativo com privilegios elevados quando necessario."""
    if is_admin():
        return

    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()


def get_internal_keyboard_id() -> str | None:
    """Busca o ID do teclado nativo do notebook via WMI."""
    try:
        wmi_obj = wmi.WMI()
        for keyboard in wmi_obj.Win32_Keyboard():
            if keyboard.DeviceID.startswith("ACPI"):
                return keyboard.DeviceID
    except Exception as exc:
        print(f"Erro ao buscar teclado via WMI: {exc}")
    return None


def resolve_keyboard_id() -> str:
    """Retorna ID dinamico com fallback seguro."""
    keyboard_id = get_internal_keyboard_id()
    if keyboard_id:
        return keyboard_id

    print("Teclado ACPI nao encontrado dinamicamente. Usando fallback.")
    return FALLBACK_KEYBOARD_ID


def _get_dev_node(instance_id: str):
    dev_inst = ctypes.c_ulong(0)
    if CM_Locate_DevNodeW(ctypes.byref(dev_inst), instance_id, 0) == CR_SUCCESS:
        return dev_inst
    return None


def is_device_enabled(instance_id: str) -> bool:
    """Verifica se o dispositivo esta ativo na arvore de dispositivos do Windows."""
    dev_inst = _get_dev_node(instance_id)
    if dev_inst is None:
        return False

    status = ctypes.c_ulong(0)
    problem = ctypes.c_ulong(0)
    result = CM_Get_DevNode_Status(ctypes.byref(status), ctypes.byref(problem), dev_inst, 0)
    if result != CR_SUCCESS:
        return False

    if problem.value == CM_PROB_DISABLED:
        return False

    return bool(status.value & DN_STARTED)


def set_device_state(instance_id: str, enable: bool = True) -> bool:
    """Ativa ou desativa o dispositivo."""
    dev_inst = _get_dev_node(instance_id)
    if dev_inst is None:
        return False

    if enable:
        return CM_Enable_DevNode(dev_inst, 0) == CR_SUCCESS

    return CM_Disable_DevNode(dev_inst, 0) == CR_SUCCESS
