import argparse
import csv
import json
import sys
from ast import literal_eval

csv.field_size_limit(sys.maxsize)


def parse_point(point_str):
    return literal_eval(point_str)


def parse_centroids(centroids_str):
    return frozenset(literal_eval(centroids_str))


def parse_clusters(clusters_str):
    clusters_list = literal_eval(clusters_str)
    retval = set()
    for cluster in clusters_list:
        retval.add(frozenset(cluster))
    return retval


parser = argparse.ArgumentParser(description="Compare two solutions")
parser.add_argument("csv_1", help="Path to the first solution csv file", type=argparse.FileType('r'))
parser.add_argument("csv_2", help="Path to the second solution csv file", type=argparse.FileType('r'))
args = parser.parse_args()

solution_row = None
reader_1 = csv.DictReader(args.csv_1)
reader_2 = csv.DictReader(args.csv_2)
keys = ["initialization centroids", "distortion", "clusters", "centroids"]
parsing_functions = [parse_centroids, int, parse_clusters, parse_centroids]

# Check header

field_names_1 = reader_1.fieldnames
field_names_2 = reader_2.fieldnames
for key in keys:
    assert key in field_names_1, \
        f"Cannot find '{key}' in the first line of the output csv at '{args.csv_1.name}'"
    assert key in field_names_2, \
        f"Cannot find '{key}' in the first line of the output csv at '{args.csv_2.name}'"

# Check each solution line

row_by_centroid_1 = {}
for i, row_1 in enumerate(reader_1):
    initialization_centroids = parse_centroids(row_1["initialization centroids"])
    assert initialization_centroids not in row_by_centroid_1, f"There are multiple times the same initialisation centroids" \
                                               f" '{row_1['initialization centroids']}' in the csv" \
                                               f" at '{args.csv_1.name}'"
    row_by_centroid_1[initialization_centroids] = {
        "initialization centroids": initialization_centroids,
        "distortion": int(row_1["distortion"]),
        "centroids": parse_centroids(row_1["centroids"]),
        "clusters": parse_clusters(row_1["clusters"])
    }

used_row_by_centroid_1 = {}
for i, row_2 in enumerate(reader_2):
    initialization_centroids = parse_centroids(row_2["initialization centroids"])
    assert initialization_centroids in row_by_centroid_1, f"The solution for the centroids '{initialization_centroids}' is given in the csv" \
                                           f" at '{args.csv_2.name}' but not in the csv at '{args.csv_1.name}'"
    used_row_by_centroid_1[initialization_centroids] = row_by_centroid_1[initialization_centroids]
    for key, type_f in zip(keys, parsing_functions):
        val = type_f(row_2[key])
        assert row_by_centroid_1[initialization_centroids][key] == val, \
            f"Both '{key}' values for the initialisation centroids '{row_2['initialization centroids']}' are different: '{row_by_centroid_1[initialization_centroids][key]}' != '{val}'"

# Check for lines that are in csv_1 but not in csv_2

for centroids, row in row_by_centroid_1.items():
    assert centroids in used_row_by_centroid_1, f"The solution for the centroids '{centroids}' is given in the csv" \
                                                f" at '{args.csv_1.name}' but not in the csv at '{args.csv_2.name}'"

print("Success !")
