# SPIDER: installation

!!! note
    The standard way of installing this version of SPIDER is within the PROTEUS Framework, as described in the [PROTEUS installation guide](https://proteus-framework.org/PROTEUS/installation.html#11-setup-spider-interior-evolution-model).

## Quick installation

Here we provide a short installation guide to get you up and running with SPIDER.

!!! info "Quadruple precision"
    To install SPIDER manually with quadruple precision, follow [this guide](quadruple_installation.md).

The recommended workflow is:

1. Set up a Conda environment
2. Clone SPIDER
3. Run the installer from inside the SPIDER checkout
4. The installer will automatically install PETSc first if it is missing
5. Then it will build SPIDER against that PETSc installation

!!! info "Are you in PROTEUS?"
    When SPIDER is located at `PROTEUS/SPIDER`, PETSc is installed automatically into `PROTEUS/petsc`. When SPIDER is cloned standalone, PETSc is installed automatically into `SPIDER/petsc`.

### 0. Prerequisites

You need:

- a working C compiler;
- `make`;
- `git`;
- MPI compiler wrappers available via `mpicc`, or permission for PETSc to download MPICH automatically.
- About 20 minutes of your time. 

A basic test to check you have a working compiler is:

```bash
echo '#include<stdio.h>' > t.c && echo 'int main(){printf("It seems to work!\n");}' >> t.c && gcc t.c && ./a.out && rm -f t.c a.out
```

To ensure you have everything installed, run:

=== "Ubuntu / Debian"

    ```bash
    sudo apt install build-essential git libopenmpi-dev
    ```

=== "Fedora / RHEL"

    ```bash
    sudo dnf install gcc git openmpi openmpi-devel lapack lapack-devel lapack-static f2c f2c-libs
    ```

=== "macOS (Homebrew)"

    ```zsh
    brew install gcc open-mpi
    xcode-select --install
    ```

!!! note "HPC clusters"

    On HPC clusters you usually **do not have sudo access**. In that case:

    1. Load any compiler / MPI modules provided by your cluster, for example:

    ```bash
    module avail
    module load gcc
    module load openmpi
    ```

### 1. Create a Conda environment [optional]

If you use Conda, it is recommended to build and run SPIDER inside a dedicated environment. This keeps the Python dependencies for SPIDER and optional tools such as SciATH separate from your base environment.

Create and activate a Python 3.12 environment:

```bash
conda create -n spider python=3.12
conda activate spider
``` 

!!! Note
    This Conda environment manages Python packages only. SPIDER itself is compiled with make, and PETSc is built by `./tools/get_spider.sh`.

### 2. Clone SPIDER

```bash
cd /somewhere/to/install
git clone https://github.com/FormingWorlds/SPIDER.git
cd SPIDER
```

### 3. Run the installer

```bash
./tools/get_spider.sh
```

If the installation succeeds, the SPIDER executable will be available at:

```bash
./spider
```

The PETSc environment used for the build will be reported by the installer, for example:

```
PETSC_DIR=/somewhere/to/install/petsc
PETSC_ARCH=arch-xxx-yyy
```
!!! info "PETSc environment"
    `./tools/get_spider.sh` sets `PETSC_DIR` and `PETSC_ARCH` automatically for installation. You only need to export them yourself if you want to rebuild or test SPIDER manually in a new shell session, like this:

    ```bash
    export PETSC_DIR=/somewhere/to/install/petsc
    export PETSC_ARCH=arch-xxx-yyy
    ```

