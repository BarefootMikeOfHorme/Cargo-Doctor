#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time

CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BOLD = "\033[1;1m"
DIM = "\033[2m"
RESET = "\033[0m"


def find_cargo_root():
    """Traverses upward from the current working directory to find the Cargo workspace/project root."""
    current = os.path.abspath(os.getcwd())
    while True:
        if os.path.exists(os.path.join(current, "Cargo.toml")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def print_header(title):
    print(f"\n{CYAN}{'='*68}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{'='*68}{RESET}\n")


def run_command(cmd, desc, cwd=None):
    print(f"{CYAN}[➜]{RESET} {desc}...")
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    duration = time.time() - start
    return result, duration


def main():
    os.environ["CARGO_TERM_COLOR"] = "always"

    # 1. Locate Cargo Root dynamically from current path
    cargo_root = find_cargo_root()
    if not cargo_root:
        print(f"{RED}[✖] Error: No Cargo.toml found in current or parent directories.{RESET}")
        sys.exit(1)

    # Change execution context to root so Cargo commands always execute globally for the project
    os.chdir(cargo_root)

    # Optional argument: target a specific file/module or pass profile ('dev' / 'release')
    args = sys.argv[1:]
    profile = "dev"
    target_filter = None

    for arg in args:
        if arg in ["dev", "release"]:
            profile = arg
        elif arg.endswith(".rs") or "/" in arg or "\\" in arg:
            target_filter = os.path.abspath(arg)

    print_header(f"CARGO DOCTOR (Root: {os.path.basename(cargo_root)})")
    pipeline_start = time.time()

    # ---------------------------------------------------------
    # STAGE 1: Formatting
    # ---------------------------------------------------------
    res, duration = run_command(["cargo", "fmt", "--all"], "Stage 1: Formatting code (cargo fmt)")
    if res.returncode != 0:
        print(f"{RED}[✖] Format check failed:{RESET}\n{res.stderr}")
        sys.exit(1)
    print(f"{GREEN}[✔] Code formatted successfully ({duration:.2f}s){RESET}\n")

    # ---------------------------------------------------------
    # STAGE 2: Clippy Analysis & JSON Parsing
    # ---------------------------------------------------------
    print(f"{CYAN}[➜]{RESET} Stage 2: Running static analysis (cargo clippy)...")
    clippy_cmd = [
        "cargo",
        "clippy",
        "--all-targets",
        "--message-format=json",
        "--",
        "-D",
        "warnings",
    ]
    if profile == "release":
        clippy_cmd.insert(2, "--release")

    start = time.time()
    proc = subprocess.Popen(
        clippy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    errors_by_file = {}
    warnings_by_file = {}

    for line in proc.stdout:
        try:
            msg = json.loads(line)
            if msg.get("reason") == "compiler-message":
                m = msg.get("message", {})
                level = m.get("level")
                code_obj = m.get("code")
                code = code_obj.get("code") if code_obj else "unknown"
                text = m.get("message")

                spans = m.get("spans", [])
                if spans:
                    primary_span = next((s for s in spans if s.get("is_primary")), spans[0])
                    file_name = primary_span.get("file_name", "unknown")
                    # Normalize absolute path matching if target filter is active
                    abs_file_path = os.path.abspath(os.path.join(cargo_root, file_name))
                else:
                    file_name = "general"
                    abs_file_path = ""

                # If user specified a target file filter, skip errors outside that scope
                if target_filter and abs_file_path != target_filter:
                    continue

                line_num = primary_span.get("line_start", 0) if spans else 0
                col_num = primary_span.get("column_start", 0) if spans else 0

                entry = {
                    "code": code,
                    "text": text.split("\n")[0],
                    "line": line_num,
                    "col": col_num,
                }

                if level == "error":
                    errors_by_file.setdefault(file_name, []).append(entry)
                elif level == "warning":
                    warnings_by_file.setdefault(file_name, []).append(entry)
        except json.JSONDecodeError:
            continue

    proc.wait()

    # ---------------------------------------------------------
    # STAGE 3: Build Generation
    # ---------------------------------------------------------
    build_success = False
    build_duration = 0.0
    if not errors_by_file:
        build_cmd = ["cargo", "build"]
        if profile == "release":
            build_cmd.append("--release")
        res, build_duration = run_command(build_cmd, f"Stage 3: Building binaries ({profile})")
        build_success = res.returncode == 0
        if not build_success:
            print(f"{RED}[✖] Build compilation failed:{RESET}\n{res.stderr}")
    else:
        print(f"{YELLOW}[!] Skipping build pass due to analysis errors.{RESET}")

    # ---------------------------------------------------------
    # STAGE 4: Summary Report
    # ---------------------------------------------------------
    print_header("DIAGNOSTIC & TASK SUMMARY REPORT")

    total_errors = sum(len(v) for v in errors_by_file.values())
    total_warnings = sum(len(v) for v in warnings_by_file.values())

    if target_filter:
        print(f"  🎯 Target Filter Active: {BOLD}{os.path.basename(target_filter)}{RESET}")
    print(f"  📦 Environment Profile:  {BOLD}{profile.upper()}{RESET}")
    print(f"  ⏱️  Total Pipeline Time:  {time.time() - pipeline_start:.2f}s")
    print(f"  ❌ Errors Found:         {RED if total_errors > 0 else GREEN}{total_errors}{RESET}")
    print(f"  ⚠️  Warnings Found:       {YELLOW if total_warnings > 0 else GREEN}{total_warnings}{RESET}")
    print(f"  ⚙️  Build Status:         {GREEN + 'SUCCESS' if build_success else RED + 'PENDING/FAILED'}{RESET}\n")

    if errors_by_file:
        print(f"{RED}{BOLD}--- [❌] BUILD & LINT ERRORS ---{RESET}")
        for file, errs in errors_by_file.items():
            print(f"\n  📁 {BOLD}{file}{RESET}")
            for e in errs:
                print(f"     ├── [{e['code']}] {e['text']}")
                print(f"     │     {DIM}Line {e['line']}, Col {e['col']}{RESET}")

    if warnings_by_file:
        print(f"\n{YELLOW}{BOLD}--- [⚠️] CLIPPY WARNINGS ---{RESET}")
        for file, warns in warnings_by_file.items():
            print(f"\n  📁 {BOLD}{file}{RESET}")
            for w in warns:
                print(f"     └── [{w['code']}] {w['text']} {DIM}(L{w['line']}){RESET}")

    print(f"\n{CYAN}{'='*68}{RESET}")
    if total_errors == 0 and build_success:
        print(f"{GREEN}{BOLD}  🎉 ALL CHECKS PASSED CLEANLY.{RESET}")
    else:
        print(f"{YELLOW}{BOLD}  💡 ACTION PLAN: Batch fix items listed above.{RESET}")
    print(f"{CYAN}{'='*68}{RESET}\n")

    sys.exit(0 if (total_errors == 0 and build_success) else 1)


if __name__ == "__main__":
    main()