static const char help[] =
    "Evaluates a single SPIDER lookup EOS at probe points given in SI units.\n"
    "Options: the usual -<prefix>_* EOS options (e.g. -melt_TYPE,\n"
    "         -melt_rho_filename_rel_to_src, ...), the scaling options\n"
    "         (-entropy0 -radius0 -time0 -pressure0), plus\n"
    "         -eos_prefix <name> (default melt)\n"
    "         -P_si <list, Pa> -S_si <list, J/kg/K> (paired probe points)\n"
    "Inputs are nondimensionalised with the scaling constants, evaluated,\n"
    "and the results are re-dimensionalised, so the printed values are SI\n"
    "for any choice of scalings. Prints one JSON object to stdout; the\n"
    "pytest wrapper owns all assertions.\n";

#include <petsc.h>

#include "eos.h"
#include "spider_test_utils.h"

#define SPIDER_TEST_MAXQ 64

int main(int argc, char **argv)
{
  PetscErrorCode       ierr;
  ScalingConstants     SC;
  FundamentalConstants FC;
  EOS                  eos;
  char                 prefix[64] = "melt";
  PetscScalar          P_si[SPIDER_TEST_MAXQ], S_si[SPIDER_TEST_MAXQ];
  PetscScalar          T[SPIDER_TEST_MAXQ], rho[SPIDER_TEST_MAXQ], cp[SPIDER_TEST_MAXQ];
  PetscScalar          alpha[SPIDER_TEST_MAXQ], dTdPs[SPIDER_TEST_MAXQ];
  PetscScalar          Sb[SPIDER_TEST_MAXQ];
  PetscInt             nP = SPIDER_TEST_MAXQ, nS = SPIDER_TEST_MAXQ, i;
  PetscBool            set = PETSC_FALSE;

  ierr = PetscInitialize(&argc, &argv, NULL, help);
  if (ierr) return (int)ierr;

  ierr = PetscOptionsGetString(NULL, NULL, "-eos_prefix", prefix, sizeof(prefix), NULL);CHKERRQ(ierr);
  ierr = PetscOptionsGetScalarArray(NULL, NULL, "-P_si", P_si, &nP, &set);CHKERRQ(ierr);
  if (!set || nP == 0) SETERRQ(PETSC_COMM_WORLD, PETSC_ERR_ARG_WRONG, "-P_si is required");
  ierr = PetscOptionsGetScalarArray(NULL, NULL, "-S_si", S_si, &nS, &set);CHKERRQ(ierr);
  if (!set || nS != nP) SETERRQ(PETSC_COMM_WORLD, PETSC_ERR_ARG_WRONG, "-S_si must pair with -P_si");

  ierr = ScalingConstantsCreate(&SC);CHKERRQ(ierr);
  ierr = SpiderTestScalingConstantsSetFromOptions(SC);CHKERRQ(ierr);
  ierr = FundamentalConstantsCreate(&FC);CHKERRQ(ierr);
  ierr = FundamentalConstantsSet(FC, SC);CHKERRQ(ierr);

  ierr = EOSCreate(&eos, SPIDER_EOS_LOOKUP);CHKERRQ(ierr);
  ierr = EOSSetUpFromOptions(eos, prefix, FC, SC);CHKERRQ(ierr);

  for (i = 0; i < nP; ++i) {
    EOSEvalData eval;
    PetscScalar Pn = P_si[i] / SC->PRESSURE;
    PetscScalar Sn = S_si[i] / SC->ENTROPY;

    ierr = EOSEval(eos, Pn, Sn, &eval);CHKERRQ(ierr);
    T[i]     = eval.T * SC->TEMP;
    rho[i]   = eval.rho * SC->DENSITY;
    cp[i]    = eval.Cp * SC->ENTROPY;
    /* the alpha table is loaded with zconst = 1/TEMP, so SI = internal / TEMP */
    alpha[i] = eval.alpha / SC->TEMP;
    dTdPs[i] = eval.dTdPs * SC->DTDP;
    if (eos->PHASE_BOUNDARY) {
      ierr = EOSGetPhaseBoundary(eos, Pn, &Sb[i], NULL);CHKERRQ(ierr);
      Sb[i] *= SC->ENTROPY;
    } else {
      Sb[i] = 0.0;
    }
  }

  ierr = PetscPrintf(PETSC_COMM_WORLD, "{\n");CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("T", T, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("rho", rho, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("cp", cp, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("alpha", alpha, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("dTdPs", dTdPs, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("phase_boundary_S", Sb, nP, PETSC_FALSE);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "}\n");CHKERRQ(ierr);

  ierr = EOSDestroy(&eos);CHKERRQ(ierr);
  ierr = FundamentalConstantsDestroy(&FC);CHKERRQ(ierr);
  ierr = ScalingConstantsDestroy(&SC);CHKERRQ(ierr);
  ierr = PetscFinalize();
  return (int)ierr;
}
