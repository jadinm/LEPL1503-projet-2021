import argparse
import copy
import csv
import itertools
import math
import struct
import sys
from typing import List, Tuple

LOG = False

parser = argparse.ArgumentParser(description="Build the k-means")
parser.add_argument("input_file", help="The path to the binary input file that describe an instance of k-means", type=argparse.FileType('rb'), default=sys.stdin.buffer)
parser.add_argument("-f", "--output-file", help="The path to the CSV output file that describes the solutions", type=argparse.FileType('w'), default=sys.stdout)
parser.add_argument("-d", "--distance", help="either \"manhattan\" or \"euclidean\": chooses the distance function to use for the k-means algorithm", type=str, default="manhattan")
parser.add_argument("-k", type=int, help="The number of clusters to find")
parser.add_argument("-p", "--picking_limit", help="Only the combinations of vectors with an index in [0, picking_limit["
                                          " can serve as initial centroids")
parser.add_argument("-q", help="quiet mode: if set, does not output the clusters content (the \"clusters\" column is simply not present in the csv)", action="store_true")
args = parser.parse_args()

print(args, file=sys.stderr)
# Parse binary file

binary_data = args.input_file.read()

K = int(args.k)
picking_limit = int(args.picking_limit)
dimension, nbr_vectors = struct.unpack("!IQ", binary_data[:12])  # Unpack binary data in network-byte order
print(f"K = {K}, dimension = {dimension}, picking_limit = {picking_limit}", file=sys.stderr)

vectors: List[Tuple] = []
start_vectors_offset = 12  # bytes
for i in range(nbr_vectors):
    v: List[int] = []
    for j in range(dimension):
        v.append(struct.unpack_from("!q", binary_data, start_vectors_offset + i * dimension * 8 + j * 8)[0])
    vectors.append(tuple(v))
if LOG:
    print(f"vectors = {vectors}", file=sys.stderr)


def update_centroids(clusters: List[List[Tuple]]) -> List[Tuple]:
    """Compute the new centroids from the the current vectors"""
    centroids = []
    for k in range(K):
        vector_sum = tuple(0 for _ in range(dimension))
        for vector in clusters[k]:
            vector_sum = tuple(vector_sum[m] + vector[m] for m in range(dimension))

        # /!\ we here use int(a/b) instead of a//b because // implements the floor division and with negative
        # numbers this is not an integer division as it rounds the result down
        centroids.append(tuple(int(vector_sum[m] / len(clusters[k])) for m in range(dimension)))

    if LOG:
        print(f"\tUpdate centroids to {centroids}", file=sys.stderr)
    return centroids


def euclidean_distance_squared(a: Tuple, b: Tuple) -> int:
    return sum([(a[m] - b[m]) * (a[m] - b[m]) for m in range(dimension)])


def manhattan_distance_squared(a: Tuple, b: Tuple) -> int:
    val = sum([abs((b[m] - a[m])) for m in range(dimension)])
    return int(val*val)


DISTANCE_SQUARED = manhattan_distance_squared if args.distance == "manhattan" else euclidean_distance_squared


def assign_vectors_to_centroids(centroids: List[Tuple], clusters: List[List[Tuple]]) \
        -> Tuple[bool, List[List[Tuple]]]:
    """
    Assign vectors to centroids
    :return: True iff the assignation has changed from the last iteration
    """
    if LOG:
        print("\tAssign points to centroids", file=sys.stderr)

    new_clusters = [[] for _ in range(K)]
    unchanged = True
    for current_centroid_idx in range(K):
        for vector in clusters[current_centroid_idx]:
            # Find the closest centroid for the vector
            closest_centroid_idx = None
            closest_centroid_distance = math.inf
            for centroid_idx in range(len(centroids)):
                distance = DISTANCE_SQUARED(vector, centroids[centroid_idx])

                if distance < closest_centroid_distance:
                    closest_centroid_idx = centroid_idx
                    closest_centroid_distance = distance

            # Add the vector to the cluster of the closest centroid

            if LOG:
                print(
                    f"\t\t{vector} closest to {centroids[closest_centroid_idx]} (before {centroids[current_centroid_idx]})", file=sys.stderr)
            new_clusters[closest_centroid_idx].append(vector)

            # Observe if the current vector changes its cluster
            unchanged = unchanged and closest_centroid_idx == current_centroid_idx

    return not unchanged, new_clusters


def k_means(initial_centroids: List[Tuple]) -> Tuple[List[Tuple], List[List[Tuple]]]:
    """
    :param initial_centroids: The initial list of the K centroids
    :return: A tuple containing the final centroids and the final clusters
    """

    if LOG:
        print(f"Computing k-means with initial centroids = {initial_centroids}", file=sys.stderr)
    centroids = initial_centroids
    clusters: List[List[Tuple]] = [[] for _ in range(K)]
    clusters[0] = copy.copy(vectors)  # Assign all points to the first cluster

    changed = True
    while changed:
        changed, clusters = assign_vectors_to_centroids(centroids, clusters)
        centroids = update_centroids(clusters)

    return centroids, clusters


def distortion(centroids: List[Tuple], clusters: List[List[Tuple]]) -> int:
    current_sum = 0
    for k, cluster in enumerate(clusters):
        for vector in cluster:
            current_sum += DISTANCE_SQUARED(vector, centroids[k])
    return current_sum


sol_initial_centroids = None
sol_centroids = None
sol_clusters = None
sol_distortion = math.inf

initial_centroid_lists = []
distortion_list = []
centroid_lists = []
cluster_lists = []

for i, centroid_initial_list in enumerate(itertools.combinations(vectors[:picking_limit], K)):
    combination_centroids, combination_clusters = k_means(list(centroid_initial_list))
    combination_distortion = distortion(combination_centroids, combination_clusters)

    if sol_distortion > combination_distortion:
        sol_distortion = combination_distortion
        sol_centroids = combination_centroids
        sol_clusters = combination_clusters
        sol_initial_centroids = list(centroid_initial_list)

    initial_centroid_lists.append(centroid_initial_list)
    distortion_list.append(combination_distortion)
    centroid_lists.append(combination_centroids)
    cluster_lists.append(combination_clusters)

if LOG:
    print(f"Best initialisation centroids:\n{sol_initial_centroids}", file=sys.stderr)
    print(f"Best centroids:\n{sol_centroids}", file=sys.stderr)
    print(f"Best clusters:\n{sol_clusters}", file=sys.stderr)
    print(f"Minimal sum of squared distances:\n{sol_distortion}", file=sys.stderr)

# Produce csv

fieldnames = ["initialization centroids", "distortion", "centroids"]
if not args.q:
    fieldnames.append("clusters")

writer = csv.DictWriter(args.output_file, delimiter=',',
                        fieldnames=fieldnames)
writer.writeheader()
for i in range(len(initial_centroid_lists)):
    row = {
        "initialization centroids": f"{list(initial_centroid_lists[i])}",
        "distortion": distortion_list[i],
        "centroids": f"{centroid_lists[i]}",
    }
    if not args.q:
        row["clusters"] = f"{cluster_lists[i]}"
    writer.writerow(row)
