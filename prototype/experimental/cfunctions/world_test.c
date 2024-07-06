#include <stdio.h>
#include <stdlib.h>

#define TABLE_SIZE 100 // Initial size of the hash table

typedef struct {
    int x;
    int y;
} Coordinates;

typedef struct {
    Coordinates key;
    int value;
} KeyValuePair;

typedef struct {
    KeyValuePair* pairs;
    int size;
    int capacity;
} HashTable;

unsigned int hash(Coordinates key) {
    // A simple hash function that combines x and y coordinates
    unsigned int hashValue = 0;
    hashValue = (hashValue << 5) + key.x;
    hashValue = (hashValue << 5) + key.y;
    return hashValue;
}

void initHashTable(HashTable* table) {
    table->pairs = malloc(sizeof(KeyValuePair) * TABLE_SIZE);
    table->size = 0;
    table->capacity = TABLE_SIZE;
}

void insert(HashTable* table, Coordinates key, int value) {
    if (table->size == table->capacity) {
        table->capacity *= 2;
        table->pairs = realloc(table->pairs, sizeof(KeyValuePair) * table->capacity);
        if (table->pairs == NULL) {
            fprintf(stderr, "Memory reallocation failed\n");
            exit(1);
        }

        // Reset the value field of the newly allocated pairs
        for (int i = table->size; i < table->capacity; i++) {
            table->pairs[i].value = -1;
        }
    }

    unsigned int index = hash(key) % table->capacity;
    int originalIndex = index;
    while (table->pairs[index].value != -1) {
        index = (index + 1) % table->capacity;
        if (index == originalIndex) {
            // All buckets are occupied, resize the hash table
            insert(table, key, value); // Recursive call to trigger resizing
            return;
        }
    }

    table->pairs[index].key = key;
    table->pairs[index].value = value;
    table->size++;
}


int find(HashTable* table, Coordinates key) {
    unsigned int index = hash(key) % table->capacity;
    while (table->pairs[index].value != -1) {
        printf("dosa\n");
        if (table->pairs[index].key.x == key.x && table->pairs[index].key.y == key.y) {
            return table->pairs[index].value;
        }
        index = (index + 1) % table->capacity;
    }
    return -1; // Key not found
}

void freeHashTable(HashTable* table) {
    free(table->pairs);
    table->size = 0;
    table->capacity = 0;
}

int main() {
    HashTable table;
    initHashTable(&table);

    // Insert chunks into the hash table
    insert(&table, (Coordinates){-13, 2185}, 0);
    insert(&table, (Coordinates){128, 29}, 1);

    // Retrieve the indices of chunks using coordinates
    int index1 = find(&table, (Coordinates){-13, 2185});
    if (index1 != -1) {
        printf("Chunk at (-13, 2185): Index = %d\n", index1);
    }

    int index2 = find(&table, (Coordinates){128, 29});
    if (index2 != -1) {
        printf("Chunk at (128, 29): Index = %d\n", index2);
    }

    freeHashTable(&table);

    return 0;
}
