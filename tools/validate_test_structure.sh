#!/usr/bin/env bash
# Marker-validation gate for the SPIDER test suite.
#
# Two checks:
#
# 1. Marker discipline: walks every *.py file under tests/, finds every
#    `def test_*` definition, and verifies that the function (or its
#    enclosing class, or the module-level pytestmark) carries exactly
#    one of:
#
#        @pytest.mark.unit
#        @pytest.mark.smoke
#        @pytest.mark.integration
#        @pytest.mark.slow
#        @pytest.mark.skip
#
# 2. Source mirror: every physics C source has a companion test file
#    tests/test_<stem>.py (utility sources are exempt; the source lists
#    mirror tools/check_test_quality.py and must be kept in sync).
#
# Any violation is printed as <file>:<line> and the script exits 1.
# Run from repository root:
#
#     bash tools/validate_test_structure.sh
#
# CI invokes this before pytest in .github/workflows/ci.yml.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -d tests ]; then
    echo "ERROR: tests/ not found in $REPO_ROOT" >&2
    exit 2
fi

python3 - <<'PY'
import ast
import pathlib
import sys

ROOT = pathlib.Path('tests').resolve()
TIER = {'unit', 'smoke', 'integration', 'slow'}
SKIP = {'skip'}
ALLOWED = TIER | SKIP

failures: list[str] = []
total = 0


def mark_names_from_decorators(decorators):
    out = []
    for d in decorators:
        # @pytest.mark.NAME
        if isinstance(d, ast.Attribute) and isinstance(d.value, ast.Attribute):
            if (
                isinstance(d.value.value, ast.Name)
                and d.value.value.id == 'pytest'
                and d.value.attr == 'mark'
            ):
                out.append(d.attr)
        # @pytest.mark.NAME(...)
        elif isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
            f = d.func
            if (
                isinstance(f.value, ast.Attribute)
                and isinstance(f.value.value, ast.Name)
                and f.value.value.id == 'pytest'
                and f.value.attr == 'mark'
            ):
                out.append(f.attr)
    return out


def module_marks(tree):
    marks = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'pytestmark':
                    val = node.value
                    items = val.elts if isinstance(val, (ast.List, ast.Tuple)) else [val]
                    for item in items:
                        marks.extend(mark_names_from_decorators([item]))
    return marks


def walk(tree, parent_marks):
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            cls_marks = parent_marks + mark_names_from_decorators(node.decorator_list)
            out.extend(walk(node, cls_marks))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('test_'):
                fn_marks = mark_names_from_decorators(node.decorator_list)
                out.append((node, parent_marks + fn_marks))
    return out


for path in sorted(ROOT.rglob('*.py')):
    # Only inspect components below tests/; the repo itself may live
    # under a dotted directory (e.g. a git worktree).
    if any(part.startswith('.') for part in path.relative_to(ROOT).parts):
        continue
    if path.name == 'conftest.py':
        continue
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'))
    except SyntaxError as exc:
        failures.append(f'{path}:{exc.lineno}: SyntaxError {exc.msg}')
        continue
    mod_marks = module_marks(tree)
    for fn, marks in walk(tree, mod_marks):
        total += 1
        tier_marks = [m for m in marks if m in TIER]
        has_skip = any(m in SKIP for m in marks)
        rel = path.relative_to(ROOT.parent)
        if len(tier_marks) > 1:
            failures.append(
                f'{rel}:{fn.lineno}: {fn.name} has multiple tier markers '
                f'{sorted(set(tier_marks))}; exactly one of '
                'unit / smoke / integration / slow is required.'
            )
        elif len(tier_marks) == 0 and not has_skip:
            failures.append(
                f'{rel}:{fn.lineno}: {fn.name} carries no marker '
                '(need one of unit / smoke / integration / slow / skip)'
            )

# Source-mirror check: physics C sources need a companion test file.
# Keep this list in sync with PHYSICS_SOURCES in tools/check_test_quality.py.
PHYSICS_SOURCES = {
    'atmosphere.c', 'bc.c', 'energy.c', 'eos.c', 'eos_adamswilliamson.c',
    'eos_composite.c', 'eos_lookup.c', 'ic.c', 'interp.c', 'matprop.c',
    'mesh.c', 'reaction.c', 'rheologicalfront.c', 'rhs.c', 'twophase.c',
}
for source in sorted(PHYSICS_SOURCES):
    stem = source.rsplit('.', 1)[0]
    companion = ROOT / f'test_{stem}.py'
    if not companion.exists():
        failures.append(f'{source}: missing companion test file tests/test_{stem}.py')

if failures:
    print(f'Structure validation FAILED with {len(failures)} finding(s) over {total} tests.')
    for f in failures:
        print(f'  {f}')
    sys.exit(1)

print(f'Structure validation OK: {total} tests, all marked; all physics sources mirrored.')
PY
