# Inside run_diagnostics() or your build stage:
    trusted_env = inject_trusted_environment(root)

    proc = subprocess.Popen(
        ["cargo", "clippy", "--message-format=json"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        cwd=root,
        env=trusted_env  # <--- Cargo now obeys the injected paths
    )