#!/usr/bin/env bash
# =============================================================================
# install_spider.sh — Compile SPIDER against a local or external PETSc install
# =============================================================================
#
# Builds the current SPIDER checkout in-place. Unlike the PROTEUS helper
# script, this script does not clone SPIDER from GitHub; it assumes it is being
# run from within an existing SPIDER repository.
#
# This script lives inside the SPIDER repository:
#
#   SPIDER/
#   ├── tools/
#   │   └── install_spider.sh
#   ├── Makefile
#   └── ...
#
# PETSc may be provided in either of two ways:
#
#   1. Default local install:
#        <SPIDER repo>/petsc-3.24.5/
#      This is the location created by ./tools/get_petsc.sh
#
#   2. External PETSc install:
#      Set PETSC_DIR and optionally PETSC_ARCH before running this script.
#
# Usage:
#   bash tools/install_spider.sh
#
# Examples:
#   bash tools/get_petsc.sh
#   bash tools/install_spider.sh
#
#   export PETSC_DIR=/path/to/petsc-3.24.5
#   export PETSC_ARCH=arch-linux-c-opt
#   bash tools/install_spider.sh
#
# Supported platforms:
#   - macOS 10.15 (Catalina) and later, Intel and Apple Silicon
#   - Linux (Ubuntu, Debian, Fedora/RHEL, HPC clusters)
#
# Prerequisites:
#   - PETSc must already be configured and built
#   - C compiler accessible via MPI wrapper (mpicc)
#   - make
#
# Environment used by this script:
#   PETSC_DIR  = path to PETSc installation
#   PETSC_ARCH = arch-{linux,darwin}-c-opt unless already set
#
# Output after completion:
#   Binary: <SPIDER repo>/spider
#
# =============================================================================

set -Eeuo pipefail

petsc_version="3.24.5"

# -----------------------------------------------------------------------------
# Portable realpath: macOS <13 (Catalina through Monterey) does not ship
# GNU coreutils realpath. Fall back to python3, which is commonly available.
# -----------------------------------------------------------------------------
portable_realpath() {
    if command -v realpath >/dev/null 2>&1; then
        realpath "$1"
    else
        python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$1"
    fi
}

# -----------------------------------------------------------------------------
# Error handling: report which step failed on any non-zero exit
# -----------------------------------------------------------------------------
current_step="initialising"
on_error() {
    local rc=$?
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
        *"Validating PETSc"*)
            echo "   - Verify PETSc exists at PETSC_DIR"
            echo "   - Check for libpetsc in \$PETSC_DIR/\$PETSC_ARCH/lib"
            echo "   - Re-run bash tools/get_petsc.sh if PETSc is incomplete"
            ;;
        *"Verifying build tools"*)
            echo "   - Ensure mpicc is installed and on PATH"
            echo "   - Ensure make is installed"
            echo "   - On macOS: install MPI with 'brew install open-mpi'"
            ;;
        *"Building"*)
            echo "   - Check the compiler output above for errors"
            echo "   - Verify PETSc is intact: ls \$PETSC_DIR/\$PETSC_ARCH/lib/libpetsc.*"
            echo "   - Verify mpicc is working: mpicc --version"
            echo "   - On macOS: ensure SDKROOT is set (xcrun --show-sdk-path)"
            ;;
        *"Verif"*)
            echo "   - The build completed without make errors but no binary was produced"
            echo "   - This may indicate a linker failure or unexpected Makefile target"
            echo "   - Try rebuilding with verbose output: make V=1"
            ;;
        *)
            echo "   - Review the output above for the failing command"
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
# 1. Determine SPIDER repo root
# -----------------------------------------------------------------------------
current_step="Determining repository root"

# Derive the repo root from this script's location (tools/install_spider.sh).
# This avoids dependence on the caller's current working directory.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(dirname "$script_dir")"

# -----------------------------------------------------------------------------
# 2. Detect platform and determine default PETSC_ARCH
# -----------------------------------------------------------------------------
current_step="Detecting platform"

if [[ "$OSTYPE" == "linux"* ]]; then
    default_petsc_arch="arch-linux-c-opt"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    default_petsc_arch="arch-darwin-c-opt"
else
    echo "ERROR: Unsupported OS type '$OSTYPE'. Only Linux and macOS are supported."
    exit 1
fi

# -----------------------------------------------------------------------------
# 3. Locate and validate PETSc installation
# -----------------------------------------------------------------------------
current_step="Validating PETSc installation"

# If PETSC_DIR is already set in the environment, respect it.
# Otherwise, default to <repo_root>/petsc-<version>, which is where
# get_petsc.sh installs PETSc.
if [[ -n "${PETSC_DIR:-}" ]]; then
    PETSC_DIR="$(portable_realpath "$PETSC_DIR")"
else
    PETSC_DIR="$repo_root/petsc-${petsc_version}"
fi

# If PETSC_ARCH is already set in the environment, respect it.
# Otherwise, use the platform-specific default.
if [[ -n "${PETSC_ARCH:-}" ]]; then
    PETSC_ARCH="$PETSC_ARCH"
else
    PETSC_ARCH="$default_petsc_arch"
fi

export PETSC_DIR
export PETSC_ARCH

echo "PETSC_DIR  = $PETSC_DIR"
echo "PETSC_ARCH = $PETSC_ARCH"

# Verify PETSc directory exists
if [[ ! -d "$PETSC_DIR" ]]; then
    echo "ERROR: PETSc directory not found at $PETSC_DIR."
    echo "Run bash tools/get_petsc.sh first, or set PETSC_DIR explicitly."
    exit 1
fi

# Verify PETSc was actually built (not just downloaded/configured).
# The library name varies by platform:
#   macOS:  libpetsc.dylib
#   Linux:  libpetsc.so or libpetsc.so.X.Y
petsc_lib_dir="$PETSC_DIR/$PETSC_ARCH/lib"
petsc_lib_found=false
for f in "$petsc_lib_dir"/libpetsc.*; do
    if [[ -f "$f" ]]; then
        petsc_lib_found=true
        break
    fi
done
if [[ "$petsc_lib_found" != "true" ]]; then
    echo "ERROR: PETSc library not found in $petsc_lib_dir."
    echo "PETSc may have been downloaded but not compiled successfully."
    echo "Re-run bash tools/get_petsc.sh to rebuild."
    exit 1
fi

# Verify PETSc's Makefile includes exist (required by SPIDER's Makefile)
petsc_conf_dir="$PETSC_DIR/lib/petsc/conf"
if [[ ! -f "$petsc_conf_dir/variables" ]] || \
   [[ ! -f "$petsc_conf_dir/rules" ]]; then
    echo "ERROR: PETSc configuration files not found in $petsc_conf_dir."
    echo "The PETSc installation appears incomplete. Re-run bash tools/get_petsc.sh."
    exit 1
fi

# -----------------------------------------------------------------------------
# 4. macOS-specific environment setup
# -----------------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Set SDKROOT so the compiler can find macOS system headers.
    # Required on Catalina+ where headers are no longer in /usr/include.
    if command -v xcrun >/dev/null 2>&1; then
        export SDKROOT
        SDKROOT="$(xcrun --show-sdk-path)"
        echo "SDKROOT    = $SDKROOT"
    fi
fi

# -----------------------------------------------------------------------------
# 5. Verify build tools are available
# -----------------------------------------------------------------------------
current_step="Verifying build tools"

if ! command -v mpicc >/dev/null 2>&1; then
    echo "ERROR: mpicc not found. A C compiler with MPI support is required."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Install via Homebrew: brew install open-mpi"
    else
        echo "Install via package manager, e.g.: sudo apt install libopenmpi-dev"
    fi
    exit 1
fi

if ! command -v make >/dev/null 2>&1; then
    echo "ERROR: make not found. Install build tools for your platform."
    exit 1
fi

# -----------------------------------------------------------------------------
# 6. Build SPIDER
# -----------------------------------------------------------------------------
current_step="Building SPIDER (make)"

# Determine number of parallel jobs.
# Uses nproc (Linux) or sysctl (macOS) to detect available CPU cores.
if command -v nproc >/dev/null 2>&1; then
    njobs="$(nproc)"
elif command -v sysctl >/dev/null 2>&1; then
    njobs="$(sysctl -n hw.ncpu)"
else
    njobs=2
fi

echo ""
echo "Building SPIDER ($njobs parallel jobs)..."

olddir="$(pwd)"
cd "$repo_root"

make -j "$njobs"

# -----------------------------------------------------------------------------
# 7. Verify the build produced the SPIDER binary
# -----------------------------------------------------------------------------
current_step="Verifying SPIDER binary"

if [[ ! -x "$repo_root/spider" ]]; then
    echo "ERROR: SPIDER binary not found after build."
    echo "Check the build output above for compilation errors."
    cd "$olddir"
    exit 1
fi

spider_version="$("$repo_root/spider" --help 2>&1 | head -1 || true)"
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
echo " Binary: $(portable_realpath "$repo_root/spider")"
echo " PETSC_DIR  = $PETSC_DIR"
echo " PETSC_ARCH = $PETSC_ARCH"
echo "========================================"