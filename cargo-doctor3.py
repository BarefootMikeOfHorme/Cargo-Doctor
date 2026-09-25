#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import shutil

# ANSI Terminal Colors
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
    print(f"\n{CYAN}{'='*72}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{'='*72}{RESET}\n")


def run_command(cmd, desc, cwd=None, capture=True):
    """Executes a subprocess and returns the result and execution time."""
    print(f"{CYAN}[➜]{RESET} {desc}...")
    start = time.time()
    result = subprocess.run(cmd, capture_output=capture, text=capture, cwd=cwd)
    duration = time.time() - start
    return result, duration


def has_cargo_subcommand(subcmd):
    """Checks if a specific cargo tool/subcommand is installed."""
    res = subprocess.run(["cargo", subcmd, "--help"], capture_output=True)
    return res.returncode == 0


def print_help():
    print(f"""{CYAN}{BOLD}CARGO DOCTOR - ADVANCED DEV PIPELINE{RESET}

{BOLD}SYNOPSIS:{RESET}
    python3 cargo-doctor.py [PROFILE] [TARGET_FILE] [OPTIONS]

{BOLD}PROFILES:{RESET}
    dev         Run checks and build using development profile (default)
    release     Run checks and build using optimized release profile

{BOLD}TARGET FILTER:{RESET}
    <path/to/file.rs>  Isolate diagnostics to a specific source file, smoothing cross-platform (WSL/Windows) debugging.

{BOLD}PIPELINE FLAGS:{RESET}
    --fix       Automatically apply safe Clippy suggestions and format fixes
    --audit     Scan dependency tree for known security vulnerabilities
    --udeps     Detect unused dependencies in Cargo.toml (requires nightly toolchain)
    --test      Execute the test suite after a successful build
    --all       Include all features and workspace members
    --help      Show this help message
""")


def main():
    # Force color output for cargo commands
    os.environ["CARGO_TERM_COLOR"] = "always"

    args = sys.argv[1:]
    if "--help" in args or "-h" in args:
        print_help()
        sys.exit(0)

    # 1. Workspace Localization
    cargo_root = find_cargo_root()
    if not cargo_root:
        print(f"{RED}[✖] Error: No Cargo.toml found in current or parent directories.{RESET}")
        sys.exit(1)

    os.chdir(cargo_root)

    # 2. Argument Parsing
    profile = "dev"
    target_filter = None
    
    # Feature Flags
    auto_fix = "--fix" in args
    run_audit = "--audit" in args
    run_udeps = "--udeps" in args
    run_tests = "--test" in args
    all_features = "--all" in args or "--all-features" in args

    for arg in args:
        if arg in ["dev", "release"]:
            profile = arg
        elif arg.endswith(".rs") or "/" in arg or "\\" in arg:
            # Normalize paths for seamless WSL / PowerShell interchangeability
            target_filter = os.path.normpath(os.path.abspath(arg))

    print_header(f"CARGO DOCTOR (Root: {os.path.basename(cargo_root)})")
    pipeline_start = time.time()
    
    warnings_by_file = {}
    errors_by_file = {}

    # ---------------------------------------------------------
    # STAGE 0: Auto-Fixing (Optional)
    # ---------------------------------------------------------
    if auto_fix:
        print(f"{CYAN}[➜]{RESET} Stage 0: Applying automatic fixes (cargo clippy --fix & fmt)...")
        fix_cmd = ["cargo", "clippy", "--fix", "--allow-dirty", "--allow-staged"]
        if all_features:
            fix_cmd.append("--all-features")
        subprocess.run(fix_cmd, capture_output=True)
        subprocess.run(["cargo", "fmt", "--all"], capture_output=True)
        print(f"{GREEN}[✔] Automated formatting and lints applied.{RESET}\n")

    # ---------------------------------------------------------
    # STAGE 1: Formatting Check
    # ---------------------------------------------------------
    if not auto_fix:
        res, duration = run_command(["cargo", "fmt", "--all", "--", "--check"], "Stage 1: Validating code style (cargo fmt)")
        if res.returncode != 0:
            print(f"{YELLOW}[!] Formatting discrepancies found. Use '--fix' to resolve automatically.{RESET}\n")
        else:
            print(f"{GREEN}[✔] Code formatting verified ({duration:.2f}s){RESET}\n")

    # ---------------------------------------------------------
    # STAGE 2: Fast Compilation Check
    # ---------------------------------------------------------
    check_cmd = ["cargo", "check"]
    if all_features: check_cmd.append("--all-features")
    res, duration = run_command(check_cmd, "Stage 2: Fast compiler check (cargo check)")
    if res.returncode != 0:
        print(f"{RED}[✖] Compilation check failed. Skipping deeper linting.{RESET}")
        print(res.stderr)
        sys.exit(1)
    print(f"{GREEN}[✔] Syntax and types verified ({duration:.2f}s){RESET}\n")

    # ---------------------------------------------------------
    # STAGE 3: Clippy Static Analysis
    # ---------------------------------------------------------
    print(f"{CYAN}[➜]{RESET} Stage 3: Running deep static analysis (cargo clippy)...")
    clippy_cmd = [
        "cargo", "clippy", "--all-targets", "--message-format=json"
    ]
    if profile == "release": clippy_cmd.append("--release")
    if all_features: clippy_cmd.append("--all-features")
    # Deny warnings to treat them as hard errors in CI pipelines
    clippy_cmd.extend(["--", "-D", "warnings"])

    start = time.time()
    proc = subprocess.Popen(clippy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

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
                    abs_file_path = os.path.normpath(os.path.abspath(os.path.join(cargo_root, file_name)))
                else:
                    file_name = "general"
                    abs_file_path = ""

                # Filter diagnostics to target file if specified
                if target_filter and abs_file_path != target_filter:
                    continue

                entry = {
                    "code": code,
                    "text": text.split("\n")[0],
                    "line": primary_span.get("line_start", 0) if spans else 0,
                    "col": primary_span.get("column_start", 0) if spans else 0,
                }

                if level == "error":
                    errors_by_file.setdefault(file_name, []).append(entry)
                elif level == "warning":
                    warnings_by_file.setdefault(file_name, []).append(entry)
        except json.JSONDecodeError:
            continue
    proc.wait()
    print(f"{GREEN}[✔] Analysis complete ({time.time() - start:.2f}s){RESET}\n")

    # ---------------------------------------------------------
    # STAGE 4: Security Audit (Optional)
    # ---------------------------------------------------------
    audit_success = True
    if run_audit:
        if has_cargo_subcommand("audit"):
            res, duration = run_command(["cargo", "audit"], "Stage 4: Auditing dependencies for vulnerabilities")
            if res.returncode == 0:
                print(f"{GREEN}[✔] No vulnerabilities found ({duration:.2f}s){RESET}\n")
            else:
                audit_success = False
                print(f"{RED}[✖] Security vulnerabilities detected!{RESET}\n{res.stdout}")
        else:
            print(f"{YELLOW}[!] cargo-audit is not installed. Run 'cargo install cargo-audit' to enable.{RESET}\n")

    # ---------------------------------------------------------
    # STAGE 5: Unused Dependencies (Optional)
    # ---------------------------------------------------------
    if run_udeps:
        if has_cargo_subcommand("udeps"):
            res, duration = run_command(["cargo", "+nightly", "udeps"], "Stage 5: Checking for unused dependencies")
            if res.returncode == 0:
                print(f"{GREEN}[✔] Cargo.toml is clean ({duration:.2f}s){RESET}\n")
            else:
                print(f"{YELLOW}[!] Unused dependencies found:{RESET}\n{res.stderr}")
        else:
            print(f"{YELLOW}[!] cargo-udeps is missing or nightly toolchain is not active.{RESET}\n")

    # ---------------------------------------------------------
    # STAGE 6: Build Artifacts
    # ---------------------------------------------------------
    build_success = False
    if not errors_by_file and audit_success:
        build_cmd = ["cargo", "build"]
        if profile == "release": build_cmd.append("--release")
        if all_features: build_cmd.append("--all-features")

        res, build_duration = run_command(build_cmd, f"Stage 6: Compiling binaries ({profile})")
        build_success = res.returncode == 0
        if build_success:
            print(f"{GREEN}[✔] Build compilation succeeded ({build_duration:.2f}s){RESET}\n")
        else:
            print(f"{RED}[✖] Build compilation failed:{RESET}\n{res.stderr}")
    else:
        print(f"{YELLOW}[!] Skipping binary build pass due to upstream pipeline errors.{RESET}\n")

    # ---------------------------------------------------------
    # STAGE 7: Test Suite (Optional)
    # ---------------------------------------------------------
    if run_tests and build_success:
        test_cmd = ["cargo", "test"]
        if all_features: test_cmd.append("--all-features")
        res, duration = run_command(test_cmd, "Stage 7: Executing test suite")
        if res.returncode == 0:
            print(f"{GREEN}[✔] All tests passed cleanly ({duration:.2f}s){RESET}\n")
        else:
            print(f"{RED}[✖] Test suite encountered failures:{RESET}\n{res.stdout}")

    # ---------------------------------------------------------
    # STAGE 8: Executive Summary Report
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
    print(f"  ⚙️  Build Status:         {GREEN + 'SUCCESS' if build_success else RED + 'PENDING/FAILED'}{RESET}")
    if run_audit:
        print(f"  🛡️  Security Audit:       {GREEN + 'PASSED' if audit_success else RED + 'VULNERABLE'}{RESET}")

    if errors_by_file:
        print(f"\n{RED}{BOLD}--- [❌] BUILD & LINT ERRORS ---{RESET}")
        for file, errs in errors_by_file.items():
            print(f"  📁 {BOLD}{file}{RESET}")
            for e in errs:
                print(f"     ├── [{e['code']}] {e['text']} {DIM}(L{e['line']}, C{e['col']}){RESET}")

    if warnings_by_file:
        print(f"\n{YELLOW}{BOLD}--- [⚠️] CLIPPY WARNINGS ---{RESET}")
        for file, warns in warnings_by_file.items():
            print(f"  📁 {BOLD}{file}{RESET}")
            for w in warns:
                print(f"     └── [{w['code']}] {w['text']} {DIM}(L{w['line']}){RESET}")

    print(f"\n{CYAN}{'='*72}{RESET}")
    if total_errors == 0 and build_success and audit_success:
        print(f"{GREEN}{BOLD}  🎉 ALL CHECKS PASSED CLEANLY.{RESET}")
    else:
        print(f"{YELLOW}{BOLD}  💡 ACTION PLAN: Review the diagnostics above or run with '--fix'.{RESET}")
    print(f"{CYAN}{'='*72}{RESET}\n")

    sys.exit(0 if (total_errors == 0 and build_success and audit_success) else 1)


if __name__ == "__main__":
    main()