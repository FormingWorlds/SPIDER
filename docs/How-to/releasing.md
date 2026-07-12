# Releasing

SPIDER uses calendar versioning: releases are named `YY.MM.DD` (no leading `v`), with a `.N` suffix appended when more than one release happens on the same day. The version lives in `version.h` and is stamped into every JSON output file, so archived runs identify the code that produced them.

## Procedure

1. **Update `version.h`** so the three components match the release date:

    ```c
    #define SPIDER_MAJOR_VERSION "26"
    #define SPIDER_MINOR_VERSION "03"
    #define SPIDER_PATCH_VERSION "02"
    ```

    Commit this change through a pull request like any other change.

2. **Confirm CI is green on `main`**, including the most recent nightly run (the nightly tier runs the full regression suite and the full coverage gate).

3. **Tag and publish the release** from the commit that updated `version.h`:

    ```bash
    git tag 26.03.02
    git push origin 26.03.02
    gh release create 26.03.02 --generate-notes --title "26.03.02"
    ```

    !!! warning "Tag format"
        Tags are bare CalVer dates with no leading `v` (`26.03.02`, not `v26.03.02`), so the tag matches the `version.h` triple that the release guard checks and that is stamped into every JSON output file.

    Edit the generated notes where the automatic summary needs context; call out any change to the JSON output fields or their units explicitly, because the PROTEUS coupling reads them.

4. **Release guard.** A workflow checks on every published release that the tag name matches the `version.h` triple and fails the release job on a mismatch; fix `version.h` (or retag) and re-run it if it fires.

5. **Update the PROTEUS pin.** Coupled deployments pin SPIDER by commit in PROTEUS's `pyproject.toml` (`[tool.proteus.modules.spider]`); after a release that PROTEUS should adopt, open a PROTEUS pull request bumping the pin and run the PROTEUS interior smoke tests against it. See [Coupling to PROTEUS](proteus_coupling.md) for the exchange contract that makes a pin bump safe.

There is no package registry step: SPIDER ships as source plus the GitHub release.

## What warrants a release

- Any change to the JSON output contract (fields, units, scalings) that PROTEUS consumes.
- Physics changes that move the frozen regression references.
- Build-system or dependency changes (PETSc version support).
- Accumulated fixes worth pinning from PROTEUS.
