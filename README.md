====================================================================
  CARGO DOCTOR: TUTORIAL & WORKFLOW GUIDE
====================================================================

Welcome to Cargo Doctor! This guide walks you through setting up, 
running, and using the intelligent Cargo diagnostic runner from 
anywhere in your project tree.

--------------------------------------------------------------------
  1. SETUP & INSTALLATION
--------------------------------------------------------------------

Step A: Place the script in your project root (beside your workspace 
        or package `Cargo.toml`).
Step B: Make the script executable (Linux/macOS):
        $ chmod +x cargo-doctor.py

--------------------------------------------------------------------
  2. RUNNING THE PIPELINE
--------------------------------------------------------------------

Because Cargo Doctor automatically scans upward to find your project's 
`Cargo.toml`, you can run it from *anywhere* in your file hierarchy—whether 
you are sitting in the root folder or buried deep inside a nested module.

• Standard Development Run:
  $ python3 cargo-doctor.py
  
• Release Optimization Run:
  $ python3 cargo-doctor.py release

--------------------------------------------------------------------
  3. TARGETED FILE DEBUGGING (ISOLATED SCOPE)
--------------------------------------------------------------------

If you are working on a massive project and only want to inspect issues 
tied to a specific file or module you are currently modifying, pass the 
file path as an argument:

  $ python3 cargo-doctor.py src/core/engine.rs

(The script will automatically suppress compiler errors and warnings 
originating outside that file scope).

--------------------------------------------------------------------
  4. CREATING A TERMINAL ALIAS (OPTIONAL SPEED-UP)
--------------------------------------------------------------------

To make the script feel like a native cargo command, add an alias or 
shortcut to your shell profile:

• Bash / Zsh (~/.bashrc or ~/.zshrc):
  alias cargo-doc='python3 /absolute/path/to/cargo-doctor.py'

• PowerShell (~/Documents/PowerShell/Microsoft.PowerShell_profile.ps1):
  function cargo-doc { python C:\path\to\cargo-doctor.py $args }

Once aliased, you can simply type `cargo-doc` from any subdirectory!
====================================================================