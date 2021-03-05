import argparse
import json
import struct
import sys

VECTORS_LABEL = "vectors"


def parse_args():
    parser = argparse.ArgumentParser(description="Build a binary input from a json file")
    parser.add_argument("json_file", help="The path to the json file", type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument("binary_file", help="The path to the binary file that can be fed to your k-means program", type=argparse.FileType('wb'), default=sys.stdout.buffer)
    return parser.parse_args()


args = parse_args()

# Read

json_obj = json.load(args.json_file)

# Check JSON input

assert VECTORS_LABEL in json_obj, "The vectors are not given"
vectors = json_obj[VECTORS_LABEL]
assert isinstance(vectors, list), "The vectors are not given as a list"

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
args.binary_file.write(binary_data)
