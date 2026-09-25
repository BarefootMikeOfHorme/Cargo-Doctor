====================================================================
  CARGO DOCTOR: TEMPLATE & WORKFLOW GUIDE
====================================================================

Cargo Doctor is a diagnostic wrapper designed to live as a template in 
your project templates directory or root setup. It automatically scans 
upward to locate your workspace/package `Cargo.toml`, formats your code, 
runs strict Clippy static analysis with JSON error mapping, compiles 
binaries, and outputs an actionable clean summary.

--------------------------------------------------------------------
  1. SETUP & INSTALLATION
--------------------------------------------------------------------

Step A: Copy `cargo-doctor.py` into your project's root folder 
        (beside your workspace or package `Cargo.toml`).
Step B: Make the script executable (Linux/macOS):
        $ chmod +x cargo-doctor.py

--------------------------------------------------------------------
  2. COMMAND OPTIONS & FLAGS REFERENCE
--------------------------------------------------------------------

Cargo Doctor fully harnesses underlying cargo flags through clean optional arguments:

• Profiles:
  - `dev`      : Compiles and analyzes using standard development profile (Default).
  - `release`  : Compiles and analyzes using the optimized release profile (`--release`).

• Scoping & Targets:
  - `<file.rs>`: Pass any relative path to a `.rs` file to filter out all unrelated 
                 compiler and clippy messages, letting you focus strictly on your current file.

• Optional Flags:
  - `--tests`  : Expands Clippy analysis to include unit and integration tests.
  - `--benches` : Expands analysis to cover benchmark targets.
  - `--all`    : Activates all workspace features (`--all-features`) across targets.
  - `--help`   : Displays quick inline CLI help.

--------------------------------------------------------------------
  3. USAGE EXAMPLES
--------------------------------------------------------------------

• Standard Development Pipeline:
  $ python3 cargo-doctor.py

• Optimized Release Build Check with Tests Included:
  $ python3 cargo-doctor.py release --tests

• Isolate Analysis to a Single Module File:
  $ python3 cargo-doctor.py src/core/engine.rs

• Full Workspace Feature Validation:
  $ python3 cargo-doctor.py --all

--------------------------------------------------------------------
  4. TERMINAL ALIAS SETUP (OPTIONAL CONVENIENCE)
--------------------------------------------------------------------

To make the script behave like a native command from any subdirectory:

• Bash / Zsh (`~/.bashrc` or `~/.zshrc`):
  alias cargo-doc='python3 /absolute/path/to/cargo-doctor.py'

• PowerShell (`~/Documents/PowerShell/Microsoft.PowerShell_profile.ps1`):
  function cargo-doc { python C:\path\to\cargo-doctor.py $args }
====================================================================