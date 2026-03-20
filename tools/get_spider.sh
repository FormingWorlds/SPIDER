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
# The script is suitable for standalone SPIDER installs, and still behaves
# nicely inside a PROTEUS/SPIDER checkout by installing PETSc in PROTEUS/petsc.
#
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Portable path helpers: macOS <13 (Catalina through Monterey) does not ship
# GNU coreutils realpath. Fall back to python3.
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
on_error() {
    local rc=$?  # must be first line — captures the failing command's exit code
    echo ""
    echo "========================================"
    echo " ERROR: SPIDER installation failed"
    echo ""
    echo " Step that failed: $current_step"
    echo " Command:          $BASH_COMMAND"
    echo " Exit code:        $rc"
    echo ""
    echo " Troubleshooting:"
    case "$current_step" in
        *"PETSc"*)
            echo "   - Check the PETSc installer output above for errors"
            echo "   - Try running ./tools/get_petsc.sh manually first"
            ;;
        *"Building"*)
            echo "   - Check the compiler output above for errors"
            echo "   - Verify mpicc is working: mpicc --version"
            echo "   - Verify PETSc is intact: ls \$PETSC_DIR/\$PETSC_ARCH/lib/libpetsc.*"
            echo "   - On macOS: ensure SDKROOT is set (xcrun --show-sdk-path)"
            ;;
        *"Verif"*)
            echo "   - The build completed without make errors but no binary was produced"
            echo "   - This usually indicates a linker failure that was suppressed"
            echo "   - Try rebuilding with verbose output: make V=1"
            ;;
        *)
            echo "   - See your platform-specific troubleshooting notes"
            ;;
    esac
    echo ""
    echo " PETSc environment used:"
    echo "   PETSC_DIR  = ${PETSC_DIR:-<not set>}"
    echo "   PETSC_ARCH = ${PETSC_ARCH:-<not set>}"
    echo "========================================"
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
    echo "ERROR: Unsupported OS type '$OSTYPE'. Only Linux and macOS are supported."
    exit 1
fi

# -----------------------------------------------------------------------------
# 2. Locate SPIDER checkout to build
# -----------------------------------------------------------------------------
current_step="Locating SPIDER checkout"

# Derive the current repository root from this script's location.
script_dir="$(cd "$(dirname "$0")" && pwd)"
default_repo_root="$(dirname "$script_dir")"

# Default build target is the current checkout; override via first argument.
if [[ -n "${1:-}" ]]; then
    workpath="$(portable_abspath "$1")"
else
    workpath="$default_repo_root"
fi

if [[ ! -d "$workpath" ]]; then
    echo "ERROR: SPIDER directory not found at $workpath."
    exit 1
fi

if [[ ! -f "$workpath/Makefile" ]]; then
    echo "ERROR: No Makefile found in $workpath."
    echo "Expected an already-cloned SPIDER checkout."
    exit 1
fi

if [[ ! -x "$workpath/tools/get_petsc.sh" ]]; then
    echo "ERROR: Could not find executable PETSc installer at $workpath/tools/get_petsc.sh."
    echo "Ensure this script lives inside the SPIDER checkout."
    exit 1
fi

workpath="$(portable_realpath "$workpath")"

# -----------------------------------------------------------------------------
# 3. Locate or bootstrap PETSc installation
# -----------------------------------------------------------------------------
current_step="Validating PETSc installation"

# Honour PETSC_DIR if the user already exported it; otherwise derive a sensible
# default from the repository layout.
if [[ -n "${PETSC_DIR:-}" ]]; then
    petsc_path="$PETSC_DIR"
else
    petsc_path="$(default_petsc_path_for_repo "$workpath")"
fi

# If PETSc is missing or incomplete, install it automatically first.
if ! petsc_built_ok "$petsc_path" "$PETSC_ARCH"; then
    current_step="Installing PETSc via tools/get_petsc.sh"
    echo "PETSc not found (or incomplete) at $petsc_path"
    echo "Bootstrapping PETSc first..."
    "$workpath/tools/get_petsc.sh" "$petsc_path"
    current_step="Validating PETSc installation"
fi

if ! petsc_built_ok "$petsc_path" "$PETSC_ARCH"; then
    echo "ERROR: PETSc library/configuration files not found after installation."
    echo "Checked: $petsc_path"
    exit 1
fi

export PETSC_DIR="$(portable_realpath "$petsc_path")"
export PETSC_ARCH

echo "PETSC_DIR  = $PETSC_DIR"
echo "PETSC_ARCH = $PETSC_ARCH"

# -----------------------------------------------------------------------------
# 4. macOS-specific environment setup
# -----------------------------------------------------------------------------
if [[ "$OSTYPE" == darwin* ]]; then
    # Set SDKROOT so the compiler can find macOS system headers.
    # Required on Catalina+ where headers are no longer in /usr/include.
    if command -v xcrun >/dev/null 2>&1; then
        export SDKROOT
        SDKROOT=$(xcrun --show-sdk-path)
        echo "SDKROOT    = $SDKROOT"
    fi
fi

# -----------------------------------------------------------------------------
# 5. Verify build tools are available
# -----------------------------------------------------------------------------
current_step="Verifying build tools"

for cmd in python3 make; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: Required command '$cmd' not found in PATH."
        exit 1
    fi
done

if ! command -v mpicc >/dev/null 2>&1; then
    echo "WARNING: mpicc not found in PATH."
    echo "         This is fine if PETSc was built with downloaded MPICH and the"
    echo "         wrapper is available through PETSc's build rules during make."
fi

# -----------------------------------------------------------------------------
# 6. Build SPIDER
# -----------------------------------------------------------------------------
current_step="Building SPIDER (make)"

# Determine number of parallel jobs.
# Uses nproc (Linux) or sysctl (macOS) to detect available CPU cores.
if command -v nproc >/dev/null 2>&1; then
    njobs=$(nproc)
elif command -v sysctl >/dev/null 2>&1; then
    njobs=$(sysctl -n hw.ncpu)
else
    njobs=2
fi

echo ""
echo "Building SPIDER in $workpath ($njobs parallel jobs)..."
olddir=$(pwd)
cd "$workpath"

make -j "$njobs"

# -----------------------------------------------------------------------------
# 7. Verify the build produced the SPIDER binary
# -----------------------------------------------------------------------------
current_step="Verifying SPIDER binary"

if [[ ! -x "$workpath/spider" ]]; then
    echo "ERROR: SPIDER binary not found after build."
    echo "Check the build output above for compilation errors."
    cd "$olddir"
    exit 1
fi

spider_version=$("$workpath/spider" --help 2>&1 | head -1 || true)
echo ""
echo "Build successful: $spider_version"

# -----------------------------------------------------------------------------
# 8. Done
# -----------------------------------------------------------------------------
cd "$olddir"

echo ""
echo "========================================"
echo " SPIDER installation complete."
echo ""
echo " Binary: $(portable_realpath "$workpath/spider")"
echo " PETSC_DIR  = $PETSC_DIR"
echo " PETSC_ARCH = $PETSC_ARCH"
echo "========================================"
