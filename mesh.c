#include "mesh.h"
#include "monitor.h"
#include "eos_adamswilliamson.h"

static PetscErrorCode SetMeshRegular( Ctx * );
static PetscErrorCode SetMeshFromExternalFile( Ctx * );
static PetscErrorCode SetMeshPressureFromRadius( EOS, DM, Vec, Vec );
static PetscErrorCode SetMeshPressureGradientFromRadius( EOS, DM, Vec, Vec );
static PetscErrorCode SetMeshSphericalArea( DM, Vec, Vec );
static PetscErrorCode SetMeshSphericalVolume( Ctx *, Vec, Vec );
static PetscErrorCode SetMeshMass( EOS, Ctx * );
static PetscErrorCode GetRadiusFromMassCoordinate( Ctx * );
static PetscErrorCode RadiusIsMassCoordinate( Ctx * );

PetscErrorCode set_mesh( Ctx *E)
{
    PetscErrorCode ierr;
    Mesh           *M = &E->mesh;
    DM             da_b=E->da_b, da_s=E->da_s;
    Parameters     P = E->parameters;

    PetscFunctionBeginUser;

    /* for regular mesh (mass coordinates) */
    ierr = SetMeshRegular( E );CHKERRQ(ierr);

    if (P->MESH_SOURCE == 1) {
        /* external file provides radius, pressure, density, gravity */
        ierr = SetMeshFromExternalFile( E );CHKERRQ(ierr);
    } else {
        /* Adams-Williamson pathway (default, unchanged) */
        if(P->MASS_COORDINATES){
            ierr = GetRadiusFromMassCoordinate( E );CHKERRQ(ierr);
        }
        else{
            ierr = RadiusIsMassCoordinate( E );CHKERRQ(ierr);
        }

        ierr = SetMeshPressureFromRadius( P->eos_mesh, da_b, M->radius_b, M->pressure_b );CHKERRQ(ierr);
        ierr = SetMeshPressureGradientFromRadius( P->eos_mesh, da_b, M->radius_b, M->dPdr_b);CHKERRQ(ierr);
        ierr = SetMeshPressureFromRadius( P->eos_mesh, da_s, M->radius_s, M->pressure_s );CHKERRQ(ierr);
        ierr = SetMeshPressureGradientFromRadius( P->eos_mesh, da_s, M->radius_s, M->dPdr_s  );CHKERRQ(ierr);
        ierr = SetMeshMass( P->eos_mesh, E );CHKERRQ(ierr);
    }

    /* geometry terms without 4*pi prefactor */
    ierr = SetMeshSphericalArea( da_b, M->radius_b, M->area_b);CHKERRQ(ierr);
    ierr = SetMeshSphericalArea( da_s, M->radius_s, M->area_s );CHKERRQ(ierr);
    ierr = SetMeshSphericalVolume( E, M->radius_b, M->volume_s);CHKERRQ(ierr);

    /* mantle mass also needed for atmosphere calculations */
    P->atmosphere_parameters->mantle_mass_ptr = &M->mantle_mass;

    PetscFunctionReturn(0);
}

static PetscErrorCode SetMeshFromExternalFile( Ctx *E )
{
    /* Read mesh data from an external file (e.g., produced by Zalmoxis).

       File format (all values in SI units):
         # <numpts_b> <numpts_s>
         r_b[0]  P_b[0]  rho_b[0]  g_b[0]     (numpts_b lines: basic nodes)
         ...
         r_s[0]  P_s[0]  rho_s[0]  g_s[0]     (numpts_s lines: staggered nodes)
         ...

       Node ordering: surface (index 0) to CMB (index N-1).
       Gravity is negative (pointing inward) in the file.
    */

    PetscErrorCode  ierr;
    Mesh            *M = &E->mesh;
    Parameters      P = E->parameters;
    ScalingConstants SC = P->scaling_constants;
    PetscInt        numpts_b, numpts_s, file_nb, file_ns;
    PetscInt        i;
    FILE            *fp;
    PetscScalar     *arr_r, *arr_p, *arr_dpdr, *arr_m, *arr_dxidr;
    const PetscScalar *arr_xi;
    PetscScalar     r_val, p_val, rho_val, g_val;
    PetscScalar     rho_average, vol_shell;
    PetscScalar     *rho_b_tmp;

    PetscFunctionBeginUser;

    ierr = DMDAGetInfo(E->da_b,NULL,&numpts_b,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);CHKERRQ(ierr);
    ierr = DMDAGetInfo(E->da_s,NULL,&numpts_s,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);CHKERRQ(ierr);

    /* allocate temporary array for basic-node densities (needed for dxi/dr) */
    ierr = PetscMalloc1(numpts_b, &rho_b_tmp);CHKERRQ(ierr);

    /* open file */
    fp = fopen(P->mesh_external_filename, "r");
    if (!fp) SETERRQ1(PETSC_COMM_WORLD,PETSC_ERR_FILE_OPEN,
        "Cannot open external mesh file: %s", P->mesh_external_filename);

    /* parse header */
    if (fscanf(fp, "# %d %d\n", &file_nb, &file_ns) != 2) {
        fclose(fp);
        SETERRQ1(PETSC_COMM_WORLD,PETSC_ERR_FILE_READ,
            "Cannot parse header of external mesh file: %s", P->mesh_external_filename);
    }
    if (file_nb != numpts_b) {
        fclose(fp);
        SETERRQ2(PETSC_COMM_WORLD,PETSC_ERR_ARG_INCOMP,
            "External mesh file has %d basic nodes; expected %d",
            file_nb, numpts_b);
    }
    if (file_ns != numpts_s) {
        fclose(fp);
        SETERRQ2(PETSC_COMM_WORLD,PETSC_ERR_ARG_INCOMP,
            "External mesh file has %d staggered nodes; expected %d",
            file_ns, numpts_s);
    }

    /* --- Read basic node data and populate mesh vectors --- */
    ierr = DMDAVecGetArray(E->da_b,M->radius_b,&arr_r);CHKERRQ(ierr);
    ierr = DMDAVecGetArray(E->da_b,M->pressure_b,&arr_p);CHKERRQ(ierr);
    ierr = DMDAVecGetArray(E->da_b,M->dPdr_b,&arr_dpdr);CHKERRQ(ierr);

    for (i=0; i<numpts_b; ++i) {
        if (fscanf(fp, "%lf %lf %lf %lf", &r_val, &p_val, &rho_val, &g_val) != 4) {
            fclose(fp);
            SETERRQ2(PETSC_COMM_WORLD,PETSC_ERR_FILE_READ,
                "Error reading basic node %d from %s", i, P->mesh_external_filename);
        }
        /* nondimensionalize and store */
        arr_r[i] = r_val / SC->RADIUS;
        arr_p[i] = p_val / SC->PRESSURE;
        /* dP/dr = rho * g (hydrostatic; g is negative in file) */
        arr_dpdr[i] = (rho_val * g_val) / SC->DPDR;
        /* save density for dxi/dr computation below */
        rho_b_tmp[i] = rho_val / SC->DENSITY;
    }

    ierr = DMDAVecRestoreArray(E->da_b,M->radius_b,&arr_r);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArray(E->da_b,M->pressure_b,&arr_p);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArray(E->da_b,M->dPdr_b,&arr_dpdr);CHKERRQ(ierr);

    /* --- Validate file geometry against -radius and -coresize --- */
    /* Surface = index 0, CMB = index numpts_b-1 (file is surface-to-CMB) */
    {
        PetscScalar r_surface, r_cmb, file_coresize, rtol;
        ierr = DMDAVecGetArrayRead(E->da_b,M->radius_b,&arr_r);CHKERRQ(ierr);
        r_surface = arr_r[0] * SC->RADIUS;          /* re-dimensionalize */
        r_cmb     = arr_r[numpts_b-1] * SC->RADIUS;
        ierr = DMDAVecRestoreArrayRead(E->da_b,M->radius_b,&arr_r);CHKERRQ(ierr);

        rtol = 0.01;  /* 1% relative tolerance */
        if (PetscAbsScalar(r_surface - P->radius) / P->radius > rtol) {
            PetscPrintf(PETSC_COMM_WORLD,
                "WARNING: external mesh surface radius (%.6e m) differs from "
                "-radius (%.6e m) by >%.0f%%. Ensure -radius matches the file.\n",
                r_surface, P->radius, rtol*100);
        }
        file_coresize = r_cmb / r_surface;
        if (PetscAbsScalar(file_coresize - P->coresize) / P->coresize > rtol) {
            PetscPrintf(PETSC_COMM_WORLD,
                "WARNING: external mesh coresize (%.6f = R_cmb/R_surface) differs from "
                "-coresize (%.6f) by >%.0f%%. Ensure -coresize matches the file.\n",
                file_coresize, P->coresize, rtol*100);
        }
    }

    /* --- Read staggered node data --- */
    {
        PetscScalar *rho_s_tmp;
        ierr = PetscMalloc1(numpts_s, &rho_s_tmp);CHKERRQ(ierr);

        ierr = DMDAVecGetArray(E->da_s,M->radius_s,&arr_r);CHKERRQ(ierr);
        ierr = DMDAVecGetArray(E->da_s,M->pressure_s,&arr_p);CHKERRQ(ierr);
        ierr = DMDAVecGetArray(E->da_s,M->dPdr_s,&arr_dpdr);CHKERRQ(ierr);

        for (i=0; i<numpts_s; ++i) {
            if (fscanf(fp, "%lf %lf %lf %lf", &r_val, &p_val, &rho_val, &g_val) != 4) {
                fclose(fp);
                SETERRQ2(PETSC_COMM_WORLD,PETSC_ERR_FILE_READ,
                    "Error reading staggered node %d from %s", i, P->mesh_external_filename);
            }
            arr_r[i] = r_val / SC->RADIUS;
            arr_p[i] = p_val / SC->PRESSURE;
            arr_dpdr[i] = (rho_val * g_val) / SC->DPDR;
            rho_s_tmp[i] = rho_val / SC->DENSITY;
        }

        ierr = DMDAVecRestoreArray(E->da_s,M->radius_s,&arr_r);CHKERRQ(ierr);
        ierr = DMDAVecRestoreArray(E->da_s,M->pressure_s,&arr_p);CHKERRQ(ierr);
        ierr = DMDAVecRestoreArray(E->da_s,M->dPdr_s,&arr_dpdr);CHKERRQ(ierr);

        fclose(fp);

        /* --- Compute shell masses from staggered density and basic radii --- */
        /* mass_s[i] = rho_s[i] * (r_b[i]^3 - r_b[i+1]^3) / 3
           (without 4*pi, matching SPIDER convention) */
        {
            Vec radius_local = E->work_local_b;
            const PetscScalar *arr_rb;

            ierr = DMGlobalToLocalBegin(E->da_b,M->radius_b,INSERT_VALUES,radius_local);CHKERRQ(ierr);
            ierr = DMGlobalToLocalEnd(E->da_b,M->radius_b,INSERT_VALUES,radius_local);CHKERRQ(ierr);
            ierr = DMDAVecGetArrayRead(E->da_b,radius_local,&arr_rb);CHKERRQ(ierr);
            ierr = DMDAVecGetArray(E->da_s,M->mass_s,&arr_m);CHKERRQ(ierr);

            M->mantle_mass = 0.0;
            for (i=0; i<numpts_s; ++i) {
                vol_shell = (PetscPowScalar(arr_rb[i],3.0) - PetscPowScalar(arr_rb[i+1],3.0)) / 3.0;
                arr_m[i] = rho_s_tmp[i] * vol_shell;
                M->mantle_mass += arr_m[i];
            }

            ierr = DMDAVecRestoreArrayRead(E->da_b,radius_local,&arr_rb);CHKERRQ(ierr);
            ierr = DMDAVecRestoreArray(E->da_s,M->mass_s,&arr_m);CHKERRQ(ierr);
        }

        ierr = PetscFree(rho_s_tmp);CHKERRQ(ierr);
    }

    /* --- Compute dxi/dr at basic nodes ---
       dxi/dr = (rho / rho_avg) * (r / xi)^2
       This is a general property of mass coordinates, not specific to AW */
    {
        const PetscScalar *arr_rb;

        /* average density of the mantle */
        ierr = DMDAVecGetArrayRead(E->da_b,M->radius_b,&arr_rb);CHKERRQ(ierr);
        rho_average = M->mantle_mass * 3.0 /
            (PetscPowScalar(arr_rb[0],3.0) - PetscPowScalar(arr_rb[numpts_b-1],3.0));
        ierr = DMDAVecRestoreArrayRead(E->da_b,M->radius_b,&arr_rb);CHKERRQ(ierr);

        ierr = DMDAVecGetArray(E->da_b,M->dxidr_b,&arr_dxidr);CHKERRQ(ierr);
        ierr = DMDAVecGetArrayRead(E->da_b,M->radius_b,&arr_rb);CHKERRQ(ierr);
        ierr = DMDAVecGetArrayRead(E->da_b,M->xi_b,&arr_xi);CHKERRQ(ierr);

        for (i=0; i<numpts_b; ++i) {
            arr_dxidr[i] = (rho_b_tmp[i] / rho_average)
                * PetscPowScalar(arr_rb[i] / arr_xi[i], 2.0);
        }

        ierr = DMDAVecRestoreArray(E->da_b,M->dxidr_b,&arr_dxidr);CHKERRQ(ierr);
        ierr = DMDAVecRestoreArrayRead(E->da_b,M->radius_b,&arr_rb);CHKERRQ(ierr);
        ierr = DMDAVecRestoreArrayRead(E->da_b,M->xi_b,&arr_xi);CHKERRQ(ierr);
    }

    ierr = PetscFree(rho_b_tmp);CHKERRQ(ierr);

    PetscFunctionReturn(0);
}

static PetscErrorCode SetMeshRegular( Ctx *E )
{

    PetscErrorCode ierr;
    PetscScalar    *arr;
    PetscInt       i,ilo_b,ihi_b,ilo_s,ihi_s,w_b,w_s,numpts_b,numpts_s;
    Mesh           *M = &E->mesh;
    Parameters     P = E->parameters;
    DM             da_b=E->da_b, da_s=E->da_s;
    PetscScalar    dx_b;

    PetscFunctionBeginUser;

    ierr = DMDAGetInfo(E->da_b,NULL,&numpts_b,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);CHKERRQ(ierr);
    ierr = DMDAGetInfo(E->da_s,NULL,&numpts_s,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);CHKERRQ(ierr);

    /* basic node spacing (negative) */
    /* mass coordinate enforced to go from core radius to P->radius */

    dx_b = -P->radius * (1.0-P->coresize) / (numpts_b-1);

    /* mass coordinate at basic nodes */
    ierr = DMDAGetCorners(da_b,&ilo_b,0,0,&w_b,0,0);CHKERRQ(ierr);
    ihi_b = ilo_b + w_b;
    ierr = DMDAVecGetArray(da_b,M->xi_b,&arr);CHKERRQ(ierr);
    for (i=ilo_b; i<ihi_b; ++i){
        arr[i] = P->radius*P->coresize - (numpts_b-1-i)*dx_b;
    }
    ierr = DMDAVecRestoreArray(da_b,M->xi_b,&arr);CHKERRQ(ierr);

    /* mass coordinate at staggered nodes */
    ierr = DMDAGetCorners(da_s,&ilo_s,0,0,&w_s,0,0);CHKERRQ(ierr);
    ihi_s = ilo_s + w_s;
    ierr = DMDAVecGetArray(da_s,M->xi_s,&arr);CHKERRQ(ierr);
    for (i=ilo_s;i<ihi_s;++i){
        arr[i] = P->radius*P->coresize-0.5*dx_b - (numpts_s-1-i)*dx_b;
    }
    ierr = DMDAVecRestoreArray(da_s,M->xi_s,&arr);CHKERRQ(ierr);

    PetscFunctionReturn(0);
}

static PetscErrorCode SetMeshSphericalArea(DM da, Vec radius, Vec area )
{

    PetscErrorCode    ierr;
    PetscScalar       *arr_area;
    const PetscScalar *arr_radius;
    PetscInt          i,ilo,ihi,w;

    PetscFunctionBeginUser;
    ierr = DMDAGetCorners(da,&ilo,0,0,&w,0,0);CHKERRQ(ierr);
    ihi = ilo + w;
    ierr = DMDAVecGetArrayRead(da,radius,&arr_radius);CHKERRQ(ierr);
    ierr = DMDAVecGetArray(da,area,&arr_area);CHKERRQ(ierr);
    for(i=ilo; i<ihi; ++i){
        /* excludes 4*pi prefactor */
        arr_area[i] = PetscPowScalar( arr_radius[i], 2.0 );
    }
    ierr = DMDAVecRestoreArrayRead(da,radius,&arr_radius);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArray(da,area,&arr_area);CHKERRQ(ierr);
    PetscFunctionReturn(0);
}

static PetscErrorCode SetMeshSphericalVolume(Ctx * E, Vec radius, Vec volume )
{

    PetscErrorCode    ierr;
    PetscScalar       *arr_volume;
    const PetscScalar *arr_radius;
    PetscInt          i,ilo_s,ihi_s,w_s,ilo,ihi;
    DM                da_b=E->da_b,da_s=E->da_s;
    Vec               radius_local=E->work_local_b;

    PetscFunctionBeginUser;
    ierr = DMDAGetCorners(da_s,&ilo_s,0,0,&w_s,0,0);CHKERRQ(ierr);
    ihi_s = ilo_s + w_s;
    ilo = ilo_s;
    ihi = ihi_s;
    ierr = DMGlobalToLocalBegin(da_b,radius,INSERT_VALUES,radius_local);CHKERRQ(ierr);
    ierr = DMGlobalToLocalEnd(da_b,radius,INSERT_VALUES,radius_local);CHKERRQ(ierr);
    ierr = DMDAVecGetArrayRead(da_b,radius_local,&arr_radius);CHKERRQ(ierr);
    ierr = DMDAVecGetArray(da_s,volume,&arr_volume);CHKERRQ(ierr);
    for(i=ilo; i<ihi; ++i){
        arr_volume[i] = PetscPowScalar(arr_radius[i],3.0) - PetscPowScalar(arr_radius[i+1],3.0);
        /* note excludes 4*pi prefactor */
        arr_volume[i] *= 1.0 / 3.0;
    }
    // here and elsewhere, it's very dangerous to use the same indice to refer to two DAs without checking that the local ranges are valid.
    ierr = DMDAVecRestoreArrayRead(da_b,radius_local,&arr_radius);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArray(da_s,volume,&arr_volume);CHKERRQ(ierr);
    PetscFunctionReturn(0);
}

static PetscErrorCode SetMeshPressureFromRadius( const EOS eos, DM da, Vec radius, Vec pressure )
{
    PetscErrorCode    ierr;
    PetscScalar       *arr_p;
    const PetscScalar *arr_r;
    PetscInt          i,ilo,ihi,w;

    PetscFunctionBeginUser;
    ierr = DMDAGetCorners(da,&ilo,0,0,&w,0,0);CHKERRQ(ierr);
    ihi = ilo + w;
    ierr = DMDAVecGetArrayRead(da,radius,&arr_r);CHKERRQ(ierr);
    ierr = DMDAVecGetArray(da,pressure,&arr_p);CHKERRQ(ierr);
    for(i=ilo; i<ihi; ++i){
        ierr = EOSAdamsWilliamsonGetPressureFromRadius( eos, arr_r[i], &arr_p[i] );CHKERRQ(ierr);
    }
    ierr = DMDAVecRestoreArrayRead(da,radius,&arr_r);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArray(da,pressure,&arr_p);CHKERRQ(ierr);
    PetscFunctionReturn(0);
}

static PetscErrorCode SetMeshPressureGradientFromRadius( const EOS eos, DM da, Vec radius, Vec pressureg )
{
    PetscErrorCode    ierr;
    PetscScalar       *arr_pg;
    const PetscScalar *arr_r;
    PetscInt          i,ilo,ihi,w;

    PetscFunctionBeginUser;
    ierr = DMDAGetCorners(da,&ilo,0,0,&w,0,0);CHKERRQ(ierr);
    ihi = ilo + w;
    ierr = DMDAVecGetArray(da,pressureg,&arr_pg);CHKERRQ(ierr);
    ierr = DMDAVecGetArrayRead(da,radius,&arr_r);CHKERRQ(ierr);
    for(i=ilo; i<ihi; ++i){
        ierr = EOSAdamsWilliamsonGetPressureGradientFromRadius( eos, arr_r[i], &arr_pg[i]);CHKERRQ(ierr);
    }
    ierr = DMDAVecRestoreArray(da,pressureg,&arr_pg);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArrayRead(da,radius,&arr_r);CHKERRQ(ierr);
    PetscFunctionReturn(0);
}

static PetscErrorCode SetMeshMass( const EOS eos, Ctx *E)
{
    PetscErrorCode    ierr;
    Mesh              *M = &E->mesh;
    PetscScalar       *arr_m;
    const PetscScalar *arr_r;
    PetscInt          i,ilo,ihi,w;

    PetscFunctionBeginUser;
    ierr = DMDAGetCorners(E->da_b,&ilo,0,0,&w,0,0);CHKERRQ(ierr);
    ihi = ilo + w;

    ierr = DMDAVecGetArray(E->da_b,M->radius_b,&arr_r);CHKERRQ(ierr);
    ierr = DMDAVecGetArray(E->da_s,M->mass_s,&arr_m);CHKERRQ(ierr);

    for(i=ilo; i<ihi-1; ++i){
        ierr = EOSAdamsWilliamsonGetMassWithinShell( eos, arr_r[i], arr_r[i+1], &arr_m[i]);CHKERRQ(ierr);
     }
    /* total mantle mass */
    ierr = EOSAdamsWilliamsonGetMassWithinShell( eos, arr_r[ilo], arr_r[ihi-1], &M->mantle_mass);CHKERRQ(ierr);

    ierr = DMDAVecRestoreArrayRead(E->da_b,M->radius_b,&arr_r);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArrayRead(E->da_s,M->mass_s,&arr_m);CHKERRQ(ierr);

    PetscFunctionReturn(0);
}

static PetscErrorCode RadiusIsMassCoordinate( Ctx *E )
{
    /* recovers legacy behaviour of the code by setting the operational/code
       coordinate to the radius directly */

    PetscErrorCode ierr;
    Mesh           *M = &E->mesh;

    PetscFunctionBeginUser;

    ierr = VecCopy( M->xi_b, M->radius_b );CHKERRQ(ierr);
    ierr = VecCopy( M->xi_s, M->radius_s );CHKERRQ(ierr);
    ierr = VecSet( M->dxidr_b, 1.0);CHKERRQ(ierr);

    PetscFunctionReturn(0);
}

static PetscErrorCode GetRadiusFromMassCoordinate( Ctx *E )
{
    PetscErrorCode  ierr;
    SNES            snes;
    Vec             x,r;
    Mat             J;
    PetscScalar     *xx, *radius, *xi, *dxidr, dx;
    PetscInt        i,numpts_b,numpts_s;
    Mesh            *M = &E->mesh;
    Parameters const P = E->parameters;
    EOS        const eos = P->eos_mesh;

    PetscFunctionBeginUser;

    ierr = DMDAGetInfo(E->da_b,NULL,&numpts_b,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);CHKERRQ(ierr);
    ierr = DMDAGetInfo(E->da_s,NULL,&numpts_s,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);CHKERRQ(ierr);

    ierr = SNESCreate( PETSC_COMM_WORLD, &snes );CHKERRQ(ierr);

    /* Use this to address this specific SNES (nonlinear solver) from the command
       line or options file, e.g. -atmosic_snes_view */
    ierr = SNESSetOptionsPrefix(snes,"mass_coord_");CHKERRQ(ierr);

    /* convert to DMComposite? */
    ierr = VecCreate( PETSC_COMM_WORLD, &x );CHKERRQ(ierr);
    ierr = VecSetSizes( x, PETSC_DECIDE, numpts_b+numpts_s );CHKERRQ(ierr);
    ierr = VecSetFromOptions(x);CHKERRQ(ierr);
    ierr = VecDuplicate(x,&r);CHKERRQ(ierr);

    /* Jacobian */
    MatCreate(PETSC_COMM_WORLD,&J);
    MatSetSizes(J,PETSC_DECIDE,PETSC_DECIDE,numpts_b+numpts_s,numpts_b+numpts_s);
    MatSetFromOptions(J);
    MatSetUp(J);

    ierr = SNESSetFunction(snes,r,EOSAdamsWilliamson_ObjectiveFunctionRadius,E);CHKERRQ(ierr);

    /* initialise vector x with initial guess */
    /* the main reason I loop here is because I have slammed the basic and staggered nodes
       together, but the initial guesses for the basic and staggered radius can be identical
       to their mass coordinate counterparts.  i.e.,
           radius_s = xi_s
           radius_b = xi_b
       Presumably this can be done using Vec operations, once a DMcomposite is implemented */
    ierr = VecGetArray(x,&xx);CHKERRQ(ierr);
    dx = P->radius * (1.0-P->coresize) / (numpts_b-1);
    /* basic nodes */
    for (i=0; i<numpts_b; ++i) {
        /* best initial guess is evenly space from surface to cmb */
        xx[i] = P->radius - i * dx;
    }
    /* staggered nodes */
    for (i=numpts_b; i<numpts_b+numpts_s; ++i) {
        /* best initial guess is evenly space from surface to cmb */
        xx[i] = P->radius - 0.5 * dx - (i-numpts_b) * dx;
    }
    ierr = VecRestoreArray(x,&xx);CHKERRQ(ierr);

    ierr = SNESSetJacobian(snes,J,J,EOSAdamsWilliamson_JacobianRadius,E);CHKERRQ(ierr);

    /* Hard-coded solver parameters */
    /* Turn off convergence based on step size */
    ierr = PetscOptionsSetValue(NULL,"-mass_coord_snes_stol","0");CHKERRQ(ierr);
    /* Turn off convergenced based on trust region tolerance */
    ierr = PetscOptionsSetValue(NULL,"-mass_coord_snes_trtol","0");CHKERRQ(ierr);
    ierr = PetscOptionsSetValue(NULL,"-mass_coord_snes_type","newtontr");CHKERRQ(ierr);
    /* for typical terrestrial planet sizes around 1E6 m, this gives an accurate
       mapping to about 1 m, which should be more than sufficient */
    ierr = PetscOptionsSetValue(NULL,"-mass_coord_snes_rtol","1.0e-6");CHKERRQ(ierr);
    ierr = PetscOptionsSetValue(NULL,"-mass_coord_snes_atol","1.0e-6");CHKERRQ(ierr);
    ierr = PetscOptionsSetValue(NULL,"-mass_coord_ksp_rtol","1.0e-6");CHKERRQ(ierr);
    ierr = PetscOptionsSetValue(NULL,"-mass_coord_ksp_atol","1.0e-6");CHKERRQ(ierr);

    /* For solver analysis/debugging/tuning, activate a custom monitor with a flag */
    {
      PetscBool flg = PETSC_FALSE;

      ierr = PetscOptionsGetBool(NULL,NULL,"-mass_coord_snes_verbose_monitor",&flg,NULL);CHKERRQ(ierr);
      if (flg) {
        ierr = SNESMonitorSet(snes,SNESMonitorVerbose,NULL,NULL);CHKERRQ(ierr);
      }
    }

    /* Solve */
    ierr = SNESSetFromOptions(snes);CHKERRQ(ierr); /* Picks up any additional options (note prefix) */
    ierr = SNESSolve(snes,NULL,x);CHKERRQ(ierr);
  {
      SNESConvergedReason reason;
      ierr = SNESGetConvergedReason(snes,&reason);CHKERRQ(ierr);
      if (reason < 0) SETERRQ1(PetscObjectComm((PetscObject)snes),PETSC_ERR_CONV_FAILED,
          "Nonlinear solver didn't converge: %s\n",SNESConvergedReasons[reason]);
    }

    ierr = VecGetArray(x,&xx);CHKERRQ(ierr);

    /* if we can gratly reduce the number of lines of code here by NOT sanity
       checking, perhaps that is OK?  Or can we do something like if.any(values) < 0.0
       on a Vec without decomposing the Vec into an array? */
    /* extract solution for basic radius from solution vec */
    ierr = DMDAVecGetArray(E->da_b,M->radius_b,&radius);CHKERRQ(ierr);
    for (i=0; i<numpts_b; ++i) {
        if( xx[i] < 0.0 ){
            /* Sanity check on solution */
            SETERRQ1(PetscObjectComm((PetscObject)snes),PETSC_ERR_CONV_FAILED,
                "Unphysical radius coordinate, x: %g",xx[i]);
        }
        else{
            radius[i] = xx[i];
        }
    }
    ierr = DMDAVecRestoreArray(E->da_b,M->radius_b,radius);CHKERRQ(ierr);

    /* extract solution for staggered radius from solution vec */
    ierr = DMDAVecGetArray(E->da_s,M->radius_s,&radius);CHKERRQ(ierr);
    for (i=numpts_b; i<numpts_b+numpts_s; ++i) {
        if( xx[i] < 0.0 ){
            /* Sanity check on solution */
            SETERRQ1(PetscObjectComm((PetscObject)snes),PETSC_ERR_CONV_FAILED,
                "Unphysical radius coordinate, x: %g",xx[i]);
        }
        else{
            radius[i-numpts_b] = xx[i];
        }
    }
    ierr = DMDAVecRestoreArray(E->da_s,M->radius_s,radius);CHKERRQ(ierr);

    ierr = VecRestoreArray(x,&xx);CHKERRQ(ierr);

    /* now compute dxi/dr once all radius and xi are known */
    ierr = DMDAVecGetArray(E->da_b,M->dxidr_b,&dxidr);CHKERRQ(ierr);
    ierr = DMDAVecGetArrayRead(E->da_b,M->radius_b,&radius);CHKERRQ(ierr);
    ierr = DMDAVecGetArrayRead(E->da_b,M->xi_b,&xi);CHKERRQ(ierr);
    for (i=0; i<numpts_b; ++i) {
        EOSAdamsWilliamsonMassCoordinateSpatialDerivative( eos, radius[i], xi[i], &dxidr[i] );CHKERRQ(ierr);
    }
    ierr = DMDAVecRestoreArray(E->da_b,M->dxidr_b,&dxidr);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArrayRead(E->da_b,M->radius_b,&radius);CHKERRQ(ierr);
    ierr = DMDAVecRestoreArrayRead(E->da_b,M->xi_b,&xi);CHKERRQ(ierr);

    ierr = VecDestroy(&x);CHKERRQ(ierr);
    ierr = VecDestroy(&r);CHKERRQ(ierr);
    ierr = MatDestroy(&J);CHKERRQ(ierr);
    ierr = SNESDestroy(&snes);CHKERRQ(ierr);

    PetscFunctionReturn(0);

}
