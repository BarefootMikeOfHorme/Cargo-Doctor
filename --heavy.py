def generate_alias_scripts(root, env_map):
    """Generates shell scripts to instantly bind terminal sessions to the trusted toolchain."""
    alias_dir = os.path.join(root, DOCTOR_DIR, "aliases")
    os.makedirs(alias_dir, exist_ok=True)
    
    tools = env_map.get("discovered_tools", {})
    
    # 1. Generate bash/WSL alias script
    sh_path = os.path.join(alias_dir, "trusted_env.sh")
    with open(sh_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Source this file to bind terminal to Cargo Doctor trusted paths\n\n")
        if "python3.12" in tools:
            f.write(f"export PYTHON_SYS_EXECUTABLE='{tools['python3.12']['path']}'\n")
            f.write(f"alias python='{tools['python3.12']['path']}'\n")
    
    # 2. Generate PowerShell alias script
    ps1_path = os.path.join(alias_dir, "trusted_env.ps1")
    with open(ps1_path, "w") as f:
        f.write("# Run this file to bind PowerShell to Cargo Doctor trusted paths\n\n")
        if "python3.12" in tools:
            f.write(f"$env:PYTHON_SYS_EXECUTABLE = '{tools['python3.12']['path']}'\n")
            f.write(f"Set-Alias -Name python -Value '{tools['python3.12']['path']}'\n")
            
    print(f"{GREEN}  [✔] Generated terminal alias scripts in {alias_dir}{RESET}")