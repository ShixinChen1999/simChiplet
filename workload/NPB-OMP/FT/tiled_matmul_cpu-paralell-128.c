// See LICENSE for license details.

#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdio.h>
#include <pthread.h>
#ifndef BAREMETAL
#include <sys/mman.h>
#endif

#include <stdint.h>

#if defined(__i386__)

static __inline__ uint64_t rdtsc(void) {
  uint64_t x;
  __asm__ volatile ("rdtsc" : "=A" (x));
  return x;
}

#elif defined(__x86_64__)

static __inline__ uint64_t rdtsc(void) {
  uint64_t a, d;
  __asm__ volatile ("rdtsc" : "=a" (a), "=d" (d));
  return (d << 32) | a;
}

#endif

#define DIM 128

// 函数声明
void fillMatrix(int matrix[DIM][DIM]);
void printMatrix(int matrix[DIM][DIM]);
void multiplyMatrices(int a[DIM][DIM], int b[DIM][DIM], int result[DIM][DIM]);

// 填充矩阵函数
void fillMatrix(int matrix[DIM][DIM]) {
    for (int i = 0; i < DIM; i++) {
        for (int j = 0; j < DIM; j++) {
            matrix[i][j] = rand() % 10 + 1;
        }
    }
}

// 打印矩阵函数
void printMatrix(int matrix[DIM][DIM]) {
    for (int i = 0; i < DIM; i++) {
        for (int j = 0; j < DIM; j++) {
            printf("%d ", matrix[i][j]);
        }
        printf("\n");
    }
}

// 矩阵乘法函数
void multiplyMatrices(int a[DIM][DIM], int b[DIM][DIM], int result[DIM][DIM]) {
    for (int i = 0; i < DIM; i++) {
        for (int j = 0; j < DIM; j++) {
            result[i][j] = 0;
            for (int k = 0; k < DIM; k++) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
}


void *matmul_thread_2(void* arg) {
    printf("Thread number %ld\n", (long)arg);
    int A[DIM][DIM], B[DIM][DIM], C[DIM][DIM];

    // 初始化随机数生成器
    srand(time(NULL));

    // 填充矩阵A和B
    fillMatrix(A);
    fillMatrix(B);

   // 打印矩阵A和B
    // printf("Matrix A:\n");
    // printMatrix(A);
    // printf("Matrix B:\n");
    // printMatrix(B);

    // 矩阵乘法 A * B = C

    uint64_t start, end;

    start = rdtsc();
    multiplyMatrices(A, B, C);
    end = rdtsc();

    printf("Cycles taken: %lu\n", end - start);

    

    // // 打印结果矩阵C
    // printf("Result Matrix C:\n");
    // printMatrix(C);
}



void *print_message_function(void *ptr)
{
    char *message;
    message = (char *) ptr;
    printf("%s\n", message);
    int sum=0;
    for(int i=0;i<1000;i++){
        sum+=i;
    }
    printf("%d\n", sum);
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        printf("Usage: %s [number of threads]\n", argv[0]);
        return 1;
    }

    int num_threads = atoi(argv[1]);
    pthread_t threads[num_threads];
    unsigned index = 0;  
    
    for (index = 0; index< num_threads; index++) {
        int ret = pthread_create(&threads[index], NULL, matmul_thread_2, (void*) (long)index);
        //printf("ret=%d\n",ret);
        if (ret) {
            fprintf(stderr, "Error - pthread_create() return code: %d\n", ret);
            exit(EXIT_FAILURE);
        }
    }

    // for (int i = 0; i < num_threads; i++) {
    //     pthread_join(threads[i], NULL);
    // }
    for (int index = 0; index < num_threads; ++index) {
        int result_code = pthread_join(threads[index], NULL);
        if (result_code) {
            printf("ERROR; return code from pthread_join() is %d\n", result_code);
            return -1;
        }
    }

    return 0;
}





