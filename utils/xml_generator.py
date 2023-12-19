from clixon.element import Element
import random
import string
import argparse


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))

    return result_str


def create_tags(root, nr=10):
    idx = 0
    new_root = root

    while idx < nr:
        new_tag = get_random_string(10)
        new_attr = {get_random_string(10): get_random_string(50)}
        new_root.create(new_tag, attributes=new_attr)
        new_root = getattr(new_root, new_tag)

        idx += 1

    new_root.set_data(get_random_string(20))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--depth", type=int, default=10)
    parser.add_argument("-i", "--iters", type=int, default=10)
    parser.add_argument("-w", "--write", type=str, default="test.xml")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = parse_args()
    root = Element("root")
    depth = random.randint(1, args.depth)
    iters = random.randint(1, args.iters)
    write = args.write

    for i in range(iters):
        create_tags(root, depth)

    try:
        with open(write, "w") as f:
            f.write(root.dumps())
    except Exception as e:
        print("Error writing to file: {}".format(e))
