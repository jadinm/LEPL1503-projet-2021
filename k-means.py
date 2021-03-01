import copy
import itertools
import math
from typing import List, Tuple

K: int = 2
vectors: List[Tuple[int, int]] = [(1, 1), (2, 2), (3, 4), (5, 7), (3, 5), (5, 5), (4, 5)]


def update_centroids(clusters: List[List[Tuple[int, int]]]) -> List[Tuple[int, int]]:
    """Compute the new centroids from the the current vectors"""
    centroids = []
    for i in range(K):
        vector_sum = (0, 0)
        for vector in clusters[i]:
            vector_sum = (vector_sum[0] + vector[0], vector_sum[1] + vector[1])

        # TODO Change here if we use floating points
        centroids.append((round(vector_sum[0] // len(clusters[i])), round(vector_sum[1] // len(clusters[i]))))

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
    for i, cluster in enumerate(clusters):
        for vector in cluster:
            current_sum += euclidean_distance_squared(vector, centroids[i])
    return current_sum


sol_initial_centroids = None
sol_centroids = None
sol_clusters = None
sol_distortion = math.inf

for centroid_initial_list in itertools.combinations(vectors, K):
    combination_centroids, combination_clusters = k_means(list(centroid_initial_list))
    combination_distortion = distortion(combination_centroids, combination_clusters)

    if sol_distortion > combination_distortion:
        sol_distortion = combination_distortion
        sol_centroids = combination_centroids
        sol_clusters = combination_clusters
        sol_initial_centroids = list(centroid_initial_list)

print(f"Best initialisation centroids:\n{sol_initial_centroids}")
print(f"Best centroids:\n{sol_centroids}")
print(f"Best clusters:\n{sol_clusters}")
print(f"Minimal sum of squared distances:\n{sol_distortion}")
