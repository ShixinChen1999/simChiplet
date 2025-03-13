// See LICENSE for license details.

#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <pthread.h>
#ifndef BAREMETAL
#include <sys/mman.h>
#endif
#include "include/gemmini_testutils.h"
#include "include/images.h"
#include "include/resnet50_params.h"

#define CHECK_RESULT 0

#define NO_BIAS 1
#define FULL_BIAS_WIDTH 1

#if FULL_BIAS_WIDTH
typedef acc_t ACC_T;
#else
typedef elem_t ACC_T;
#error variable-bitwidth bias not currently supported
#endif

#ifndef BAREMETAL
#define MAT_DIM_I 14
#define MAT_DIM_K 14
#define MAT_DIM_J 14
#else
#define MAT_DIM_I 28
#define MAT_DIM_K 28
#define MAT_DIM_J 28
#endif



void print_tile(elem_t* in, int tile_dim) {
  for (size_t r = 0; r < tile_dim; r++) {
    printf("row starts at: %p\n", in +r*MAT_DIM_J);
    for (size_t c = 0; c < tile_dim; c++) {
      printf("%d ", *(in +r*MAT_DIM_J + c));
    }
    printf("\n");
  }
}

void full_matmul(elem_t A[MAT_DIM_I][MAT_DIM_K], elem_t B[MAT_DIM_K][MAT_DIM_J], ACC_T D[MAT_DIM_I][MAT_DIM_J], full_t C_full[MAT_DIM_I][MAT_DIM_J]) {
  for (size_t r = 0; r < MAT_DIM_I; r++)
    for (size_t c = 0; c < MAT_DIM_J; c++) {
      C_full[r][c] = D[r][c];
      for (size_t k = 0; k < MAT_DIM_K; k++)
        C_full[r][c] += A[r][k]*B[k][c];
    }
}

void full_printMatrix(elem_t m[MAT_DIM_I][MAT_DIM_J]) {
  for (size_t i = 0; i < MAT_DIM_I; ++i) {
    for (size_t j = 0; j < MAT_DIM_J; ++j)
      printf("%d ", m[i][j]);
    printf("\n");
  }
}

int full_is_equal(elem_t x[MAT_DIM_I][MAT_DIM_J], elem_t y[MAT_DIM_I][MAT_DIM_J]) {
  for (size_t i = 0; i < MAT_DIM_I; ++i)
    for (size_t j = 0; j < MAT_DIM_J; ++j)
      if (x[i][j] != y[i][j])
        return 0;
  return 1;
}

void full_matscale(full_t full[MAT_DIM_I][MAT_DIM_J], elem_t out[MAT_DIM_I][MAT_DIM_J], acc_scale_t scale) {
  for (size_t r = 0; r < MAT_DIM_I; r++)                             
    for (size_t c = 0; c < MAT_DIM_J; c++) {
      // Scale element
      full_t scaled = ACC_SCALE(full[r][c], scale);

      // Saturate and cast element
#ifndef ELEM_T_IS_FLOAT
      full_t elem = scaled > elem_t_max ? elem_t_max : (scaled < elem_t_min ? elem_t_min : scaled);
      out[r][c] = elem;
#else
      out[r][c] = scaled; // TODO should we also saturate when using floats?
#endif
    }
} 

void *conv_thread() {
  // int DIM_I=0;
  // int DIM_J=0;
  // int DIM_K=0;

#ifndef BAREMETAL
    if (mlockall(MCL_CURRENT | MCL_FUTURE) != 0) {
      perror("mlockall failed");
      exit(1);
    }
#endif

    // if(argc!=4){
    //   printf("[error] Please input I, J, K\n");
    //   exit(1);
    // }else{
    //   DIM_I=atol(argv[1]);
    //   DIM_J=atol(argv[2]);
    //   DIM_K=atol(argv[3]);
    // }


    //gemmini_flush(0);
    printf("I,J,K= %d %d %d\n",MAT_DIM_I,MAT_DIM_J,MAT_DIM_K);
    

    static elem_t full_A[MAT_DIM_I][MAT_DIM_K] row_align(1);
    static elem_t full_B[MAT_DIM_K][MAT_DIM_J] row_align(1);
    static elem_t full_C[MAT_DIM_I][MAT_DIM_J] row_align(1);
    static ACC_T full_D[MAT_DIM_I][MAT_DIM_J] row_align_acc(1); // TODO don't use row_align_acc when ACC_T is elem_t

    static full_t gold_full[MAT_DIM_I][MAT_DIM_J];
    static elem_t gold[MAT_DIM_I][MAT_DIM_J];

#if CHECK_RESULT == 1
    // printf("Init A\n");
    for (size_t i = 0; i < MAT_DIM_I; ++i) {
      for (size_t j = 0; j < MAT_DIM_K; ++j) {
        full_A[i][j] = rand() % 2;
      }
    }

    // printf("Init B\n");
    for (size_t i = 0; i < MAT_DIM_K; ++i) {
      for (size_t j = 0; j < MAT_DIM_J; ++j) {
        full_B[i][j] = rand() % 2;
      }
    }

    // printf("Init D\n");
    for (size_t i = 0; i < MAT_DIM_I; ++i) {
      for (size_t j = 0; j < MAT_DIM_J; ++j) {
        full_D[i][j] = NO_BIAS ? 0 : rand() % 2;
      }
    }

    printf("Starting slow CPU matmul\n");
    unsigned long cpu_start = read_cycles();
    full_matmul(full_A, full_B, full_D, gold_full);
    unsigned long cpu_end = read_cycles();
    printf("Cycles taken: %u\n", cpu_end-cpu_start);
    full_matscale(gold_full, gold, ACC_SCALE_IDENTITY);
#endif

    printf("Starting fast CPU conv\n");
    unsigned long start = read_cycles();

    
    // start = read_cycles();

    tiled_conv_auto(
            conv_1_params.batch_size, conv_1_params.in_dim, conv_1_params.in_channels,
            conv_1_params.out_channels, conv_1_params.out_dim,
            conv_1_params.stride, 1, 1, conv_1_params.padding, conv_1_params.kernel_size,
            false, false, false, false, false,

            (elem_t*)images, (elem_t*)conv_1_w, (acc_t*)conv_1_b, (elem_t*)conv_1_out_pooled,

            RELU, conv_1_params.output_scale, 0,
            conv_1_params.pool_size, conv_1_params.pool_stride, conv_1_params.pool_padding,

            CPU);

    

    // end = read_cycles();
    
    // printf("conv  cycles: %llu \n", end - start);


    unsigned long end = read_cycles();
    printf("Cycles taken: %u\n", end-start);

#if CHECK_RESULT == 1
    if (!full_is_equal(full_C, gold)) {
      printf("C:\n");
      full_printMatrix(full_C);
      printf("Gold:\n");
      full_printMatrix(gold);
      printf("\n");

      exit(1);
    }
#endif

  //exit(0);
}



void *print_message_function(void *ptr);

int main(int argc, char *argv[])
{
    if (argc != 2) {
        printf("Usage: %s [number of threads]\n", argv[0]);
        return 1;
    }

    int num_threads = atoi(argv[1]);
    pthread_t threads[num_threads];
    const char *message = "Thread";

    for (int i = 0; i < num_threads; i++) {
        int ret = pthread_create(&threads[i], NULL, conv_thread, (void *) message);
        printf("ret=%d\n",ret);
        if (ret) {
            fprintf(stderr, "Error - pthread_create() return code: %d\n", ret);
            exit(EXIT_FAILURE);
        }
    }

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    return 0;
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



