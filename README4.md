====================================================================
  CARGO DOCTOR: LOCAL DEVELOPER PORTAL
====================================================================

Cargo Doctor has evolved from a simple test runner into a lightweight 
developer portal. When initialized in a global root or subroot, it 
generates a dedicated `.cargo-doctor` directory to store system maps, 
wiring logic, and AI contexts, keeping your root directory clean.

--------------------------------------------------------------------
  1. FOLDER STRUCTURE
--------------------------------------------------------------------

Running Cargo Doctor creates a hidden `.cargo-doctor` directory with 
the following structure. These files are highly formatted for AI 
consumption (like local LLMs or Aider).

.cargo-doctor/
  ├── blueprints/       # system_map.json (Folder structures & LOC)
  ├── wiring/           # individual .json files mapping structs and functions
  ├── ai-context/       # latest_error.json (Direct feed for AI repair)
  └── state.json        # Timestamp cache to keep delta scans lightning fast

*Note: You should add `.cargo-doctor/` to your `.gitignore`.*

--------------------------------------------------------------------
  2. SCOPING COMMANDS
--------------------------------------------------------------------

• Initialization & Heavy Scans
  $python3 cargo-doctor.py init$ python3 cargo-doctor.py scan --heavy
  Use this when you drop the tool into a new root, or if you've made 
  massive structural changes. It ignores the cache, rebuilds the entire 
  file blueprint, and regenerates the wiring maps for every file.

• The Daily Light Scan (Delta Check)
  $ python3 cargo-doctor.py scan --light
  (Or simply: $ python3 cargo-doctor.py)
  This is the fast path. It references `.cargo-doctor/state.json` and 
  only scans files that have been modified, added, or removed. If no 
  changes are detected, it exits instantly with "Dependencies met."

--------------------------------------------------------------------
  3. WATCH MODE (QUICK AMEND SCRIPT)
--------------------------------------------------------------------

If you are going through waves of "additions -> debug -> repair," run:

  $ python3 cargo-doctor.py watch

This initiates a zero-dependency polling loop. Any time a file is added, 
removed, renamed, or saved, Cargo Doctor will detect the filesystem 
change, trigger a `--light` amend, update the dashboard, and export the 
latest errors to the `.cargo-doctor/ai-context/latest_error.json` file.
====================================================================