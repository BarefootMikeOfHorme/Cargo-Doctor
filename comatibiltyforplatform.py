import shutil
import platform
import os
import subprocess

def locate_powershell_executable():
    """Locates the safest, most performant PowerShell binary available."""
    is_wsl = "microsoft-standard" in platform.uname().release.lower()
    
    # Priority order for PowerShell runtimes
    candidates = ["pwsh", "pwsh.exe", "powershell.exe"]
    
    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return {"binary": candidate, "path": path, "is_wsl": is_wsl}

    # WSL Fallback: Reach into the Windows host filesystem if not on WSL $PATH
    if is_wsl:
        wsl_win_ps = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
        if os.path.exists(wsl_win_ps):
            return {"binary": "powershell.exe", "path": wsl_win_ps, "is_wsl": True}

    return None