# Cargo-Doctor Global Shortcut Proxy
export GLOBAL_CARGO_DOCTOR="/path/to/cargo-doctor.py"

alias cdoctor='python3 "$GLOBAL_CARGO_DOCTOR"'
alias cdinitial='python3 "$GLOBAL_CARGO_DOCTOR" --init'
alias cdsetuprerun='python3 "$GLOBAL_CARGO_DOCTOR" --scan --heavy'
alias cdvalidate='python3 "$GLOBAL_CARGO_DOCTOR" --validate'
alias cdreqs='python3 "$GLOBAL_CARGO_DOCTOR" --requirements'

# Directory Enter Hook
cd() {
    builtin cd "$@"
    if [ -f "./.cargo-doctor/aliases/cargo_doctor_aliases.sh" ]; then
        source "./.cargo-doctor/aliases/cargo_doctor_aliases.sh"
    fi
}