def run_safe_powershell_command(script_or_command, root):
    """Executes a PowerShell snippet safely using the mapped binary path."""
    registry_path = os.path.join(root, ".cargo-doctor", "blueprints", "tools_registry.json")
    
    if not os.path.exists(registry_path):
        ps_bin = "powershell.exe"
    else:
        with open(registry_path, "r") as f:
            reg = json.load(f)
        ps_bin = reg.get("discovered", {}).get("powershell", {}).get("path", "powershell.exe")

    # Safe execution flags
    cmd = [
        ps_bin,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-Command", script_or_command
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr