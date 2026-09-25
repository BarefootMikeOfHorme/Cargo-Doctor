#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import re

# ANSI Terminal Colors
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BOLD = "\033[1;1m"
DIM = "\033[2m"
RESET = "\033[0m"
CLEAR_LINE = "\033[K"
UP = "\033[F"

DOCTOR_DIR = ".cargo-doctor"
STATE_FILE = os.path.join(DOCTOR_DIR, "state.json")
BLUEPRINT_FILE = os.path.join(DOCTOR_DIR, "blueprints", "system_map.json")
WIRING_DIR = os.path.join(DOCTOR_DIR, "wiring")
AI_CONTEXT_FILE = os.path.join(DOCTOR_DIR, "ai-context", "latest_error.json")


def find_cargo_root():
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.exists(os.path.join(current, "Cargo.toml")):
            return current
        parent = os.path.dirname(current)
        if parent == current: return None
        current = parent


def setup_doctor_env(root):
    """Creates the isolated folder structure for Cargo Doctor assets."""
    base = os.path.join(root, DOCTOR_DIR)
    folders = [base, os.path.join(base, "blueprints"), WIRING_DIR, os.path.join(base, "ai-context")]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)


def get_loc(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except: return 0


def extract_wiring(filepath, root):
    """Extracts Rust structures and exports a mapped wiring JSON."""
    wiring = {"uses": [], "pub_fns": [], "structs": []}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            wiring["uses"] = re.findall(r'use\s+([^;]+);', content)
            wiring["pub_fns"] = re.findall(r'pub\s+fn\s+([a-zA-Z0-9_]+)', content)
            wiring["structs"] = re.findall(r'struct\s+([a-zA-Z0-9_]+)', content)
            
        # Save wiring specifically for this file
        rel_name = os.path.relpath(filepath, root).replace(os.sep, "_") + ".json"
        with open(os.path.join(root, WIRING_DIR, rel_name), 'w') as out:
            json.dump(wiring, out, indent=2)
    except: pass
    return wiring


def scan_environment(root, is_heavy):
    """
    Generates the Easy-View Blueprint.
    --light: Only processes changed/added/removed files (Delta).
    --heavy: Rebuilds the entire blueprint and wiring map from scratch.
    """
    mode_text = "HEAVY (Full Subroot Scan)" if is_heavy else "LIGHT (Delta Scan)"
    print(f"\n{CYAN}{BOLD}=== SYSTEM BLUEPRINT ({mode_text}) ==={RESET}")
    
    cache = {}
    if not is_heavy and os.path.exists(os.path.join(root, STATE_FILE)):
        with open(os.path.join(root, STATE_FILE), 'r') as f:
            cache = json.load(f).get("files", {})

    new_cache = {"files": {}}
    blueprint = {}
    total_loc = 0
    delta_count = 0

    for dirpath, _, filenames in os.walk(root):
        if "target" in dirpath or ".git" in dirpath or DOCTOR_DIR in dirpath: continue
        
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".": rel_dir = "ROOT"
        blueprint[rel_dir] = []

        for f in filenames:
            if not f.endswith(('.rs', '.toml', '.py')): continue
            full_path = os.path.join(dirpath, f)
            loc = get_loc(full_path)
            total_loc += loc
            mtime = os.path.getmtime(full_path)
            
            is_changed = True
            status = "⚙" # Unprocessed / Changed / Added
            if not is_heavy and str(full_path) in cache and cache[str(full_path)] == mtime:
                status = "✓" # Clean
                is_changed = False
            else:
                delta_count += 1
                
            wiring = extract_wiring(full_path, root) if f.endswith('.rs') and is_changed else None
            
            blueprint[rel_dir].append({
                "file": f, "loc": loc, "status": status, 
                "changed": is_changed,
            })
            new_cache["files"][str(full_path)] = mtime

    # Export Blueprint to file for AI context
    with open(os.path.join(root, BLUEPRINT_FILE), 'w') as bp_out:
        json.dump(blueprint, bp_out, indent=2)

    # Print Dashboard
    for folder, files in blueprint.items():
        print(f"\n📁 {BOLD}{folder}{RESET}")
        for file_data in files:
            color = GREEN if file_data['status'] == '✓' else YELLOW
            print(f"  ├── [{color}{file_data['status']}{RESET}] {file_data['file']} {DIM}({file_data['loc']} LOC){RESET}")

    print(f"\n{DIM}Total tracked LOC: {total_loc} | Files requiring diagnostic check: {delta_count}{RESET}\n")
    return new_cache, delta_count


def run_diagnostics(root):
    """Executes the Cargo pipeline and formats AI context if errors occur."""
    print(f"{CYAN}➜{RESET} Executing Cargo Diagnostics...\n")
    proc = subprocess.Popen(
        ["cargo", "clippy", "--message-format=json"], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=root
    )

    errors, warnings, ai_dump = [], [], []

    for line in proc.stdout:
        try:
            msg = json.loads(line)
            if msg.get("reason") == "compiler-message":
                m = msg.get("message", {})
                level = m.get("level")
                spans = m.get("spans", [])
                
                if not spans: continue
                primary = next((s for s in spans if s.get("is_primary")), spans[0])
                
                err_data = {
                    "file": primary.get("file_name", "unknown"),
                    "line": primary.get("line_start", 0),
                    "text": m.get("message"),
                    "snippet": primary.get("text", []),
                    "level": level
                }
                
                if level == "error": errors.append(err_data)
                elif level == "warning": warnings.append(err_data)
                
                ai_dump.append(err_data)
                sys.stdout.write(f"{CLEAR_LINE}  Scanning... {RED}{len(errors)} Errors{RESET}, {YELLOW}{len(warnings)} Warnings{RESET} {UP}\n")
                sys.stdout.flush()
        except: pass

    proc.wait()
    sys.stdout.write(f"{CLEAR_LINE}  Scan Complete. {RED}{len(errors)} Errors{RESET}, {YELLOW}{len(warnings)} Warnings{RESET}\n")
    
    if ai_dump:
        with open(os.path.join(root, AI_CONTEXT_FILE), 'w') as f:
            json.dump({"diagnostics": ai_dump}, f, indent=2)

    return errors, warnings


def watch_mode(root):
    """Zero-dependency watcher for rapid amends. Polls for directory/file changes."""
    print(f"{CYAN}👀 Watch Mode Active. Monitoring for file changes, additions, or removals...{RESET}")
    print(f"{DIM}Press Ctrl+C to exit.{RESET}\n")
    
    last_state = {}
    if os.path.exists(os.path.join(root, STATE_FILE)):
        with open(os.path.join(root, STATE_FILE), 'r') as f:
            last_state = json.load(f).get("files", {})

    try:
        while True:
            current_state = {}
            changed = False
            for dirpath, _, filenames in os.walk(root):
                if "target" in dirpath or ".git" in dirpath or DOCTOR_DIR in dirpath: continue
                for f in filenames:
                    if f.endswith(('.rs', '.toml', '.py')):
                        full_path = str(os.path.join(dirpath, f))
                        mtime = os.path.getmtime(full_path)
                        current_state[full_path] = mtime
                        if full_path not in last_state or last_state[full_path] != mtime:
                            changed = True

            # Check for deletions
            if len(current_state) != len(last_state): changed = True

            if changed:
                print(f"\n{YELLOW}⚡ File system change detected. Running light amend...{RESET}")
                new_cache, deltas = scan_environment(root, is_heavy=False)
                errors, _ = run_diagnostics(root)
                if not errors:
                    with open(os.path.join(root, STATE_FILE), 'w') as f:
                        json.dump(new_cache, f)
                last_state = current_state
                print(f"{CYAN}👀 Resuming watch...{RESET}")

            time.sleep(2) # Poll every 2 seconds
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Watch mode terminated.{RESET}")
        sys.exit(0)


def print_help():
    print(f"""{CYAN}{BOLD}CARGO DOCTOR - LOCAL DEV PORTAL{RESET}

{BOLD}COMMANDS:{RESET}
  {GREEN}init{RESET}          Initialize the .cargo-doctor structure and run a heavy baseline scan.
  {GREEN}scan --light{RESET}  (Default) Quick delta scan. Only maps files changed since last run.
  {GREEN}scan --heavy{RESET}  Rebuilds the entire file blueprint and wiring map from scratch.
  {GREEN}watch{RESET}         Stays open in terminal, automatically amending state when files change.
""")


def main():
    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print_help()
        sys.exit(0)

    root = find_cargo_root()
    if not root:
        print(f"{RED}[✖] No Cargo.toml found.{RESET}")
        sys.exit(1)
        
    os.chdir(root)
    setup_doctor_env(root)

    cmd = args[0] if args else "scan"
    is_heavy = "--heavy" in args or cmd == "init"

    if cmd == "watch":
        watch_mode(root)
        return

    # Normal Run execution
    new_cache, deltas = scan_environment(root, is_heavy)
    
    if deltas == 0 and not is_heavy:
        print(f"{GREEN}✓ Dependencies met. No changes detected.{RESET}")
        sys.exit(0)

    errors, warnings = run_diagnostics(root)
    
    if errors:
        print(f"\n{RED}{BOLD}=== 🚨 ACTION REQUIRED: ERRORS ==={RESET}")
        for e in errors:
            print(f"  [E] {BOLD}{e['file']}{RESET}:{e['line']}\n      {e['text']}")
            if e['snippet']:
                print(f"      {DIM}> {e['snippet'][0].get('text', '').strip()}{RESET}")
        print(f"\n{YELLOW}💡 Hint: Point your AI to {AI_CONTEXT_FILE} for immediate repair context.{RESET}")
        sys.exit(1)
    else:
        # Save state only on successful build
        with open(os.path.join(root, STATE_FILE), 'w') as f:
            json.dump(new_cache, f)
        print(f"\n{GREEN}{BOLD}🎉 SYSTEM GREEN. Ready for next task.{RESET}")
        sys.exit(0)

if __name__ == "__main__":
    main()