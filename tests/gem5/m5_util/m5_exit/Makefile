# Makefile for building various ISA-specific m5_exit tests using Docker

# Path to the gem5 directory root
GEM5_DIR = $(shell pwd)/../../../..
# TODO: Change this to the path of the Makefile
PWD = ${GEM5_DIR}/tests/gem5/m5_util/m5_exit

# Path to m5 lib (libm5.a) source directory.
M5_LIB = util/m5
GEM5_M5_LIB = ${GEM5_DIR}/${M5_LIB}
GEM5_M5_LIB_X86 = ${GEM5_DIR}/${M5_LIB}/build/x86/out
GEM5_M5_LIB_ARM = ${GEM5_DIR}/${M5_LIB}/build/arm64/out
GEM5_M5_LIB_RISCV = ${GEM5_DIR}/${M5_LIB}/build/riscv/out

# The multiplatform ("linux/arm64", "linux/riscv64", and "linux/amd64")Docker
# image to use. Needed for cross-compilation.
DOCKER_IMAGE = ghcr.io/gem5/ubuntu-24.04_all-dependencies:latest


#Base Docker command to run. Just need to specify platform and image.
DOCKER_BASE_CMD = docker run --rm  -it -u 0: -v ${GEM5_DIR}:${GEM5_DIR}

# More specific Docker command for building the m5 library
DOCKER_BASE_LIB_CMD = ${DOCKER_BASE_CMD} --platform linux/amd64 -w ${GEM5_M5_LIB} ${DOCKER_IMAGE}

# Targets
TARGETS = bin/x86-m5-exit bin/arm-m5-exit bin/riscv-m5-exit

# Default target
all: ${TARGETS}

bin/x86-m5-exit: bin ${GEM5_M5_LIB_X86}
	${DOCKER_BASE_CMD} --platform linux/amd64 ${DOCKER_IMAGE} gcc ${PWD}/m5_exit.c -L ${GEM5_M5_LIB_X86} -l m5 -I ${GEM5_DIR}/include --static -o ${PWD}/bin/x86-m5-exit

${GEM5_M5_LIB_X86}:
	${DOCKER_BASE_LIB_CMD} scons build/x86/out/m5 -j `nproc`

bin/arm-m5-exit: bin ${GEM5_M5_LIB_ARM}
	${DOCKER_BASE_CMD} --platform linux/arm64 ${DOCKER_IMAGE} gcc ${PWD}/m5_exit.c -L ${GEM5_M5_LIB_ARM} -l m5 -I ${GEM5_DIR}/include --static -o ${PWD}/bin/arm-m5-exit

${GEM5_M5_LIB_ARM}:
	${DOCKER_BASE_LIB_CMD} bash -c 'apt update -y && apt install -y g++-aarch64-* && scons arm64.CROSS_COMPILE=aarch64-linux-gnu- build/arm64/out/m5 -j `nproc`'

bin/riscv-m5-exit: bin ${GEM5_M5_LIB_RISCV}
	${DOCKER_BASE_CMD} --platform linux/riscv64 ${DOCKER_IMAGE} gcc ${PWD}/m5_exit.c -L ${GEM5_M5_LIB_RISCV} -l m5 -I ${GEM5_DIR}/include --static -o ${PWD}/bin/riscv-m5-exit

${GEM5_M5_LIB_RISCV}:
	${DOCKER_BASE_LIB_CMD} bash -c 'apt update -y && apt install -y g++-riscv64-* && scons riscv.CROSS_COMPILE=riscv64-linux-gnu- build/riscv/out/m5 -j `nproc`'

#${GEM5_M5_LIB_X86}:
#	${DOCKER_BASE_CMD} --platform linux/amd64 -w ${GEM5_M5_LIB} ${DOCKER_IMAGE} bash -c \
#	  " \
#	  apt update -y && \
#	  apt install -y \
#	    g++-riscv64-* \
#	    g++-aarch64-* && ls && \
#	  scons riscv.CROSS_COMPILE=riscv64-linux-gnu- \
#	    build/riscv/out/m5 -j `nproc` && \
#	  scons arm64.CROSS_COMPILE=aarch64-linux-gnu- \
#	    build/arm64/out/m5 -j `nproc` && \
#	  scons build/x86/out/m5 -j `nproc` \
#	  "

# Create bin directory
bin:
	mkdir -p bin

# Clean target
clean:
	- rm -r bin ${GEM5_DIR}/${M5_LIB}/build

.PHONY: all clean
