#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static void sum_arr(uint8_t *arr, uint8_t arr_len, uint8_t *sum) {
    for (int i = 0; i < arr_len; i++) {
        *sum += arr[i];
    }
}

int main() {
    uint8_t arr[] = {6, 12, 1, 4};
    uint8_t arr_len = sizeof(arr) / sizeof(uint8_t);

    uint8_t sum;
    sum_arr(arr, arr_len, &sum);
    printf("%d", sum);

    return 0;
}