def validate_requirements(root, auto_update=False):
    """Validates and synchronizes both Rust (Cargo) and Python (Pip) dependency graphs."""
    print(f"\n{CYAN}{BOLD}=== DEPENDENCY & REQUIREMENTS SYNC ==={RESET}")
    
    # 1. RUST: Cargo Lockfile & Outdated Check
    print(f"{CYAN}➜{RESET} Checking Rust dependencies (Cargo.toml)...")
    if auto_update:
        print(f"{DIM}  Running `cargo update` to refresh Cargo.lock...{RESET}")
        subprocess.run(["cargo", "update"], cwd=root)
        print(f"{GREEN}  [✔] Cargo.lock synchronized.{RESET}")
    
    # Check for cargo-outdated (optional power-user tool)
    has_outdated = subprocess.run(["cargo", "outdated", "--help"], capture_output=True).returncode == 0
    if has_outdated:
        print(f"{DIM}  Scanning for stale crates...{RESET}")
        res = subprocess.run(["cargo", "outdated"], capture_output=True, text=True, cwd=root)
        if "Outdated dependencies:" in res.stdout:
            print(f"{YELLOW}  [!] Outdated Rust crates detected:{RESET}\n{res.stdout}")
        else:
            print(f"{GREEN}  [✔] All Rust dependencies are up to date.{RESET}")
    else:
        print(f"{DIM}  (Install `cargo-outdated` for deep version tracking: `cargo install cargo-outdated`){RESET}")

    # 2. PYTHON: PyO3 Binding Validation
    print(f"\n{CYAN}➜{RESET} Checking Python bindings and virtual environment...")
    req_file = os.path.join(root, "requirements.txt")
    
    if os.path.exists(req_file):
        print(f"{DIM}  Found requirements.txt. Validating against active Python environment...{RESET}")
        
        # Get installed pip packages
        installed = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"], 
            capture_output=True, text=True
        ).stdout.lower()

        with open(req_file, 'r') as f:
            required = [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]

        missing = []
        for req in required:
            # Strip version pinning (==, >=, ~=) for a basic presence check
            base_pkg = re.split(r'[=><~]', req)[0]
            if base_pkg not in installed:
                missing.append(req)

        if missing:
            print(f"{RED}  [✖] Missing Python dependencies required for bindings:{RESET}")
            for m in missing:
                print(f"      - {m}")
            
            if auto_update:
                print(f"\n{YELLOW}  Auto-installing missing Python packages...{RESET}")
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file])
                print(f"{GREEN}  [✔] Python environment synced.{RESET}")
            else:
                print(f"\n{YELLOW}  💡 Hint: Run with `--requirements --fix` to auto-install.{RESET}")
        else:
            print(f"{GREEN}  [✔] Python environment matches requirements.txt.{RESET}")
    else:
        print(f"{DIM}  No requirements.txt found in root. Generating one from active environment...{RESET}")
        if auto_update:
            with open(req_file, 'w') as f:
                subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f)
            print(f"{GREEN}  [✔] Created requirements.txt based on current build state.{RESET}")