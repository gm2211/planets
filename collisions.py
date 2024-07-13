import numpy as np
from scipy.spatial import cKDTree
from typing import List

from objects import Circle

def bounding_box(sphere: Circle) -> Square:

def validate_no_collitions(candidate: Circle, circles: List[Circle]) -> bool:
    boundingBoxes = np.array([(1, 1, 1, 2, 2, 2), (3, 3, 3, 6, 6, 6), (5, 5, 5, 7, 7, 7), (7, 7, 7, 8, 8, 8)])

    centers = boundingBoxes[:, :3] + 0.5 * (boundingBoxes[:, 3:] - boundingBoxes[:, :3])

    tree = cKDTree(centers)

    distances, indices = tree.query(centers, k=3)

    colisions = []
    for i in range(len(indices)):
        for j in indices[i, 1:]:
            if i < j and not np.all(np.logical_or(boundingBoxes[i, :3] > boundingBoxes[j, 3:],
                                                  boundingBoxes[i, 3:] < boundingBoxes[j, :3])):
                collision = (boundingBoxes[i], boundingBoxes[j])
                colisions.append(collision)
                print(collision)
