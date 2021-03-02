import argparse
import copy
import csv
import itertools
import math
import struct
from typing import List, Tuple

parser = argparse.ArgumentParser(description="Build the k-means")
parser.add_argument("input_file", help="The path to the binary input file that describe an instance of k-means")
parser.add_argument("output_file", help="The path to the CSV output file that describes the solutions")
args = parser.parse_args()

# Parse binary file

with open(args.input_file, "rb") as file_obj:
    binary_data = file_obj.read()

K, dimension, picking_limit = struct.unpack("!III", binary_data[:12])  # Unpack binary data in network-byte order
print(f"K = {K}, dimension = {dimension}, picking_limit = {picking_limit}")

vectors: List[Tuple[int, int]] = []
start_vectors_offset = 4 * 3
nbr_vectors = (len(binary_data) - start_vectors_offset) // 8 // dimension
for i in range(nbr_vectors):
    v: List[int] = []
    for j in range(dimension):
        v.append(struct.unpack_from("!q", binary_data, start_vectors_offset + i * dimension * 8 + j * 8)[0])
    vectors.append(tuple(v))
print(f"vectors = {vectors}")


def update_centroids(clusters: List[List[Tuple[int, int]]]) -> List[Tuple[int, int]]:
    """Compute the new centroids from the the current vectors"""
    centroids = []
    for k in range(K):
        vector_sum = (0, 0)
        for vector in clusters[k]:
            vector_sum = (vector_sum[0] + vector[0], vector_sum[1] + vector[1])

        # TODO Change here if we use floating points
        centroids.append((round(vector_sum[0] // len(clusters[k])), round(vector_sum[1] // len(clusters[k]))))

    print(f"\tUpdate centroids to {centroids}")
    return centroids


def euclidean_distance_squared(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return (a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1])


def manhattan_distance_squared(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return ((b[0] - a[0]) + (b[1] - a[1])) * ((b[0] - a[0]) + (b[1] - a[1]))


def assign_vectors_to_centroids(centroids: List[Tuple[int, int]], clusters: List[List[Tuple[int, int]]]) \
        -> Tuple[bool, List[List[Tuple[int, int]]]]:
    """
    Assign vectors to centroids
    :return: True iff the assignation has changed from the last iteration
    """
    print("\tAssign points to centroids")

    new_clusters = [[] for _ in range(K)]
    unchanged = True
    for current_centroid_idx in range(K):
        for vector in clusters[current_centroid_idx]:
            # Find the closest centroid for the vector
            closest_centroid_idx = None
            closest_centroid_distance = math.inf
            for centroid_idx in range(len(centroids)):
                distance = euclidean_distance_squared(vector, centroids[centroid_idx])

                if distance < closest_centroid_distance:
                    closest_centroid_idx = centroid_idx
                    closest_centroid_distance = distance

            # Add the vector to the cluster of the closest centroid
            print(
                f"\t\t{vector} closest to {centroids[closest_centroid_idx]} (before {centroids[current_centroid_idx]})")
            new_clusters[closest_centroid_idx].append(vector)

            # Observe if the current vector changes its cluster
            unchanged = unchanged and closest_centroid_idx == current_centroid_idx

    return not unchanged, new_clusters


def k_means(initial_centroids: List[Tuple[int, int]]) -> Tuple[List[Tuple[int, int]], List[List[Tuple[int, int]]]]:
    """
    :param initial_centroids: The initial list of the K centroids
    :return: A tuple containing the final centroids and the final clusters
    """
    print(f"Computing k-means with initial centroids = {initial_centroids}")
    centroids = initial_centroids
    clusters: List[List[Tuple[int, int]]] = [[] for _ in range(K)]
    clusters[0] = copy.copy(vectors)  # Assign all points to the first cluster

    changed = True
    while changed:
        changed, clusters = assign_vectors_to_centroids(centroids, clusters)
        centroids = update_centroids(clusters)

    return centroids, clusters


def distortion(centroids: List[Tuple[int, int]], clusters: List[List[Tuple[int, int]]]) -> int:
    current_sum = 0
    for k, cluster in enumerate(clusters):
        for vector in cluster:
            current_sum += euclidean_distance_squared(vector, centroids[k])
    return current_sum


sol_initial_centroids = None
sol_centroids = None
sol_clusters = None
sol_distortion = math.inf

initial_centroid_lists = []
distortion_list = []
centroid_lists = []
cluster_lists = []

for centroid_initial_list in itertools.combinations(vectors[:picking_limit], K):
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

print(f"Best initialisation centroids:\n{sol_initial_centroids}")
print(f"Best centroids:\n{sol_centroids}")
print(f"Best clusters:\n{sol_clusters}")
print(f"Minimal sum of squared distances:\n{sol_distortion}")

# Produce csv

with open(args.output_file, "w") as file_obj:
    writer = csv.DictWriter(file_obj, delimiter=',',
                            fieldnames=["initialization centroids", "distortion", "centroids", "clusters"])
    writer.writeheader()
    for i in range(len(initial_centroid_lists)):
        writer.writerow({
            "initialization centroids": f"{list(initial_centroid_lists[i])}",
            "distortion": distortion_list[i],
            "centroids": f"{centroid_lists[i]}",
            "clusters": f"{cluster_lists[i]}"
        })
