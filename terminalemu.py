import subprocess
import threading
import platform

def launch_isolated_output_process(cmd_list: list, context: dict, popout: bool = False):
    """Executes build tasks in a threaded subprocess or a detached popout terminal."""
    
    def worker():
        env = os.environ.copy()
        # Enforce sandbox cargo target and python paths
        env["CARGO_TARGET_DIR"] = str(context["tmp_sandbox"] / "target")
        
        proc = subprocess.Popen(
            cmd_list,
            cwd=str(context["project_root"]),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate()
        
        # Log threaded output cleanly to doctor storage
        out_log = context["doctor_dir"] / "tmp" / "latest_run.log"
        out_log.parent.mkdir(parents=True, exist_ok=True)
        with open(out_log, "w") as f:
            f.write(f"=== STDOUT ===\n{stdout}\n=== STDERR ===\n{stderr}")

    if popout:
        # Launch dedicated popout terminal window based on host OS
        system_os = platform.system().lower()
        cmd_str = " ".join(cmd_list)
        
        if "windows" in system_os:
            # Use Windows Terminal (wt) if available, fallback to cmd
            popout_cmd = ["wt.exe", "new-tab", "-d", str(context["project_root"]), "powershell", "-NoExit", "-Command", cmd_str]
        else:
            # Linux / WSL popout using x-terminal-emulator or gnome-terminal
            popout_cmd = ["x-terminal-emulator", "-e", f"bash -c '{cmd_str}; exec bash'"]

        try:
            subprocess.Popen(popout_cmd, cwd=str(context["project_root"]))
            print(f"\033[36m⚡ Spawned detached terminal process for: {cmd_list[0]}\033[0m")
        except FileNotFoundError:
            # Fallback to threaded background run if GUI terminal launcher isn't installed
            threading.Thread(target=worker, daemon=True).start()
            print(f"\033[33m⚡ GUI terminal unavailable. Running task in background thread...\033[0m")
    else:
        # Standard threaded background run
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()