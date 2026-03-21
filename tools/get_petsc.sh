#!/usr/bin/env bash
# =============================================================================
# get_petsc.sh — Download, configure, and compile PETSc for SPIDER
# =============================================================================
#
# Downloads PETSc 3.19.0 from OSF and builds it with sundials2 support.
# SPIDER is a pure C code, so C++ and Fortran compilers are disabled.
#
# This script is intended to live inside the SPIDER repository:
#
#   SPIDER/
#   ├── tools/
#   │   └── get_petsc.sh
#   ├── Makefile
#   └── ...
#
# Default install locations:
#   - Standalone clone: <something>/SPIDER/petsc/
#   - Nested clone:     <something>/PROTEUS/petsc/
#
# An optional first argument may be supplied to choose a different PETSc path.
# The argument is interpreted as the final PETSc directory itself:
#
#   ./tools/get_petsc.sh
#   ./tools/get_petsc.sh /path/to/petsc
#
# Supported platforms:
#   - macOS 10.15 (Catalina) and later, Intel and Apple Silicon
#   - Linux (Ubuntu, Debian, Fedora/RHEL, HPC clusters)
#
# Prerequisites:
#   macOS:  brew install gcc open-mpi
#           xcode-select --install
#   Ubuntu: sudo apt install build-essential libopenmpi-dev unzip curl
#   Fedora: sudo dnf install gcc openmpi openmpi-devel lapack lapack-devel \
#               lapack-static f2c f2c-libs unzip curl
#
# Environment after completion:
#   PETSC_DIR  = <install path>
#   PETSC_ARCH = arch-{linux,darwin}-c-opt
#
# =============================================================================

set -euo pipefail

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

# -----------------------------------------------------------------------------
# Repository layout helper
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

# -----------------------------------------------------------------------------
# Error handling: report which step failed on any non-zero exit
# -----------------------------------------------------------------------------
current_step="initialising"
url="https://osf.io/download/p5vxq/"

on_error() {
    local rc=$?  # must be first line — captures the failing command's exit code
    echo ""
    echo "========================================"
    echo " ERROR: PETSc installation failed"
    echo ""
    echo " Step that failed: $current_step"
    echo " Command:          $BASH_COMMAND"
    echo " Exit code:        $rc"
    echo ""
    echo " Troubleshooting:"
    case "$current_step" in
        *"Download"*)
            echo "   - Check your internet connection"
            echo "   - Verify the OSF URL is accessible: $url"
            echo "   - Try downloading manually: curl -LsS $url > petsc.zip"
            ;;
        *"Decompress"*)
            echo "   - The downloaded archive may be corrupted"
            echo "   - Delete the PETSc directory and re-run this script"
            ;;
        *"Configure"*)
            echo "   - Check PETSc configure output above for details"
            echo "   - On macOS: ensure Xcode CLI tools are installed (xcode-select --install)"
            echo "   - Verify MPI is installed (mpicc --version)"
            ;;
        *"Build"*)
            echo "   - Check PETSc build output above for compiler errors"
            echo "   - Ensure your C compiler is working (mpicc --version)"
            echo "   - On macOS: verify SDKROOT is set (xcrun --show-sdk-path)"
            ;;
        *"Test"*)
            echo "   - PETSc built but tests failed"
            echo "   - Check the test output above for details"
            echo "   - On macOS: check /etc/hosts for localhost entry"
            ;;
        *)
            echo "   - Review the output above for the failing command"
            ;;
    esac
    echo "========================================"
}
trap on_error ERR

# -----------------------------------------------------------------------------
# 1. Detect platform and set PETSC_ARCH
# -----------------------------------------------------------------------------
current_step="Detecting platform"

if [[ "$OSTYPE" == "linux"* ]]; then
    export PETSC_ARCH=arch-linux-c-opt
elif [[ "$OSTYPE" == "darwin"* ]]; then
    export PETSC_ARCH=arch-darwin-c-opt
else
    echo "ERROR: Unsupported OS type '$OSTYPE'. Only Linux and macOS are supported."
    exit 1
fi

# -----------------------------------------------------------------------------
# 2. Determine SPIDER repo root and target PETSc directory
# -----------------------------------------------------------------------------
current_step="Setting up working directory"

# Derive the repo root from this script's location (tools/get_petsc.sh).
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(dirname "$script_dir")"

# Optional argument is the final PETSc directory itself.
if [[ $# -ge 1 ]]; then
    mkdir -p "$1"
    workpath="$(portable_realpath "$1")"
else
    workpath="$(default_petsc_path_for_repo "$repo_root")"
fi

export PETSC_DIR="$workpath"
echo "PETSC_DIR  = $PETSC_DIR"
echo "PETSC_ARCH = $PETSC_ARCH"

# Clean previous installation
rm -rf "$workpath"
mkdir -p "$workpath"

# -----------------------------------------------------------------------------
# 3. Download PETSc 3.19.0 from OSF
# -----------------------------------------------------------------------------
current_step="Downloading PETSc archive from OSF"

zipfile="$workpath/petsc.zip"
echo "Downloading PETSc archive from OSF..."
echo "    $url -> $zipfile"
curl -LsS "$url" > "$zipfile"

current_step="Decompressing PETSc archive"
echo "Decompressing..."
unzip -qq "$zipfile" -d "$workpath"
rm -f "$zipfile"

# -----------------------------------------------------------------------------
# 4. Determine platform-specific configure flags
# -----------------------------------------------------------------------------
current_step="Determining platform-specific flags"

# Defaults assume a generic Linux system without system MPI or BLAS/LAPACK.
mpi_flag="--download-mpich"
blas_flag="--download-f2cblaslapack"
ldflags=""
cflags=""

# ---- Linux special cases ----------------------------------------------------
if [[ "$OSTYPE" == "linux"* ]]; then
    host="$(hostname -f 2>/dev/null || hostname)"

    # Snellius HPC cluster: use the cluster's MPI (loaded via module)
    if [[ "$host" == *"snellius"* ]]; then
        echo "    Detected Snellius cluster — using system MPI"
        mpi_flag=""

    # Habrok / RUG cluster
    elif [[ "$host" == *"hpc.rug.nl" ]]; then
        echo "    Detected Habrok cluster"

    # Fedora / RHEL / Rocky
    elif [[ -f "/etc/fedora-release" || -f "/etc/redhat-release" ]]; then
        echo "    Detected Fedora/RHEL"
        if command -v mpicc >/dev/null 2>&1; then
            echo "    Found system MPI ($(command -v mpicc)) — skipping mpich download"
            mpi_flag=""
        else
            echo "    mpicc not in PATH — will download MPICH"
        fi
        blas_flag=""
        cflags="-fPIC -Wno-error=format-security -Wno-lto-type-mismatch -Wno-stringop-overflow"

    # Generic Linux
    elif command -v mpicc >/dev/null 2>&1; then
        echo "    Found system MPI ($(command -v mpicc)) — skipping mpich download"
        mpi_flag=""
    fi
fi

# ---- macOS ------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v xcrun >/dev/null 2>&1; then
        echo "ERROR: xcrun not found. Install Xcode Command Line Tools:"
        echo "    xcode-select --install"
        exit 1
    fi

    export SDKROOT
    SDKROOT="$(xcrun --show-sdk-path)"
    echo "    SDKROOT = $SDKROOT"

    if command -v mpicc >/dev/null 2>&1; then
        echo "    Found system MPI ($(command -v mpicc)) — skipping mpich download"
        mpi_flag=""
    else
        echo "WARNING: mpicc not found. Install MPI via Homebrew:"
        echo "    brew install open-mpi"
        echo "Falling back to --download-mpich"
    fi

    # macOS provides Accelerate framework with BLAS/LAPACK
    blas_flag=""

    if [[ "$(uname -m)" == "arm64" ]]; then
        default_brew_prefix="/opt/homebrew"
    else
        default_brew_prefix="/usr/local"
    fi
    brew_prefix="$(brew --prefix 2>/dev/null || echo "$default_brew_prefix")"
    ldflags="-L${brew_prefix}/lib -Wl,-w"
fi

# Final check: if we skipped mpich download, mpicc/mpirun must be available
if [[ -z "$mpi_flag" ]] && ! command -v mpirun >/dev/null 2>&1; then
    echo "ERROR: MPI not found and --download-mpich was disabled."
    echo "Install MPI first (e.g. 'brew install open-mpi' or 'apt install libopenmpi-dev')."
    exit 1
fi

# -----------------------------------------------------------------------------
# 5. Configure PETSc
# -----------------------------------------------------------------------------
current_step="Configuring PETSc (./configure)"

echo ""
echo "Configuring PETSc..."
echo "    MPI:     ${mpi_flag:-system}"
echo "    BLAS:    ${blas_flag:-system}"
echo "    CFLAGS:  ${cflags:-<none>}"
echo "    LDFLAGS: ${ldflags:-<none>}"

olddir="$(pwd)"
cd "$workpath"

./configure \
    --with-debugging=0 \
    --with-fc=0 \
    --with-cxx=0 \
    --download-sundials2 \
    --COPTFLAGS="-g -O3" \
    $mpi_flag \
    $blas_flag \
    ${cflags:+"CFLAGS=$cflags"} \
    ${ldflags:+"LDFLAGS=$ldflags"}

# -----------------------------------------------------------------------------
# 6. Build PETSc
# -----------------------------------------------------------------------------
current_step="Building PETSc (make all)"

ncpu=4

echo ""
echo "Building PETSc with $ncpu CPUs..."
make PETSC_DIR="$PETSC_DIR" PETSC_ARCH="$PETSC_ARCH" -j "$ncpu" all

# -----------------------------------------------------------------------------
# 7. Run PETSc self-tests
# -----------------------------------------------------------------------------
current_step="Testing PETSc (make check)"

echo ""
echo "Testing PETSc..."
make PETSC_DIR="$PETSC_DIR" PETSC_ARCH="$PETSC_ARCH" check

# -----------------------------------------------------------------------------
# 8. Done
# -----------------------------------------------------------------------------
cd "$olddir"

echo ""
echo "========================================"
echo " PETSc installation complete."
echo ""
echo " PETSC_DIR  = $PETSC_DIR"
echo " PETSC_ARCH = $PETSC_ARCH"
echo ""
echo " Add these to your shell config if you"
echo " need to rebuild SPIDER manually:"
echo "   export PETSC_DIR=$PETSC_DIR"
echo "   export PETSC_ARCH=$PETSC_ARCH"
echo "========================================"