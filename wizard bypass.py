import json

DEFAULT_EXPECTED_LOCATIONS = {
    "cargo-nextest": ["~/.cargo/bin/cargo-nextest.exe", "~/.cargo/bin/cargo-nextest"],
    "cargo-audit": ["~/.cargo/bin/cargo-audit.exe", "~/.cargo/bin/cargo-audit"],
    "maturin": ["~/.local/bin/maturin", "C:\\Python312\\Scripts\\maturin.exe"],
    "pwsh_module_pester": ["Documents/PowerShell/Modules/Pester"]
}

def scan_or_register_tools(root, wizard_choices=None):
    """Scans system for required third-party tools. 
    If found, registers paths and bypasses installation.
    """
    registry_path = os.path.join(root, ".cargo-doctor", "blueprints", "tools_registry.json")
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    
    registry = {"discovered": {}, "bypassed_installs": [], "missing": []}
    
    # 1. Check PowerShell availability
    ps_info = locate_powershell_executable()
    if ps_info:
        registry["discovered"]["powershell"] = ps_info

    # 2. Check third-party tools and crates
    for tool, expected_list in DEFAULT_EXPECTED_LOCATIONS.items():
        # First check system $PATH
        found_path = shutil.which(tool)
        
        # Second, check expected filesystem locations
        if not found_path:
            for loc in expected_list:
                expanded = os.path.expanduser(loc)
                if os.path.exists(expanded):
                    found_path = expanded
                    break

        if found_path:
            registry["discovered"][tool] = {"path": found_path, "status": "trusted_existing"}
            registry["bypassed_installs"].append(tool)
            print(f"\033[32m[✔] Discovered {tool} at {found_path} (Skipping install)\033[0m")
        else:
            registry["missing"].append(tool)
            print(f"\033[33m[!] {tool} not found on host machine.\033[0m")

    # Save mapping for pipeline execution
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
        
    return registry