#!/usr/bin/env bash
# =============================================================================
# get_petsc.sh — Download, configure, and compile PETSc for SPIDER
# =============================================================================
#
# Downloads PETSc 3.24.5 and builds it with sundials2 support.
# SPIDER is a pure C code, so C++ and Fortran compilers are disabled.
#
# This script lives inside the SPIDER repository:
#
#   SPIDER/
#   ├── tools/
#   │   └── get_petsc.sh
#   ├── Makefile
#   └── ...
#
# By default, PETSc is installed into a versioned source directory:
#
#   <SPIDER repo>/petsc-3.24.5/
#
# An optional first argument may be supplied to choose a different base path:
#
#   bash tools/get_petsc.sh           # install into ./petsc-3.24.5/
#   bash tools/get_petsc.sh /path     # install into /path/petsc-3.24.5/
#
# Supported platforms:
#   - macOS 10.15 (Catalina) and later, Intel and Apple Silicon
#   - Linux (Ubuntu, Debian, Fedora/RHEL, HPC clusters)
#
# Prerequisites:
#   macOS:  brew install gcc open-mpi
#           xcode-select --install
#   Ubuntu: sudo apt install build-essential libopenmpi-dev tar curl
#   Fedora: sudo dnf install gcc openmpi openmpi-devel lapack lapack-devel \
#               lapack-static f2c f2c-libs tar curl
#
# Environment after completion:
#   PETSC_DIR  = <install path>/petsc-3.24.5
#   PETSC_ARCH = arch-{linux,darwin}-c-opt
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
            echo "   - Verify the PETSc URL is accessible: $url"
            echo "   - Try downloading manually: curl -LsS -o petsc.tar.gz $url"
            ;;
        *"Decompress"*)
            echo "   - The downloaded archive may be corrupted"
            echo "   - Delete any previous petsc-* source directory and re-run this script"
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
# 2. Determine SPIDER repo root and set up working directory
# -----------------------------------------------------------------------------
current_step="Setting up working directory"

# Derive the repo root from this script's location (tools/get_petsc.sh).
# This avoids dependence on the caller's current working directory.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(dirname "$script_dir")"

# Default: install PETSc into <repo_root>/petsc-<version>/.
# Optional argument: install into <arg>/petsc-<version>/.
if [[ $# -ge 1 ]]; then
    mkdir -p "$1"
    install_base="$(portable_realpath "$1")"
else
    install_base="$repo_root"
fi

echo "PETSC_ARCH = $PETSC_ARCH"

# -----------------------------------------------------------------------------
# 3. Download PETSc release tarball
# -----------------------------------------------------------------------------
current_step="Downloading PETSc release tarball"

archive="$install_base/petsc-${petsc_version}.tar.gz"
srcdir="$install_base/petsc-${petsc_version}"
url="https://web.cels.anl.gov/projects/petsc/download/release-snapshots/petsc-${petsc_version}.tar.gz"

echo "Downloading PETSc ${petsc_version} release tarball..."
echo "    $url -> $archive"

rm -f "$archive"
rm -rf "$srcdir"

curl -LsS "$url" -o "$archive"

current_step="Decompressing PETSc archive"
echo "Decompressing..."
tar -xzf "$archive" -C "$install_base"
rm -f "$archive"

# PETSc release tarballs extract into a versioned source directory.
# Use that extracted directory as PETSC_DIR.
workpath="$srcdir"
export PETSC_DIR="$workpath"

echo "PETSC_DIR  = $PETSC_DIR"
echo "PETSC_ARCH = $PETSC_ARCH"

# -----------------------------------------------------------------------------
# 4. Determine platform-specific configure flags
# -----------------------------------------------------------------------------
current_step="Determining platform-specific flags"

# These variables collect optional flags that vary by platform.
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

    # Habrok cluster: keep default behavior and download both MPI and BLAS/LAPACK.
    elif [[ "$host" == *"hpc.rug.nl" ]]; then
        echo "    Detected Habrok cluster — downloading BLAS and MPI"

    # Fedora / RHEL / Rocky: system packages often provide MPI and BLAS/LAPACK.
    # Only skip MPI download if mpicc is actually available on PATH.
    elif [[ -f "/etc/fedora-release" || -f "/etc/redhat-release" ]]; then
        echo "    Detected Fedora/RHEL"
        if command -v mpicc >/dev/null 2>&1; then
            echo "    Found system MPI ($(which mpicc)) — skipping mpich download"
            mpi_flag=""
        else
            echo "    mpicc not in PATH — will download MPICH"
        fi
        blas_flag=""

        # RHEL/Rocky toolchains may enable warnings that break sundials2 or
        # PETSc configure tests. Suppress the problematic ones.
        cflags="-fPIC -Wno-error=format-security -Wno-lto-type-mismatch -Wno-stringop-overflow"

    # Generic Linux: if mpicc is available, prefer system MPI over download.
    elif command -v mpicc >/dev/null 2>&1; then
        echo "    Found system MPI ($(which mpicc)) — skipping mpich download"
        mpi_flag=""
    fi
fi

# ---- macOS ------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then

    # Verify Xcode Command Line Tools are installed (provides system headers)
    if ! command -v xcrun >/dev/null 2>&1; then
        echo "ERROR: xcrun not found. Install Xcode Command Line Tools:"
        echo "    xcode-select --install"
        exit 1
    fi

    # Set SDKROOT so the compiler can find macOS system headers.
    # Required on Catalina+ where headers are no longer in /usr/include.
    export SDKROOT
    SDKROOT="$(xcrun --show-sdk-path)"
    echo "    SDKROOT = $SDKROOT"

    # Use Homebrew's MPI if available (both Intel and Apple Silicon paths)
    if command -v mpicc >/dev/null 2>&1; then
        echo "    Found system MPI ($(which mpicc)) — skipping mpich download"
        mpi_flag=""
    else
        echo "WARNING: mpicc not found. Install MPI via Homebrew:"
        echo "    brew install open-mpi"
        echo "Falling back to --download-mpich"
    fi

    # macOS provides Accelerate framework with BLAS/LAPACK; no download needed
    blas_flag=""

    # Suppress deprecated linker warnings that can break PETSc configure checks.
    # macOS 13+ / Xcode 15+ deprecated -bind_at_load and -multiply_defined;
    # macOS 26+ / clang 17+ treats these warnings as errors in PETSc's
    # configure runtime tests (checkStdC). The -Wl,-w flag suppresses all
    # linker warnings, allowing configure to complete.
    # Homebrew prefix differs by architecture:
    #   Apple Silicon (arm64): /opt/homebrew
    #   Intel (x86_64):        /usr/local
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
# Key flags:
#   --with-fc=0   : disable Fortran (SPIDER does not use Fortran)
#   --with-cxx=0  : disable C++ (SPIDER is pure C)
#   --download-sundials2 : required by SPIDER for ODE integration
#   --COPTFLAGS   : optimization flags for the C compiler
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

# Number of processes to use for `make all`; fixed at a reasonable number.
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