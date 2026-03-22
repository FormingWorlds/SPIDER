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
# Logs:
#   Full build logs are written to:
#     <parent of PETSc dir>/logs/get_petsc-YYYYmmdd-HHMMSS.log
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
# Safety guard for destructive operations
# -----------------------------------------------------------------------------
safe_to_remove_dir() {
    local target="$1"
    local resolved

    [[ -n "$target" ]] || return 1
    resolved="$(portable_realpath "$target")"

    case "$resolved" in
        /|/home|/root|"${HOME}"|.)
            return 1
            ;;
    esac

    # Refuse very short paths
    [[ "${#resolved}" -ge 10 ]] || return 1

    # This installer should only ever remove a PETSc directory
    [[ "$(basename "$resolved")" == "petsc" ]] || return 1

    return 0
}

# -----------------------------------------------------------------------------
# Error handling: report which step failed on any non-zero exit
# -----------------------------------------------------------------------------
current_step="initialising"
url="https://osf.io/download/p5vxq/"
logfile=""

on_error() {
    local rc=$?

    console ""
    console "========================================"
    console " ERROR: PETSc installation failed"
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
        *"required tools"*)
            console "   - Install the missing prerequisite and re-run the script"
            console "   - On minimal HPC/login nodes, load any needed modules first"
            ;;
        *"Preparing PETSc directory"*)
            console "   - The target directory may have been rejected by the safety guard"
            console "   - Check that the install path is correct and ends in 'petsc'"
            console "   - Refused paths include '/', '$HOME', '.', and very short paths"
            ;;
        *"Download"*)
            console "   - Check your internet connection"
            console "   - Verify the OSF URL is accessible: $url"
            console "   - Try downloading manually: curl -fLsS \"$url\" -o petsc.zip"
            ;;
        *"Decompress"*)
            console "   - The downloaded archive may be corrupted"
            console "   - Delete the PETSc directory and re-run this script"
            ;;
        *"Configure"*)
            console "   - Check PETSc configure output in the log file"
            console "   - On macOS: ensure Xcode CLI tools are installed (xcode-select --install)"
            console "   - Verify MPI is installed (mpicc --version)"
            ;;
        *"Build"*)
            console "   - Check PETSc build output in the log file"
            console "   - Ensure your C compiler is working (mpicc --version)"
            console "   - On macOS: verify SDKROOT is set (xcrun --show-sdk-path)"
            ;;
        *"Test"*)
            console "   - PETSc built but tests failed"
            console "   - Check the test output in the log file"
            console "   - On macOS: check /etc/hosts for localhost entry"
            ;;
        *)
            console "   - Review the log file for the failing command"
            ;;
    esac

    console "========================================"
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
    echo "ERROR: Unsupported OS type '$OSTYPE'. Only Linux and macOS are supported." >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# 2. Verify required tools are available
# -----------------------------------------------------------------------------
current_step="Verifying required tools"

for cmd in curl unzip make; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: Required command '$cmd' not found in PATH." >&2
        echo "Install it first and re-run this script." >&2
        exit 1
    fi
done

# realpath is optional, but python3 is required as the fallback
if ! command -v realpath >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Neither 'realpath' nor 'python3' was found in PATH." >&2
    echo "Install one of them so the script can resolve paths correctly." >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# 3. Determine SPIDER repo root and target PETSc directory
# -----------------------------------------------------------------------------
current_step="Setting up working directory"

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

# -----------------------------------------------------------------------------
# 4. Set up logging
# -----------------------------------------------------------------------------
current_step="Setting up logging"

log_dir="$(dirname "$workpath")/logs"
mkdir -p "$log_dir"
timestamp="$(date +%Y%m%d-%H%M%S)"
logfile="$log_dir/get_petsc-$timestamp.log"

exec >>"$logfile" 2>&1

announce "Logging PETSc build to: $logfile"
announce "PETSC_DIR  = $PETSC_DIR"
announce "PETSC_ARCH = $PETSC_ARCH"

# -----------------------------------------------------------------------------
# 5. Prepare PETSc directory
# -----------------------------------------------------------------------------
current_step="Preparing PETSc directory"

if [[ -e "$workpath" ]]; then
    if ! safe_to_remove_dir "$workpath"; then
        echo "ERROR: Refusing to remove unsafe path: $workpath" >&2
        exit 1
    fi
    rm -rf "$workpath"
fi
mkdir -p "$workpath"

# -----------------------------------------------------------------------------
# 6. Download PETSc 3.19.0 from OSF
# -----------------------------------------------------------------------------
current_step="Downloading PETSc archive from OSF"

zipfile="$workpath/petsc.zip"
announce ""
announce "Downloading PETSc archive from OSF..."
announce "    $url -> $zipfile"
curl -fLsS "$url" -o "$zipfile"

current_step="Decompressing PETSc archive"
announce "Decompressing..."
unzip -qq "$zipfile" -d "$workpath"
rm -f "$zipfile"

# -----------------------------------------------------------------------------
# 7. Determine platform-specific configure flags
# -----------------------------------------------------------------------------
current_step="Determining platform-specific flags"

mpi_flag="--download-mpich"
blas_flag="--download-f2cblaslapack"
ldflags=""
cflags=""

# ---- Linux special cases ----------------------------------------------------
if [[ "$OSTYPE" == "linux"* ]]; then
    host="$(hostname -f 2>/dev/null || hostname)"

    if [[ "$host" == *"snellius"* ]]; then
        announce "    Detected Snellius cluster — using system MPI"
        mpi_flag=""
    elif [[ "$host" == *"hpc.rug.nl" ]]; then
        announce "    Detected Habrok cluster"
    elif [[ -f "/etc/fedora-release" || -f "/etc/redhat-release" ]]; then
        announce "    Detected Fedora/RHEL"
        if command -v mpicc >/dev/null 2>&1; then
            announce "    Found system MPI ($(command -v mpicc)) — skipping mpich download"
            mpi_flag=""
        else
            announce "    mpicc not in PATH — will download MPICH"
        fi
        blas_flag=""
        cflags="-fPIC -Wno-error=format-security -Wno-lto-type-mismatch -Wno-stringop-overflow"
    elif command -v mpicc >/dev/null 2>&1; then
        announce "    Found system MPI ($(command -v mpicc)) — skipping mpich download"
        mpi_flag=""
    fi
fi

# ---- macOS ------------------------------------------------------------------
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v xcrun >/dev/null 2>&1; then
        echo "ERROR: xcrun not found. Install Xcode Command Line Tools:" >&2
        echo "    xcode-select --install" >&2
        exit 1
    fi

    export SDKROOT
    SDKROOT="$(xcrun --show-sdk-path)"
    announce "    SDKROOT = $SDKROOT"

    if command -v mpicc >/dev/null 2>&1; then
        announce "    Found system MPI ($(command -v mpicc)) — skipping mpich download"
        mpi_flag=""
    else
        announce "WARNING: mpicc not found. Install MPI via Homebrew:"
        announce "    brew install open-mpi"
        announce "Falling back to --download-mpich"
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

if [[ -z "$mpi_flag" ]] && ! command -v mpirun >/dev/null 2>&1; then
    echo "ERROR: MPI not found and --download-mpich was disabled." >&2
    echo "Install MPI first (e.g. 'brew install open-mpi' or 'apt install libopenmpi-dev')." >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# 8. Configure PETSc
# -----------------------------------------------------------------------------
current_step="Configuring PETSc (./configure)"

announce ""
announce "Configuring PETSc..."
announce "    MPI:     ${mpi_flag:-system}"
announce "    BLAS:    ${blas_flag:-system}"
announce "    CFLAGS:  ${cflags:-<none>}"
announce "    LDFLAGS: ${ldflags:-<none>}"

olddir="$(pwd)"
cd "$workpath"

configure_args=(
    --with-debugging=0
    --with-fc=0
    --with-cxx=0
    --download-sundials2
    "--COPTFLAGS=-g -O3"
)

if [[ -n "$mpi_flag" ]]; then
    configure_args+=("$mpi_flag")
fi
if [[ -n "$blas_flag" ]]; then
    configure_args+=("$blas_flag")
fi
if [[ -n "$cflags" ]]; then
    configure_args+=("CFLAGS=$cflags")
fi
if [[ -n "$ldflags" ]]; then
    configure_args+=("LDFLAGS=$ldflags")
fi

./configure "${configure_args[@]}"

# -----------------------------------------------------------------------------
# 9. Build PETSc
# -----------------------------------------------------------------------------
current_step="Building PETSc (make all)"

ncpu=4
announce ""
announce "Building PETSc with $ncpu CPUs..."
make PETSC_DIR="$PETSC_DIR" PETSC_ARCH="$PETSC_ARCH" -j "$ncpu" all

# -----------------------------------------------------------------------------
# 10. Run PETSc self-tests
# -----------------------------------------------------------------------------
current_step="Testing PETSc (make check)"

announce ""
announce "Testing PETSc..."
make PETSC_DIR="$PETSC_DIR" PETSC_ARCH="$PETSC_ARCH" check

# -----------------------------------------------------------------------------
# 11. Done
# -----------------------------------------------------------------------------
cd "$olddir"

announce ""
announce "========================================"
announce " PETSc installation complete."
announce ""
announce " PETSC_DIR  = $PETSC_DIR"
announce " PETSC_ARCH = $PETSC_ARCH"
announce " Log file:  $logfile"
announce ""
announce " Add these to your shell config if you"
announce " need to rebuild SPIDER manually:"
announce "   export PETSC_DIR=$PETSC_DIR"
announce "   export PETSC_ARCH=$PETSC_ARCH"
announce "========================================"