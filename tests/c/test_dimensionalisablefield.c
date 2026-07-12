static const char help[] =
    "Exercises the DimensionalisableField wrapper on a small DMDA:\n"
    "create, fill, scale, unscale, duplicate, local vector, and the\n"
    "scaling query. Prints one JSON object to stdout; the pytest\n"
    "wrapper owns all assertions.\n";

#include <petsc.h>

#include "dimensionalisablefield.h"

#define TEST_N 5
#define TEST_SCALING 2.5

int main(int argc, char **argv)
{
  PetscErrorCode         ierr;
  DM                     dm;
  DimensionalisableField f, fdup;
  Vec                    v, vlocal;
  PetscScalar            scalings[1] = {TEST_SCALING};
  PetscScalar            dupScaling[1];
  const PetscScalar      *arr;
  PetscScalar            original0, scaled0, rescaled0, roundtrip0;
  PetscInt               i, numDomains, nlocal;

  ierr = PetscInitialize(&argc, &argv, NULL, help);
  if (ierr) return (int)ierr;

  ierr = DMDACreate1d(PETSC_COMM_WORLD, DM_BOUNDARY_NONE, TEST_N, 1, 1, NULL, &dm);CHKERRQ(ierr);
  ierr = DMSetUp(dm);CHKERRQ(ierr);

  ierr = DimensionalisableFieldCreate(&f, dm, scalings, PETSC_FALSE);CHKERRQ(ierr);
  ierr = DimensionalisableFieldSetName(f, "test field");CHKERRQ(ierr);
  ierr = DimensionalisableFieldSetUnits(f, "test units");CHKERRQ(ierr);

  /* fill the global vector with 1..N so index slips are visible */
  ierr = DimensionalisableFieldGetGlobalVec(f, &v);CHKERRQ(ierr);
  for (i = 0; i < TEST_N; ++i) {
    ierr = VecSetValue(v, i, (PetscScalar)(i + 1), INSERT_VALUES);CHKERRQ(ierr);
  }
  ierr = VecAssemblyBegin(v);CHKERRQ(ierr);
  ierr = VecAssemblyEnd(v);CHKERRQ(ierr);

  ierr = VecGetArrayRead(v, &arr);CHKERRQ(ierr);
  original0 = arr[0];
  ierr = VecRestoreArrayRead(v, &arr);CHKERRQ(ierr);

  /* scale multiplies by the stored scaling, unscale inverts it */
  ierr = DimensionalisableFieldScale(f);CHKERRQ(ierr);
  ierr = VecGetArrayRead(v, &arr);CHKERRQ(ierr);
  scaled0 = arr[0];
  ierr = VecRestoreArrayRead(v, &arr);CHKERRQ(ierr);

  /* scaling an already-scaled field is the documented no-op guard:
     it warns and must leave the values untouched */
  ierr = DimensionalisableFieldScale(f);CHKERRQ(ierr);
  ierr = VecGetArrayRead(v, &arr);CHKERRQ(ierr);
  rescaled0 = arr[0];
  ierr = VecRestoreArrayRead(v, &arr);CHKERRQ(ierr);

  ierr = DimensionalisableFieldUnscale(f);CHKERRQ(ierr);
  ierr = VecGetArrayRead(v, &arr);CHKERRQ(ierr);
  roundtrip0 = arr[0];
  ierr = VecRestoreArrayRead(v, &arr);CHKERRQ(ierr);

  /* the duplicate carries the scaling and domain layout */
  ierr = DimensionalisableFieldDuplicate(f, &fdup);CHKERRQ(ierr);
  numDomains = 1;
  ierr = DimensionalisableFieldGetScaling(fdup, &numDomains, dupScaling);CHKERRQ(ierr);

  /* the local vector matches the serial DMDA layout */
  ierr = DimensionalisableFieldCreateLocalVec(f, &vlocal);CHKERRQ(ierr);
  ierr = VecGetLocalSize(vlocal, &nlocal);CHKERRQ(ierr);

  ierr = PetscPrintf(PETSC_COMM_WORLD, "{\n");CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"original0\": %.17g,\n", (double)original0);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"scaled0\": %.17g,\n", (double)scaled0);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"rescaled0\": %.17g,\n", (double)rescaled0);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"roundtrip0\": %.17g,\n", (double)roundtrip0);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"scaling\": %.17g,\n", (double)TEST_SCALING);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"dup_scaling0\": %.17g,\n", (double)dupScaling[0]);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"num_domains\": %d,\n", (int)numDomains);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "\"nlocal\": %d\n", (int)nlocal);CHKERRQ(ierr);
  ierr = PetscPrintf(PETSC_COMM_WORLD, "}\n");CHKERRQ(ierr);

  ierr = VecDestroy(&vlocal);CHKERRQ(ierr);
  ierr = DimensionalisableFieldDestroy(&fdup);CHKERRQ(ierr);
  ierr = DimensionalisableFieldDestroy(&f);CHKERRQ(ierr);
  ierr = DMDestroy(&dm);CHKERRQ(ierr);
  ierr = PetscFinalize();
  return 0;
}
