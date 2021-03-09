import argparse
import csv
import json
import sys

import matplotlib.pyplot as plt

csv.field_size_limit(sys.maxsize)


def check_positive_or_min(value):
    if value == "min":
        return value
    try:
        value = int(value)
        if value < 0:
            raise argparse.ArgumentTypeError(f"{value} is an invalid positive integer value")
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is not an integer")
    return value


def parse_args():
    parser = argparse.ArgumentParser(description="Plot a set of clusters computed by the k-means algorithm"
                                                 " (it only works for vectors in two dimensions)")
    parser.add_argument("-i", "--csv-file", help="The path to the csv file containing the k-means output", type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument("index_solution", help="The index of the k-means solution to plot starting at 0 "
                                               "(set \"min\" to automatically choose the solution with minimum distortion)",
                        type=check_positive_or_min)
    parser.add_argument("-b", "--black",
                        help="If set, does color the points and does not display the centroid of the clusters.",
                        action="store_true")
    parser.add_argument("-o", "--output-file", help="The path to the output file (can be pdf or png)", type=str, default=None)

    return parser.parse_args()


args = parse_args()

# Recover clusters

solution_row = None
reader = csv.DictReader(args.csv_file)

# Check header
actual_field_names = reader.fieldnames
for expected_field_name in ["initialization centroids", "distortion", "centroids", "clusters"]:
    assert expected_field_name in actual_field_names, \
        f"Cannot find '{actual_field_names}' in the first line of the output csv at '{args.csv_file}'"

if args.index_solution == "min":
    solution_row = min(list(reader), key=lambda x: int(x["distortion"]))
else:
    # Get the correct solution row
    for i, row in enumerate(reader):
        if i == args.index_solution:
            solution_row = row
        break

assert solution_row is not None, \
    f"Reached the end of the file '{args.csv_file}' before finding the solution number {args.index_solution}"

solution_row["initialization centroids"] = json.loads(solution_row["initialization centroids"]
                                                      .replace("(", "[").replace(")", "]"))
solution_row["centroids"] = json.loads(solution_row["centroids"].replace("(", "[").replace(")", "]"))
solution_row["clusters"] = json.loads(solution_row["clusters"].replace("(", "[").replace(")", "]"))

print(f"initialization centroids = {solution_row['initialization centroids']}")
print(f"centroids = {solution_row['centroids']}")
print(f"clusters = {solution_row['clusters']}")

# Plot clusters
for cluster in solution_row["clusters"]:
    plt.scatter([vector[0] for vector in cluster], [vector[1] for vector in cluster], s=5, color="black" if args.black else None)

if not args.black:
    # Plot centroids
    plt.scatter([vector[0] for vector in solution_row["centroids"]], [vector[1] for vector in solution_row["centroids"]],
                color="black", marker="x", label="centroids")

if not args.black:
    plt.legend()
if args.output_file:
    plt.savefig(args.output_file)
else:
    plt.show()
