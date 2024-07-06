/* everything related to the world except generation and drawing

world (array):
-> chunks

chunk (struct):
-> array of blocks
-> array of entities

* all chunks in world are loaded chunks
* all chunks in world, which don't border to unloaded chunks get updated
* all visible chunks are updated chunks

def update()
- updates all blocks and enities in all updated chunks
- returns all updated chunks for drawing and entity updating

def set_loaded(size)
- set the width and height of the loaded chunks independent of the coord

def get_loaded()
- returns coords of all loaded chunks

def load(coords, chunks)
- inserts new chunks into loaded chunks

def unload(coords)
- removes chunks from loaded chunks

http://www.laurentluce.com/posts/python-dictionary-implementation/
https://www.wangxinliu.com/tech/program/ModernCpp9/

*/

#include <stdio.h>
#define CHUNK_SIZE 16


typedef struct {
    int blocks[CHUNK_SIZE][CHUNK_SIZE];
    int** entites;
} Chunk;


Chunk** chunks = NULL;
int loaded_chunks[] = {0, 0, 0, 0}; // all chunks, which should be loaded or are loaded
int should_loaded_chunks[] = {0, 0, 0, 0}; // all chunks, which should be loaded, but aren't
int should_loaded_chunks_num = 0;


// set the position of the loaded chunks
void set_position_loaded_chunks(x, y) {
    loaded_chunks[0] = x;
    loaded_chunks[1] = y;
}


// set the size of the loaded chunks
void set_size_loaded_chunks(width, height) {
    loaded_chunks[2] = width;
    loaded_chunks[3] = height;
}


// get the coords of all loaded chunks
void get_loaded_chunks(int* coords) {
    *coords = loaded_chunks;
}


// get the coords of all chunks, which should be loaded and return length
int get_should_loaded_chunks(int* coords) {
    *coords = should_loaded_chunks;
    return should_loaded_chunks_num;
}


// update all loaded chunks and all entities in them
void update() {
    for (int chunk_x = loaded_chunks[0]; chunk_x <= loaded_chunks[0] + loaded_chunks[2]; chunk_x++) {
        for (int chunk_y = loaded_chunks[1]; chunk_y <= loaded_chunks[1] + loaded_chunks[3]; chunk_y++) {

        }
    }
}