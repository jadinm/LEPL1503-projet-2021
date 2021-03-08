import argparse
import csv

parser = argparse.ArgumentParser(description="Compare two solutions")
parser.add_argument("csv_1", help="Path to the first solution csv file", type=argparse.FileType('r'))
parser.add_argument("csv_2", help="Path to the second solution csv file", type=argparse.FileType('r'))
args = parser.parse_args()

solution_row = None
reader_1 = csv.DictReader(args.csv_1)
reader_2 = csv.DictReader(args.csv_2)
keys = ["initialization centroids", "distortion", "centroids", "clusters"]

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
for row_1 in reader_1:
    centroids = row_1["initialization centroids"]
    assert centroids not in row_by_centroid_1, f"There are multiple times the same initialisation centroids" \
                                               f" '{row_1['initialization centroids']}' in the csv" \
                                               f" at '{args.csv_1.name}'"
    row_by_centroid_1[centroids] = row_1

used_row_by_centroid_1 = {}
for row_2 in reader_2:
    centroids = row_2["initialization centroids"]
    assert centroids in row_by_centroid_1, f"The solution for the centroids '{centroids}' is given in the csv" \
                                           f" at '{args.csv_2.name}' but not in the csv at '{args.csv_1.name}'"
    used_row_by_centroid_1[centroids] = row_by_centroid_1[centroids]
    for key in keys:
        assert row_by_centroid_1[centroids][key] == row_2[key], \
            f"Both '{key}' values for the initialisation centroids '{row_2['initialization centroids']}' are different."

# Check for lines that are in csv_1 but not in csv_2

for centroids, row in row_by_centroid_1.items():
    assert centroids in used_row_by_centroid_1, f"The solution for the centroids '{centroids}' is given in the csv" \
                                                f" at '{args.csv_1.name}' but not in the csv at '{args.csv_2.name}'"
