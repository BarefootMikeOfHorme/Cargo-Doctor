import platform

def suggest_and_fix_dependencies(error_text, auto_run=False):
    """Maps missing system commands/libraries to their installation fixes."""
    print(f"\n{CYAN}➜{RESET} Analyzing build failure for missing system dependencies...")
    
    is_windows = os.name == 'nt'
    is_wsl = "microsoft-standard" in platform.uname().release.lower()
    
    # Common PyO3 / Rust / System dependency errors and their fixes
    resolution_map = {
        "linker `cc` not found": {
            "windows": "winget install -e --id Microsoft.VisualStudio.2022.BuildTools",
            "linux": "sudo apt-get install build-essential"
        },
        "cmake: command not found": {
            "windows": "winget install -e --id Kitware.CMake",
            "linux": "sudo apt-get install cmake"
        },
        "No module named 'maturin'": {
            "windows": "python -m pip install maturin",
            "linux": "python3 -m pip install maturin"
        },
        "pkg-config not found": {
            "windows": "choco install pkgconfiglite",
            "linux": "sudo apt-get install pkg-config"
        },
        "libssl-dev": {
            "windows": "winget install -e --id ShiningLight.OpenSSL",
            "linux": "sudo apt-get install libssl-dev"
        }
    }

    found_fixes = []
    for error_trigger, commands in resolution_map.items():
        if error_trigger in error_text:
            cmd = commands["windows"] if is_windows else commands["linux"]
            found_fixes.append((error_trigger, cmd))

    if not found_fixes:
        print(f"{DIM}No known system dependency fixes identified for this error.{RESET}")
        return False

    print(f"{YELLOW}💡 Missing System Dependencies Detected!{RESET}")
    for trigger, cmd in found_fixes:
        print(f"  Missing: {BOLD}{trigger}{RESET}")
        print(f"  Command: {GREEN}{cmd}{RESET}")
        
        if auto_run:
            # Interactive Guardrail
            resp = input(f"\nExecute `{cmd}` now? [Y/n]: ").strip().lower()
            if resp in ['', 'y', 'yes']:
                subprocess.run(cmd.split(), check=False)
                print(f"{GREEN}[✔] Attempted installation. You may need to restart the script.{RESET}")
            else:
                print(f"{DIM}Skipped.{RESET}")
                
    return True