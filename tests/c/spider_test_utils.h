#if !defined(SPIDER_TEST_UTILS_H_)
#define SPIDER_TEST_UTILS_H_

/* Shared helpers for the C test executables under tests/c/.
   Each executable evaluates SPIDER functions at probe points supplied
   by its pytest wrapper and prints a single JSON object to stdout.
   Assertions, tolerances, and discrimination guards live in the Python
   wrappers (tests/test_*.py), never here. */

#include <petsc.h>

#include "constants.h"
#include "util.h"

/* Fill the scaling constants from the -entropy0 / -radius0 / -time0 /
   -pressure0 / -volatile0 options, mirroring ScalingConstantsSet and
   ScalingConstantsSetFromOptions in parameters.c (which are static and
   therefore not linkable from here). Keep in sync with parameters.c. */
static PETSC_UNUSED PetscErrorCode SpiderTestScalingConstantsSetFromOptions(ScalingConstants SC)
{
  PetscErrorCode ierr;
  PetscScalar    ENTROPY0, RADIUS0, TIME0, PRESSURE0, VOLATILE0;
  PetscScalar    SQRTST;

  PetscFunctionBeginUser;
  /* PetscOptionsGetPositiveScalar matches the production reads in
     parameters.c, so a nonpositive scaling errors here exactly as it
     would in the binary. */
  ierr = PetscOptionsGetPositiveScalar("-entropy0", &ENTROPY0, 1.0E3, NULL);CHKERRQ(ierr);
  ierr = PetscOptionsGetPositiveScalar("-radius0", &RADIUS0, 1.0E6, NULL);CHKERRQ(ierr);
  ierr = PetscOptionsGetPositiveScalar("-time0", &TIME0, 3.154E7, NULL);CHKERRQ(ierr);
  ierr = PetscOptionsGetPositiveScalar("-pressure0", &PRESSURE0, 1.0E7, NULL);CHKERRQ(ierr);
  ierr = PetscOptionsGetPositiveScalar("-volatile0", &VOLATILE0, 1.0E-10, NULL);CHKERRQ(ierr);

  SC->ENTROPY   = ENTROPY0;
  SC->RADIUS    = RADIUS0;
  SC->TIME      = TIME0;
  SC->PRESSURE  = PRESSURE0;
  SC->VOLATILE  = VOLATILE0;
  SC->AREA      = PetscSqr(SC->RADIUS);
  SC->VOLUME    = SC->AREA * SC->RADIUS;
  SC->TEMP      = PetscSqr(SC->RADIUS / SC->TIME) / SC->ENTROPY;
  SQRTST        = PetscSqrtScalar(SC->ENTROPY * SC->TEMP);
  SC->MASS      = SC->PRESSURE * SC->VOLUME / (SC->ENTROPY * SC->TEMP);
  SC->DENSITY   = SC->PRESSURE / (SC->ENTROPY * SC->TEMP);
  SC->TIMEYRS   = SC->TIME / (60.0 * 60.0 * 24.0 * 365.25);
  SC->SENERGY   = SC->ENTROPY * SC->TEMP;
  SC->ENERGY    = SC->SENERGY * SC->MASS;
  SC->POWER     = SC->ENERGY / SC->TIME;
  SC->FLUX      = SC->POWER / SC->AREA;
  SC->DPDR      = SC->PRESSURE / SC->RADIUS;
  SC->GRAVITY   = SC->ENTROPY * SC->TEMP / SC->RADIUS;
  SC->KAPPA     = SC->RADIUS * SQRTST;
  SC->DSDP      = SC->ENTROPY / SC->PRESSURE;
  SC->DSDR      = SC->ENTROPY / SC->RADIUS;
  SC->DTDP      = SC->TEMP / SC->PRESSURE;
  SC->DTDR      = SC->TEMP / SC->RADIUS;
  SC->GSUPER    = SC->GRAVITY * SC->DTDR;
  SC->VISC      = SC->DENSITY * SC->KAPPA;
  SC->LOG10VISC = PetscLog10Real(SC->VISC);
  SC->COND      = SC->ENTROPY * SC->DENSITY * SC->KAPPA;
  SC->SIGMA     = SC->FLUX * 1.0 / PetscPowScalar(SC->TEMP, 4.0);
  SC->HEATGEN   = PetscPowScalar(SC->ENTROPY * SC->TEMP, 3.0 / 2.0) / SC->RADIUS;

  PetscFunctionReturn(0);
}

/* Print a JSON array of scalars with full double precision. */
static PETSC_UNUSED PetscErrorCode SpiderTestPrintScalarArray(const char *key, const PetscScalar *vals, PetscInt n, PetscBool trailing_comma)
{
  PetscErrorCode ierr;
  PetscInt       i;

  PetscFunctionBeginUser;
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"%s\": [", key);CHKERRQ(ierr);
  for (i = 0; i < n; ++i) {
    ierr = PetscPrintf(PETSC_COMM_WORLD, "%.17g%s", (double)vals[i], (i < n - 1) ? ", " : "");CHKERRQ(ierr);
  }
  ierr = PetscPrintf(PETSC_COMM_WORLD, "]%s\n", trailing_comma ? "," : "");CHKERRQ(ierr);
  PetscFunctionReturn(0);
}

#endif
