################################################################################
# SPIDER Makefile                                                              #
################################################################################

# Executable Name
EXNAME = spider

# Source files, each corresponding to a .o object file and .d dependency file
SRC_C = \
        atmosphere.c \
        bc.c \
        cJSON.c \
	constants.c \
        ctx.c \
        dimensionalisablefield.c \
        energy.c \
        eos.c \
        eos_adamswilliamson.c \
        eos_composite.c \
        eos_lookup.c \
        eos_output.c \
        ic.c \
        interp.c \
        main.c \
        matprop.c \
        mesh.c \
        monitor.c \
        parameters.c \
        poststep.c \
        reaction.c \
        rheologicalfront.c \
        rhs.c \
        rollback.c \
        twophase.c \
        util.c \

# Main Target
all :: ${EXNAME}

### SPIDER Root Directory #####################################################
# Placement of this line matters. It will only work before any "include"s
SPIDER_ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

### PETSc ######################################################################
# Include PETSc variables and rules
include ${PETSC_DIR}/lib/petsc/conf/variables
include ${PETSC_DIR}/lib/petsc/conf/rules

### Flags ######################################################################
# Extra flags
# Use -O0 to turn off optimization, to debug with LLDB/GDB
# You can specify this from the command line, e.g.
# Available sanitizer flags with OSX
# With debugging
#  make clean; make -j CFLAGS_EXTRA="-O0"
# with Address Sanitizer
#   make clean; make -j CFLAGS_EXTRA="-O0 -fsanitize=address"
# with UndefinedBehaviorSanitizer
#   make clean; make -j CFLAGS_EXTRA="-O0 -fsanitize=undefined"
CFLAGS+=${CFLAGS_EXTRA}

# Generate dependency (.d) files as we compile
CFLAGS+=${C_DEPFLAGS}

# Provide the current directory so that absolute paths to data files can be constructed.
CFLAGS+=-DSPIDER_ROOT_DIR=${SPIDER_ROOT_DIR}

# Repo-root headers, needed when compiling the C test executables under tests/c/
CFLAGS+=-I${SPIDER_ROOT_DIR}

### Compiling/Linking  #########################################################

# Objects (PETSc rules provides recipe)
SRC_O = ${SRC_C:%.c=%.o}

# Main executable
${EXNAME} : ${SRC_O}
	-${CLINKER} -o $@ $^ ${PETSC_TS_LIB}
	#${RM} $^

### Tests ######################################################################
# The pytest suite drives the spider binary and the C test executables.
# Tier system and writing guidance: docs/How-to/build_tests.md.

# C test executables: thin evaluators linked against the SPIDER objects.
# The pytest wrappers under tests/ own all assertions.
TEST_C_SRC = \
        tests/c/test_interp.c \
        tests/c/test_eos.c \
        tests/c/test_eos_composite.c \

TEST_C_EXE = ${TEST_C_SRC:%.c=%}
TEST_C_O = ${TEST_C_SRC:%.c=%.o}
TEST_C_D = ${TEST_C_SRC:%.c=%.d}

# All SPIDER objects except the entry point (each test provides its own main)
SRC_O_NOMAIN = $(filter-out main.o,${SRC_O})

tests_c : ${TEST_C_EXE}

${TEST_C_EXE} : % : %.o ${SRC_O_NOMAIN}
	${CLINKER} -o $@ $^ ${PETSC_TS_LIB}

test :
	python3 -m pytest -m "(unit or smoke) and not skip"

test_all :
	python3 -m pytest -m "not skip"

.PHONY: tests_c test test_all

### Dependencies ###############################################################
SRC_D = ${SRC_C:%.c=%.d}

# Indicate that SRC_D is up to date. Prevents the include from having quadratic complexity.
$(SRC_D) $(TEST_C_D) : ;

# Include dependency files
-include $(SRC_D)
-include $(TEST_C_D)

### Helper Targets #############################################################
clean ::
	rm -f ${EXNAME} ${SRC_O} ${SRC_D} ${TEST_C_EXE} ${TEST_C_O} ${TEST_C_D}

.PHONY: clean

### Misc #######################################################################

# Remove results of partial, failed builds
.DELETE_ON_ERROR:
