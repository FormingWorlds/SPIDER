#!/usr/bin/env bash
# =============================================================================
# get_spider.sh — Build SPIDER from an already-cloned checkout
# =============================================================================
#
# Builds the SPIDER interior evolution model against a local PETSc
# installation. PETSc is installed automatically first if it is missing.
#
# SPIDER is a pure C code that uses PETSc for numerics and sundials2 for
# ODE integration. The Makefile includes PETSc's build rules, so PETSC_DIR
# and PETSC_ARCH must be set correctly.
#
# Supported platforms:
#   - macOS 10.15 (Catalina) and later, Intel and Apple Silicon
#   - Linux (Ubuntu, Debian, Fedora/RHEL, HPC clusters)
#
# Supported repository layouts:
#   - Standalone clone: <something>/SPIDER/tools/get_spider.sh
#       -> PETSc defaults to <something>/SPIDER/petsc/
#   - Nested clone:     <something>/PROTEUS/SPIDER/tools/get_spider.sh
#       -> PETSc defaults to <something>/PROTEUS/petsc/
#
# Prerequisites:
#   - A cloned SPIDER repository (this script builds the current checkout)
#   - C compiler accessible via MPI wrapper (mpicc), or PETSc's MPICH download
#   - make
#
# Usage:
#   ./tools/get_spider.sh                    # build the current checkout in place
#   ./tools/get_spider.sh /path/to/SPIDER    # build a different cloned checkout
#
# Logs:
#   Full build logs are written to:
#     <SPIDER checkout>/logs/get_spider-YYYYmmdd-HHMMSS.log
#
# The script is suitable for standalone SPIDER installs, and still behaves
# nicely inside a PROTEUS/SPIDER checkout by installing PETSc in PROTEUS/petsc.
#
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Console stream setup
# -----------------------------------------------------------------------------
if tty -s 2>/dev/null && [[ -w /dev/tty ]]; then
    exec 3>/dev/tty
    exec 4>/dev/tty
else
    exec 3>&1
    exec 4>&2
fi

console() {
    printf '%s\n' "$*" >&3
}

announce() {
    printf '%s\n' "$*" >&3
    printf '%s\n' "$*"
}

# -----------------------------------------------------------------------------
# Portable path helpers
# -----------------------------------------------------------------------------
portable_realpath() {
    if command -v realpath >/dev/null 2>&1; then
        realpath "$1"
    else
        python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$1"
    fi
}

portable_abspath() {
    python3 -c "import os,sys; print(os.path.abspath(sys.argv[1]))" "$1"
}

# -----------------------------------------------------------------------------
# Repository layout helpers
# -----------------------------------------------------------------------------
default_petsc_path_for_repo() {
    local repo_root="$1"
    local parent_root

    parent_root="$(dirname "$repo_root")"

    # If this checkout lives at PROTEUS/SPIDER, prefer PROTEUS/petsc so that
    # PETSc is shared with the wider PROTEUS tree.
    if [[ "$(basename "$repo_root")" == "SPIDER" ]] && [[ "$(basename "$parent_root")" == "PROTEUS" ]]; then
        printf '%s/petsc\n' "$parent_root"
    else
        printf '%s/petsc\n' "$repo_root"
    fi
}

petsc_built_ok() {
    local petsc_dir="$1"
    local petsc_arch="$2"
    local petsc_lib_dir petsc_conf_dir f

    [[ -d "$petsc_dir" ]] || return 1

    petsc_lib_dir="$petsc_dir/$petsc_arch/lib"
    petsc_conf_dir="$petsc_dir/lib/petsc/conf"

    for f in "$petsc_lib_dir"/libpetsc.*; do
        [[ -f "$f" ]] || continue
        [[ -f "$petsc_conf_dir/variables" ]] || return 1
        [[ -f "$petsc_conf_dir/rules" ]] || return 1
        return 0
    done

    return 1
}

# -----------------------------------------------------------------------------
# Error handling: report which step failed on any non-zero exit
# -----------------------------------------------------------------------------
current_step="initialising"
logfile=""

on_error() {
    local rc=$?

    console ""
    console "========================================"
    console " ERROR: SPIDER installation failed"
    console ""
    console " Step that failed: $current_step"
    console " Command:          $BASH_COMMAND"
    console " Exit code:        $rc"
    if [[ -n "${logfile:-}" ]]; then
        console " Log file:         $logfile"
    fi
    console ""
    console " Troubleshooting:"

    case "$current_step" in
        *"PETSc"*)
            console "   - Check the PETSc installer output above for errors"
            console "   - Re-run ./tools/get_petsc.sh manually if needed"
            ;;
        *"Building"*)
            console "   - Check the compiler output in the log file"
            console "   - Verify mpicc is working: mpicc --version"
            console "   - Verify PETSc is intact: ls \$PETSC_DIR/\$PETSC_ARCH/lib/libpetsc.*"
            console "   - On macOS: ensure SDKROOT is set (xcrun --show-sdk-path)"
            ;;
        *"Verif"*)
            console "   - The build completed without make errors but no binary was produced"
            console "   - This usually indicates a linker failure that was suppressed"
            console "   - Try rebuilding with verbose output: make V=1"
            ;;
        *)
            console "   - Review the log file for the failing command"
            ;;
    esac

    console ""
    console " PETSc environment used:"
    console "   PETSC_DIR  = ${PETSC_DIR:-<not set>}"
    console "   PETSC_ARCH = ${PETSC_ARCH:-<not set>}"
    console "========================================"
}
trap on_error ERR

# -----------------------------------------------------------------------------
# 1. Detect platform and set PETSC_ARCH
# -----------------------------------------------------------------------------
current_step="Detecting platform"

if [[ "$OSTYPE" == linux* ]]; then
    PETSC_ARCH=arch-linux-c-opt
elif [[ "$OSTYPE" == darwin* ]]; then
    PETSC_ARCH=arch-darwin-c-opt
else
    echo "ERROR: Unsupported OS type '$OSTYPE'. Only Linux and macOS are supported." >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# 2. Locate SPIDER checkout to build
# -----------------------------------------------------------------------------
current_step="Locating SPIDER checkout"

script_dir="$(cd "$(dirname "$0")" && pwd)"
default_repo_root="$(dirname "$script_dir")"

if [[ -n "${1:-}" ]]; then
    workpath="$(portable_abspath "$1")"
else
    workpath="$default_repo_root"
fi

if [[ ! -d "$workpath" ]]; then
    echo "ERROR: SPIDER directory not found at $workpath." >&2
    exit 1
fi

if [[ ! -f "$workpath/Makefile" ]]; then
    echo "ERROR: No Makefile found in $workpath." >&2
    echo "Expected an already-cloned SPIDER checkout." >&2
    exit 1
fi

if [[ ! -x "$workpath/tools/get_petsc.sh" ]]; then
    echo "ERROR: Could not find executable PETSc installer at $workpath/tools/get_petsc.sh." >&2
    echo "Ensure this script lives inside the SPIDER checkout." >&2
    exit 1
fi

workpath="$(portable_realpath "$workpath")"

# -----------------------------------------------------------------------------
# 3. Set up logging
# -----------------------------------------------------------------------------
current_step="Setting up logging"

log_dir="$workpath/logs"
mkdir -p "$log_dir"
timestamp="$(date +%Y%m%d-%H%M%S)"
logfile="$log_dir/get_spider-$timestamp.log"

exec >>"$logfile" 2>&1

announce "Logging SPIDER build to: $logfile"

# -----------------------------------------------------------------------------
# 4. Locate or bootstrap PETSc installation
# -----------------------------------------------------------------------------
current_step="Validating PETSc installation"

if [[ -n "${PETSC_DIR:-}" ]]; then
    petsc_path="$PETSC_DIR"
else
    petsc_path="$(default_petsc_path_for_repo "$workpath")"
fi

if ! petsc_built_ok "$petsc_path" "$PETSC_ARCH"; then
    current_step="Installing PETSc via tools/get_petsc.sh"
    announce "PETSc not found (or incomplete) at $petsc_path"
    announce "Bootstrapping PETSc first..."
    announce "The PETSc installer will create its own log file."
    "$workpath/tools/get_petsc.sh" "$petsc_path"
    current_step="Validating PETSc installation"
fi

if ! petsc_built_ok "$petsc_path" "$PETSC_ARCH"; then
    echo "ERROR: PETSc library/configuration files not found after installation." >&2
    echo "Checked: $petsc_path" >&2
    exit 1
fi

export PETSC_DIR="$(portable_realpath "$petsc_path")"
export PETSC_ARCH

announce "PETSC_DIR  = $PETSC_DIR"
announce "PETSC_ARCH = $PETSC_ARCH"

# -----------------------------------------------------------------------------
# 5. macOS-specific environment setup
# -----------------------------------------------------------------------------
if [[ "$OSTYPE" == darwin* ]]; then
    if command -v xcrun >/dev/null 2>&1; then
        export SDKROOT
        SDKROOT="$(xcrun --show-sdk-path)"
        announce "SDKROOT    = $SDKROOT"
    fi
fi

# -----------------------------------------------------------------------------
# 6. Verify build tools are available
# -----------------------------------------------------------------------------
current_step="Verifying build tools"

for cmd in python3 make; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: Required command '$cmd' not found in PATH." >&2
        exit 1
    fi
done

if ! command -v mpicc >/dev/null 2>&1; then
    announce "WARNING: mpicc not found in PATH."
    announce "         This is fine if PETSc was built with downloaded MPICH and the"
    announce "         wrapper is available through PETSc's build rules during make."
fi

# -----------------------------------------------------------------------------
# 7. Build SPIDER
# -----------------------------------------------------------------------------
current_step="Building SPIDER (make)"

if command -v nproc >/dev/null 2>&1; then
    njobs="$(nproc)"
elif command -v sysctl >/dev/null 2>&1; then
    njobs="$(sysctl -n hw.ncpu)"
else
    njobs=2
fi

announce ""
announce "Building SPIDER in $workpath ($njobs parallel jobs)..."
olddir="$(pwd)"
cd "$workpath"

make -j "$njobs"

# -----------------------------------------------------------------------------
# 8. Verify the build produced the SPIDER binary
# -----------------------------------------------------------------------------
current_step="Verifying SPIDER binary"

if [[ ! -x "$workpath/spider" ]]; then
    echo "ERROR: SPIDER binary not found after build." >&2
    echo "Check the build output in the log file." >&2
    cd "$olddir"
    exit 1
fi

spider_version="$("$workpath/spider" --help 2>&1 | head -1 || true)"
announce ""
announce "Build successful: $spider_version"

# -----------------------------------------------------------------------------
# 9. Done
# -----------------------------------------------------------------------------
cd "$olddir"

announce ""
announce "========================================"
announce " SPIDER installation complete."
announce ""
announce " Binary: $(portable_realpath "$workpath/spider")"
announce " PETSC_DIR  = $PETSC_DIR"
announce " PETSC_ARCH = $PETSC_ARCH"
announce " Log file:  $logfile"
announce "========================================"