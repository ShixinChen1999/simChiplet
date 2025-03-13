#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

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
        int ret = pthread_create(&threads[i], NULL, print_message_function, (void *) message);
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
    for(int i=0;i<10000;i++){
        sum+=i;
    }
    printf("%d\n", sum);
}