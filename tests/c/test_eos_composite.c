static const char help[] =
    "Evaluates the two-phase composite EOS (melt + solid lookup sub-EOSes)\n"
    "at probe points given in SI units.\n"
    "Options: the -melt_* and -solid_* EOS options, the scaling options,\n"
    "         -matprop_smooth_width / -phi_critical / -phi_width, plus\n"
    "         -P_si <list, Pa> -S_si <list, J/kg/K> (paired probe points)\n"
    "Prints one JSON object to stdout with SI values plus the dimensionless\n"
    "phase fraction; the pytest wrapper owns all assertions.\n";

#include <petsc.h>

#include "eos.h"
#include "eos_composite.h"
#include "spider_test_utils.h"

#define SPIDER_TEST_MAXQ 64

int main(int argc, char **argv)
{
  PetscErrorCode       ierr;
  ScalingConstants     SC;
  FundamentalConstants FC;
  EOS                  sub_eos[2], composite;
  PetscScalar          P_si[SPIDER_TEST_MAXQ], S_si[SPIDER_TEST_MAXQ];
  PetscScalar          phi[SPIDER_TEST_MAXQ], phi_raw[SPIDER_TEST_MAXQ];
  PetscScalar          T[SPIDER_TEST_MAXQ], rho[SPIDER_TEST_MAXQ], fusion[SPIDER_TEST_MAXQ];
  PetscScalar          liquidus_S[SPIDER_TEST_MAXQ], solidus_S[SPIDER_TEST_MAXQ];
  PetscInt             nP = SPIDER_TEST_MAXQ, nS = SPIDER_TEST_MAXQ, i;
  PetscBool            set = PETSC_FALSE;

  ierr = PetscInitialize(&argc, &argv, NULL, help);
  if (ierr) return (int)ierr;

  ierr = PetscOptionsGetScalarArray(NULL, NULL, "-P_si", P_si, &nP, &set);CHKERRQ(ierr);
  if (!set || nP == 0) SETERRQ(PETSC_COMM_WORLD, PETSC_ERR_ARG_WRONG, "-P_si is required");
  ierr = PetscOptionsGetScalarArray(NULL, NULL, "-S_si", S_si, &nS, &set);CHKERRQ(ierr);
  if (!set || nS != nP) SETERRQ(PETSC_COMM_WORLD, PETSC_ERR_ARG_WRONG, "-S_si must pair with -P_si");

  ierr = ScalingConstantsCreate(&SC);CHKERRQ(ierr);
  ierr = SpiderTestScalingConstantsSetFromOptions(SC);CHKERRQ(ierr);
  ierr = FundamentalConstantsCreate(&FC);CHKERRQ(ierr);
  ierr = FundamentalConstantsSet(FC, SC);CHKERRQ(ierr);

  /* Slot order matches parameters.c: melt first (liquidus), solid second
     (solidus). */
  ierr = EOSCreate(&sub_eos[0], SPIDER_EOS_LOOKUP);CHKERRQ(ierr);
  ierr = EOSSetUpFromOptions(sub_eos[0], "melt", FC, SC);CHKERRQ(ierr);
  ierr = EOSCreate(&sub_eos[1], SPIDER_EOS_LOOKUP);CHKERRQ(ierr);
  ierr = EOSSetUpFromOptions(sub_eos[1], "solid", FC, SC);CHKERRQ(ierr);

  ierr = EOSCreate(&composite, SPIDER_EOS_COMPOSITE);CHKERRQ(ierr);
  ierr = EOSCompositeSetSubEOS(composite, sub_eos, 2);CHKERRQ(ierr);
  /* the prefix matches the production setup in parameters.c */
  ierr = EOSSetUpFromOptions(composite, "composite", FC, SC);CHKERRQ(ierr);

  for (i = 0; i < nP; ++i) {
    EOSEvalData eval;
    PetscScalar Pn = P_si[i] / SC->PRESSURE;
    PetscScalar Sn = S_si[i] / SC->ENTROPY;

    ierr = EOSEval(composite, Pn, Sn, &eval);CHKERRQ(ierr);
    phi[i]    = eval.phase_fraction;
    T[i]      = eval.T * SC->TEMP;
    rho[i]    = eval.rho * SC->DENSITY;
    fusion[i] = eval.fusion * SC->ENTROPY;
    ierr = EOSCompositeGetTwoPhasePhaseFractionNoTruncation(composite, Pn, Sn, &phi_raw[i]);CHKERRQ(ierr);
    ierr = EOSGetPhaseBoundary(sub_eos[0], Pn, &liquidus_S[i], NULL);CHKERRQ(ierr);
    liquidus_S[i] *= SC->ENTROPY;
    ierr = EOSGetPhaseBoundary(sub_eos[1], Pn, &solidus_S[i], NULL);CHKERRQ(ierr);
    solidus_S[i] *= SC->ENTROPY;
  }

  ierr = PetscPrintf(PETSC_COMM_WORLD, "{\n");CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("phase_fraction", phi, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("phase_fraction_no_truncation", phi_raw, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("T", T, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("rho", rho, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("fusion", fusion, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("liquidus_S", liquidus_S, nP, PETSC_TRUE);CHKERRQ(ierr);
  ierr = SpiderTestPrintScalarArray("solidus_S", solidus_S, nP, PETSC_FALSE);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "}\n");CHKERRQ(ierr);

  ierr = EOSDestroy(&composite);CHKERRQ(ierr);
  ierr = EOSDestroy(&sub_eos[0]);CHKERRQ(ierr);
  ierr = EOSDestroy(&sub_eos[1]);CHKERRQ(ierr);
  ierr = FundamentalConstantsDestroy(&FC);CHKERRQ(ierr);
  ierr = ScalingConstantsDestroy(&SC);CHKERRQ(ierr);
  ierr = PetscFinalize();
  return (int)ierr;
}
