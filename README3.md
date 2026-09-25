====================================================================
  CARGO DOCTOR: ADVANCED WORKFLOW & DIAGNOSTIC PIPELINE
====================================================================

Cargo Doctor is an intelligent, multi-stage wrapper designed to act as
the command center for modern Rust development. Rather than executing 
half a dozen individual cargo commands to verify code quality, this 
script aggregates formatting, fast compiler checks, deep linting, 
security auditing, and binary compilation into a single, cohesive 
dashboard.

Cargo handles downloading and compiling dependencies to ensure that 
all crates use compatible versions. Cargo Doctor orchestrates 
this ecosystem so you can focus strictly on the code. 

--------------------------------------------------------------------
  1. SETUP & PREREQUISITES
--------------------------------------------------------------------

Place `cargo-doctor.py` directly in your workspace or package root.
Make the script executable:
  $ chmod +x cargo-doctor.py

**Power User Ecosystem Additions:**
For the pipeline to reach its full potential, it is highly recommended 
to install the following standard extensions:
  $cargo install cargo-audit$ cargo install cargo-udeps

--------------------------------------------------------------------
  2. UNDERSTANDING THE STAGES
--------------------------------------------------------------------

The pipeline is structured sequentially to fail fast and provide 
immediate feedback before burning CPU cycles on full compilation:

1. **Format (`cargo fmt`)**: Enforces formatting guidelines across the project.
2. **Check (`cargo check`)**: Runs the compiler's analysis passes without producing a binary, ensuring extremely fast verification during refactoring.
3. **Lint (`cargo clippy`)**: Provides insights and warnings about potential issues, catching suboptimal patterns. 
4. **Audit (`cargo audit`)*: Scans the project's dependency tree for known vulnerabilities and outdated versions.
5. **Optimize (`cargo udeps`)*: Identifies unused dependencies in your Cargo.toml file to keep your binary bloat-free.
6. **Build & Test**: Compiles binaries and safely executes tests.

*(Starred stages require their respective flags).*

--------------------------------------------------------------------
  3. PIPELINE FLAGS & USAGE
--------------------------------------------------------------------

The script adapts heavily to the optional arguments passed to it. 
It supports running in the optimized `--release` profile or isolating 
diagnostics to a single `target_file.rs`.

**General Workflows:**
• Standard Development Run:
  $ python3 cargo-doctor.py

• Optimized Release Build:
  $ python3 cargo-doctor.py release

**Advanced Flags:**
• `--fix`   : Automatically applies compiler suggestions and formats code.
              Helpful during large refactors or Rust edition upgrades.
• `--audit` : Triggers `cargo audit` to secure the dependency chain.
• `--udeps` : Verifies you haven't left abandoned dependencies in your manifest.
• `--test`  : Runs the test suite seamlessly after a successful build.
• `--all`   : Includes all features and workspace members. 

**Combined Example:**
  $ python3 cargo-doctor.py release src/engine.rs --fix --audit --test

--------------------------------------------------------------------
  4. CI/CD INTEGRATION & BEST PRACTICES
--------------------------------------------------------------------

Cargo Doctor is uniquely designed to act as an entry point for 
Continuous Integration systems. By enforcing `cargo clippy -- -D warnings`, 
the script turns standard lints into hard blocking errors, preventing 
quality regressions from being merged.

Common CI Troubleshooting:
- If the pipeline fails on lints: Run locally with `--fix` and commit.
- If the pipeline fails on unused dependencies: Run locally with `--udeps` and remove the flagged crates.
- If the pipeline fails on audits: Update vulnerable dependencies identified by the scanner.
====================================================================