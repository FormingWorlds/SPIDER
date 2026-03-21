# Installation with quadruple precision

Quadruple precision is useful for numerically demanding cases, but it is not the default installation path.

!!! warning
    The `./tools/get_spider.sh` and `./tools/get_petsc.sh` workflow described above installs the standard double-precision version of SPIDER. To build SPIDER with quadruple precision, you currently need to install SUNDIALS and PETSc manually with quadruple-precision support first, and then build SPIDER against that installation.

## What is different from the standard install?

For quadruple precision:

- you need a **real GCC compiler**, not Apple Clang on macOS;
- you need a **separate quadruple-precision SUNDIALS build**;
- you then configure PETSc with `--with-precision=__float128` and point it to that SUNDIALS installation;
- finally, you build SPIDER with `PETSC_DIR` and `PETSC_ARCH` set to that PETSc build.

## 1. Check that your compiler supports quadruple precision

The SPIDER docs note that quadruple precision requires a GCC compiler. On macOS, `gcc` often points to Apple Clang, which does **not** provide GNU quadruple-precision support.

Check your compiler:

```bash
gcc --version
```

If the output mentions **Apple LLVM**, install GCC separately and use that compiler binary instead.

A simple test is:

```bash
echo '#include<stdio.h>' > t.c && \
echo '#include<quadmath.h>' >> t.c && \
echo 'int main(){printf("It seems to work!\n");}' >> t.c && \
gcc t.c && ./a.out && rm -f t.c a.out
```

If that fails, your current compiler is not suitable for the quadruple-precision build.

## 2. Install SUNDIALS with quadruple precision

For quadruple precision, SPIDER uses a modified SUNDIALS build rather than PETSc’s default downloaded copy. The documented workflow is: clone the modified SUNDIALS repository, configure it with CMake, and set `SUNDIALS_PRECISION=quadruple`.

!!! warning "Check that CMake is available"
    Make sure that CMake is available:
    ```bash
    cmake --version
    ```
    If it is not installed, follow the instructions [here](https://cmake.org/download/), or run:

    === "MacPorts"

        ```bash
        sudo port install cmake
        ```

    === "Homebrew"

        ```bash
        brew install cmake
        ```

    === "Ubuntu / Debian"

        ```bash
        sudo apt-get install cmake
        ```

```bash
cd /somewhere/to/install
mkdir -p sundials-quad
cd sundials-quad

git clone https://bitbucket.org/psanan/sundials-quad src
mkdir install build
cd build
cmake ../src
ccmake .
```

In `ccmake`, set values similar to:

!!! note "Using the ccmake interface"
    When using the ``ccmake` interface, make sure you type "c" to configure once you have entered these values, then "g" to generate and exit.

```
CMAKE_C_COMPILER: gcc
CMAKE_INSTALL_PREFIX: ../install
EXAMPLES_INSTALL_PATH: ../install/examples
SUNDIALS_PRECISION: quadruple
```

Then build and install:

```
make && make install
```

!!! note "C compiler"
    Use the same C compiler here that you will use for PETSc.

## 3. Install PETSc with quadruple precision

Install the pinned snapshot if interested in reproducing previous results. Otherwise, install PETSc 3.19.

=== "Pinned SPIDER-documented commit"

    ```bash
    cd /somewhere/to/install
    git clone https://gitlab.com/petsc/petsc -b main petsc-quad
    cd petsc-quad
    git checkout 63b725033a15f75ded7183cf5f88ec748e60783b
    ```

=== "PETSc 3.19"

    ```bash
    cd /somewhere/to/install
    git clone https://gitlab.com/petsc/petsc petsc-3.19
    cd petsc-3.19
    git checkout v3.19.6
    ```

Configure it against the SUNDIALS installation you just built:

```bash
./configure \
  --with-debugging=0 \
  --with-fc=0 \
  --with-cxx=0 \
  --with-cc=gcc \
  --with-precision=__float128 \
  --with-sundials=1 \
  --with-sundials-dir=/somewhere/to/install/sundials-quad/install \
  --download-mpich \
  --download-f2cblaslapack \
  --COPTFLAGS="-g -O3" \
  --CXXOPTFLAGS="-g -O3"
```

Then follow PETSc’s terminal instructions to complete the build, and export the environment it reports:

```bash
export PETSC_DIR=/somewhere/to/install/petsc-quad
export PETSC_ARCH=arch-xxx-yyy
```

## 4. Build SPIDER against the quadruple-precision PETSc

Once `PETSC_DIR` and `PETSC_ARCH` point to your quadruple-precision PETSc build, build SPIDER normally:

```bash
cd /somewhere/to/install
git clone https://github.com/FormingWorlds/SPIDER.git
cd SPIDER

make clean
make -j
```

Then test your installation by following the steps in the [testing guide](test.md).