
src_dir = .

RISCV_GCC_COMPILER=riscv64-unknown-linux-gnu-gcc # Need specify in your environment
x86_GCC_COMPILER=gcc




x86:
	gcc  src/multi.c -g -o matmul/multi.x86 -lm -lpthread
	gcc  src/tiled_matmul_cpu-paralell-16.c -g -o matmul/tiled_matmul_cpu-paralell-16.x86 -static -lm -lpthread -fPIC
	gcc  src/tiled_matmul_cpu-paralell-128.c -g -o matmul/tiled_matmul_cpu_128-paralell.x86 -static -lm -lpthread -fPIC
	gcc  src/tiled_matmul_cpu-paralell-512.c -g -o matmul/tiled_matmul_cpu_512-paralell.x86 -static -lm -lpthread -fPIC
riscv:
	${RISCV_GCC_COMPILER}  src/multi.c -g -o                         matmul/multi.riscv -lm -lpthread
	${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-16.c  -g -o matmul/tiled_matmul_cpu-paralell-16.riscv -static -lm -lpthread -fPIC
	${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-128.c -g -o matmul/tiled_matmul_cpu_128-paralell.riscv -static -lm -lpthread -fPIC
	${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-512.c -g -o matmul/tiled_matmul_cpu_512-paralell.riscv -static -lm -lpthread -fPIC
all:
	gcc  src/multi.c -g -o matmul/multi.x86 -lm -lpthread
	gcc  src/tiled_matmul_cpu-paralell-16.c -g -o matmul/tiled_matmul_cpu-paralell-16.x86 -static -lm -lpthread -fPIC
	gcc  src/tiled_matmul_cpu-paralell-128.c -g -o matmul/tiled_matmul_cpu_128-paralell.x86 -static -lm -lpthread -fPIC
	gcc  src/tiled_matmul_cpu-paralell-512.c -g -o matmul/tiled_matmul_cpu_512-paralell.x86 -static -lm -lpthread -fPIC
	${RISCV_GCC_COMPILER}  src/multi.c -g -o                         matmul/multi.riscv -lm -lpthread
	${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-16.c  -g -o matmul/tiled_matmul_cpu-paralell-16.riscv -static -lm -lpthread -fPIC
	${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-128.c -g -o matmul/tiled_matmul_cpu_128-paralell.riscv -static -lm -lpthread -fPIC
	${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-512.c -g -o matmul/tiled_matmul_cpu_512-paralell.riscv -static -lm -lpthread -fPIC
clean:
	rm -rf matmul/*.riscv matmul/*.x86


# ${RISCV_GCC_COMPILER}  src/multi.c -g -o bin/multi.riscv -static -lm -lpthread -fPIC
# gcc src/tiled_matmul_cpu-paralell-28.c -g -o bin/tiled_matmul_cpu_28-paralell.x86 -static -lm -lpthread -fPIC
# gcc src/tiled_matmul_cpu-paralell-128.c -g -o bin/tiled_matmul_cpu_128-paralell.x86 -static -lm -lpthread -fPIC
# ${RISCV_GCC_COMPILER}  src/include/resnet50_params.h src/include/images.h src/tiled_conv_cpu-paralell.c -g -o bin/tiled_conv_cpu-paralell.riscv -static -lm -lpthread -fPIC
# ${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-28.c -g -o bin/tiled_matmul_cpu_28-paralell.riscv -static -lm -lpthread -fPIC
# ${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-128.c -g -o bin/tiled_matmul_cpu_128-paralell.riscv -static -lm -lpthread -fPIC
# ${RISCV_GCC_COMPILER}  src/tiled_matmul_cpu-paralell-512.c -g -o bin/tiled_matmul_cpu_512-paralell.riscv -static -lm -lpthread -fPIC
# ${RISCV_GCC_COMPILER}  src/hello-world.c -g -o bin/hello.riscv -static -lm -lpthread -fPIC
	
#${RISCV_GCC_COMPILER}  src/qsort/qsort_main.c src/qsort/*.c src/qsort/*.h -g -o bin/qsort.riscv -static -lm -lpthread -fPIC