"""Shared, save-compatible map ordering for maps and event scripts."""
import glob
import os


def ordered_map_sources(root):
    sources = sorted(glob.glob(os.path.join(root, 'assets/maps/*.map')))
    order_path = os.path.join(root, 'assets/maps/order.txt')
    with open(order_path, encoding='utf-8') as f:
        order = [line.strip() for line in f if line.strip()]
    rank = {name: i for i, name in enumerate(order)}
    # Stable sorting leaves new maps in alphabetical order at the end.
    return sorted(sources, key=lambda p: rank.get(os.path.basename(p)[:-4], len(order)))
