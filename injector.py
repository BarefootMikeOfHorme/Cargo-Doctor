def inject_trusted_environment(root):
    """Reads the mapped toolchain and forces the current process to use those paths."""
    env_file = os.path.join(root, DOCTOR_DIR, "blueprints", "global_environment.json")
    
    if not os.path.exists(env_file):
        return os.environ.copy() # Return default if no map exists

    with open(env_file, 'r') as f:
        env_map = json.load(f)

    active_env = os.environ.copy()
    tools = env_map.get("discovered_tools", {})

    # PyO3 Specific Binding: Force Rust to use the exact Python binary mapped
    if "python3.12" in tools:
        py_path = tools["python3.12"]["path"]
        active_env["PYTHON_SYS_EXECUTABLE"] = py_path
        print(f"{CYAN}🔗 Bound PyO3 compiler to: {py_path}{RESET}")
    elif "python3" in tools:
        py_path = tools["python3"]["path"]
        active_env["PYTHON_SYS_EXECUTABLE"] = py_path
        print(f"{CYAN}🔗 Bound PyO3 compiler to: {py_path}{RESET}")

    # You can map CC or CXX for C-linkers here if needed
    if "clang" in tools:
        active_env["CC"] = tools["clang"]["path"]

    return active_env