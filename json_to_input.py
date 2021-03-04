import argparse
import json
import struct

K_LABEL = "K"
PICKING_LIMIT_LABEL = "initialisation picking limit"
VECTORS_LABEL = "vectors"


def parse_args():
    parser = argparse.ArgumentParser(description="Build a binary input from a json file")
    parser.add_argument("json_file", help="The path to the json file")
    parser.add_argument("binary_file", help="The path to the binary file that can be fed to your k-means program")
    return parser.parse_args()


args = parse_args()

# Read

with open(args.json_file) as file_obj:
    json_obj = json.load(file_obj)

# Check JSON input

assert K_LABEL in json_obj, f"The number of centroids '{K_LABEL}' is not given"
K = json_obj[K_LABEL]
assert isinstance(K, int) and 0 < K <= 2 ** 32, \
    "The number of centroids is not a strictly positive integer writable in 32 bits in C"

assert PICKING_LIMIT_LABEL in json_obj, \
    "The limit number of initialisation vectors to consider for combinations is not given"
picking_limit = json_obj[PICKING_LIMIT_LABEL]
assert isinstance(picking_limit, int) and 0 < picking_limit <= 2 ** 32, \
    "The limit number of initialisation vectors to consider for combinations" \
    " is not a strictly positive integer writable in 32 bits in C"

assert VECTORS_LABEL in json_obj, "The vectors are not given"
vectors = json_obj[VECTORS_LABEL]
assert isinstance(vectors, list), "The vectors are not given as a list"
assert len(vectors) >= picking_limit, "The number of vectors is smaller than the limit number of initialization vectors"

assert isinstance(vectors[0], list), "The first vector is not a list"
dimension = len(vectors[0])
assert 0 < dimension <= 2 ** 32, "The dimension of the first vector is not a strictly positive number" \
                                 " writable in 32 bits in C"
numbers = []
for i, vector in enumerate(vectors):
    assert isinstance(vector, list), f"The vector number {i}, {vector}, is not a list"
    assert dimension == len(vector), f"The vector number {i}, {vector}, is not of dimension {dimension}"
    for j, x in enumerate(vector):
        assert isinstance(x, int), f"The dimension number {j} ({x}) of vector number {i}, {vector}, is not an integer"
        assert -2 ** 64 < x < 2 ** 64, f"The dimension number {j} ({x}) of vector number {i}, {vector}," \
                                       f" is not representable in 64 bits in C"
    numbers.extend(vector)

# Write the structure in network byte-order

binary_data = struct.pack("!IQ" + ("q" * len(numbers)), dimension, len(numbers) // dimension, *numbers)
with open(args.binary_file, "wb") as file_obj:
    file_obj.write(binary_data)
