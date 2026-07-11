static const char help[] =
    "Evaluates SPIDER's 1-D and 2-D lookup interpolation at probe points.\n"
    "Options: -file_1d <path> -x_1d <list>  and/or\n"
    "         -file_2d <path> -x_2d <list> -y_2d <list> (paired)\n"
    "Files are read with unity scalings (values taken as-is). Prints one\n"
    "JSON object to stdout; the pytest wrapper owns all assertions.\n";

#include <petsc.h>

#include "interp.h"
#include "spider_test_utils.h"

#define SPIDER_TEST_MAXQ 64

int main(int argc, char **argv)
{
  PetscErrorCode ierr;
  char           file1d[PETSC_MAX_PATH_LEN], file2d[PETSC_MAX_PATH_LEN];
  PetscBool      has1d = PETSC_FALSE, has2d = PETSC_FALSE, set = PETSC_FALSE;
  PetscScalar    x1[SPIDER_TEST_MAXQ], x2[SPIDER_TEST_MAXQ], y2[SPIDER_TEST_MAXQ];
  PetscScalar    y1v[SPIDER_TEST_MAXQ], dy1v[SPIDER_TEST_MAXQ], z2v[SPIDER_TEST_MAXQ];
  PetscInt       n1 = SPIDER_TEST_MAXQ, n2x = SPIDER_TEST_MAXQ, n2y = SPIDER_TEST_MAXQ;
  PetscInt       i;

  ierr = PetscInitialize(&argc, &argv, NULL, help);
  if (ierr) return (int)ierr;

  ierr = PetscOptionsGetString(NULL, NULL, "-file_1d", file1d, sizeof(file1d), &has1d);CHKERRQ(ierr);
  ierr = PetscOptionsGetString(NULL, NULL, "-file_2d", file2d, sizeof(file2d), &has2d);CHKERRQ(ierr);

  ierr = PetscPrintf(PETSC_COMM_WORLD, "{\n");CHKERRQ(ierr);

  if (has1d) {
    Interp1d interp1;

    ierr = PetscOptionsGetScalarArray(NULL, NULL, "-x_1d", x1, &n1, &set);CHKERRQ(ierr);
    if (!set || n1 == 0) SETERRQ(PETSC_COMM_WORLD, PETSC_ERR_ARG_WRONG, "-x_1d required with -file_1d");
    ierr = Interp1dCreateAndSet(file1d, &interp1, 1.0, 1.0);CHKERRQ(ierr);
    for (i = 0; i < n1; ++i) {
      ierr = SetInterp1dValue(interp1, x1[i], &y1v[i], &dy1v[i]);CHKERRQ(ierr);
    }
    ierr = PetscPrintf(PETSC_COMM_WORLD, "\"xmin_1d\": %.17g,\n", (double)interp1->xmin);CHKERRQ(ierr);
    ierr = PetscPrintf(PETSC_COMM_WORLD, "\"xmax_1d\": %.17g,\n", (double)interp1->xmax);CHKERRQ(ierr);
    ierr = SpiderTestPrintScalarArray("y_1d", y1v, n1, PETSC_TRUE);CHKERRQ(ierr);
    ierr = SpiderTestPrintScalarArray("dydx_1d", dy1v, n1, has2d);CHKERRQ(ierr);
    ierr = Interp1dDestroy(&interp1);CHKERRQ(ierr);
  }

  if (has2d) {
    Interp2d interp2;

    ierr = PetscOptionsGetScalarArray(NULL, NULL, "-x_2d", x2, &n2x, &set);CHKERRQ(ierr);
    if (!set || n2x == 0) SETERRQ(PETSC_COMM_WORLD, PETSC_ERR_ARG_WRONG, "-x_2d required with -file_2d");
    ierr = PetscOptionsGetScalarArray(NULL, NULL, "-y_2d", y2, &n2y, &set);CHKERRQ(ierr);
    if (!set || n2y != n2x) SETERRQ(PETSC_COMM_WORLD, PETSC_ERR_ARG_WRONG, "-y_2d must pair with -x_2d");
    ierr = Interp2dCreateAndSet(file2d, &interp2, 1.0, 1.0, 1.0);CHKERRQ(ierr);
    for (i = 0; i < n2x; ++i) {
      ierr = SetInterp2dValue(interp2, x2[i], y2[i], &z2v[i]);CHKERRQ(ierr);
    }
    ierr = SpiderTestPrintScalarArray("z_2d", z2v, n2x, PETSC_FALSE);CHKERRQ(ierr);
    ierr = Interp2dDestroy(&interp2);CHKERRQ(ierr);
  }

  ierr = PetscPrintf(PETSC_COMM_WORLD, "}\n");CHKERRQ(ierr);

  ierr = PetscFinalize();
  return (int)ierr;
}
