import argparse
import json
import random
import sys

parser = argparse.ArgumentParser(description="Generate a set of points")
parser.add_argument("-f", help="input file (default stdin)", type=argparse.FileType('r'), default=sys.stdin)
parser.add_argument("--seed", help="The prng seed (default = 42)", default=42, type=int)
parser.add_argument("--pretty", help="if set, pretty-print the json output", action="store_true")
parser.add_argument("-n", help="The total number of points to generate", type=int)


class Cluster(object):
    def __init__(self, center, std_devs):
        self.center = center
        self.std_devs = std_devs

    def get_point(self):
        return [int(random.gauss(mu, std_dev)) for (mu, std_dev) in zip(self.center, self.std_devs)]


if __name__ == "__main__":
    args = parser.parse_args()
    random.seed(args.seed)
    input_description = json.load(args.f)
    clusters = [Cluster(center=c["center"], std_devs=c["std_devs"]) for c in input_description]

    if not all([len(c.center) == len(c.std_devs) == len(clusters[0].center) for c in clusters]):
        raise Exception("invalid input")

    points = [random.choice(clusters).get_point() for _ in range(args.n)]

    json.dump({
        "initialisation picking limit": 4, # TODO: remove this
        "K": len(clusters[0].center),
        "vectors": points
    }, sys.stdout, indent=4 if args.pretty else None)
    print("")       # last newline for prettier output on the console


