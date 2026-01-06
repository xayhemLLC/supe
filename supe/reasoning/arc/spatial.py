"""Spatial reasoning and transformations for ARC objects and grids."""

from typing import Tuple, List, Optional, Dict
import numpy as np

from supe.reasoning.arc.grid import ARCGrid, ARCObject


class SpatialReasoner:
    """Performs spatial transformations and reasoning."""

    def rotate_grid_90(self, grid: ARCGrid, clockwise: bool = True) -> ARCGrid:
        """Rotate grid 90 degrees."""
        if clockwise:
            new_data = np.rot90(grid.data, k=-1)  # -1 = clockwise
        else:
            new_data = np.rot90(grid.data, k=1)   # 1 = counterclockwise

        return ARCGrid(data=new_data, task_id=grid.task_id)

    def rotate_grid_180(self, grid: ARCGrid) -> ARCGrid:
        """Rotate grid 180 degrees."""
        new_data = np.rot90(grid.data, k=2)
        return ARCGrid(data=new_data, task_id=grid.task_id)

    def flip_horizontal(self, grid: ARCGrid) -> ARCGrid:
        """Flip grid horizontally (left-right)."""
        new_data = np.fliplr(grid.data)
        return ARCGrid(data=new_data, task_id=grid.task_id)

    def flip_vertical(self, grid: ARCGrid) -> ARCGrid:
        """Flip grid vertically (top-bottom)."""
        new_data = np.flipud(grid.data)
        return ARCGrid(data=new_data, task_id=grid.task_id)

    def transpose(self, grid: ARCGrid) -> ARCGrid:
        """Transpose grid (swap rows and columns)."""
        new_data = grid.data.T
        return ARCGrid(data=new_data, task_id=grid.task_id)

    def translate_object(self, obj: ARCObject, dr: int, dc: int) -> ARCObject:
        """Translate object by offset."""
        return obj.translate(dr, dc)

    def rotate_object_90(self, obj: ARCObject, clockwise: bool = True) -> ARCObject:
        """Rotate object 90 degrees around its center."""
        center_r, center_c = obj.center

        new_pixels = set()

        for r, c in obj.pixels:
            # Translate to origin
            r_rel = r - center_r
            c_rel = c - center_c

            # Rotate
            if clockwise:
                r_new = c_rel
                c_new = -r_rel
            else:
                r_new = -c_rel
                c_new = r_rel

            # Translate back
            r_final = int(round(r_new + center_r))
            c_final = int(round(c_new + center_c))

            new_pixels.add((r_final, c_final))

        return ARCObject(pixels=new_pixels, color=obj.color, grid_id=obj.grid_id)

    def flip_object_horizontal(self, obj: ARCObject) -> ARCObject:
        """Flip object horizontally."""
        center_r, center_c = obj.center

        new_pixels = {
            (r, int(round(2 * center_c - c)))
            for r, c in obj.pixels
        }

        return ARCObject(pixels=new_pixels, color=obj.color, grid_id=obj.grid_id)

    def flip_object_vertical(self, obj: ARCObject) -> ARCObject:
        """Flip object vertically."""
        center_r, center_c = obj.center

        new_pixels = {
            (int(round(2 * center_r - r)), c)
            for r, c in obj.pixels
        }

        return ARCObject(pixels=new_pixels, color=obj.color, grid_id=obj.grid_id)

    def scale_object(self, obj: ARCObject, factor: int) -> ARCObject:
        """Scale object by integer factor."""
        if factor <= 0:
            raise ValueError("Scale factor must be positive")

        if factor == 1:
            return obj

        min_r, min_c, max_r, max_c = obj.bounding_box

        new_pixels = set()

        for r, c in obj.pixels:
            # Normalize to 0-based
            r_norm = r - min_r
            c_norm = c - min_c

            # Scale
            for dr in range(factor):
                for dc in range(factor):
                    new_r = min_r + r_norm * factor + dr
                    new_c = min_c + c_norm * factor + dc
                    new_pixels.add((new_r, new_c))

        return ARCObject(pixels=new_pixels, color=obj.color, grid_id=obj.grid_id)

    def get_relative_position(
        self,
        obj1: ARCObject,
        obj2: ARCObject,
    ) -> Dict[str, bool]:
        """Determine relative position between two objects."""
        c1_r, c1_c = obj1.center
        c2_r, c2_c = obj2.center

        return {
            "above": c1_r < c2_r,
            "below": c1_r > c2_r,
            "left": c1_c < c2_c,
            "right": c1_c > c2_c,
            "overlaps": obj1.overlaps(obj2),
        }

    def is_inside(self, inner: ARCObject, outer: ARCObject) -> bool:
        """Check if inner object is completely inside outer object."""
        return inner.pixels.issubset(outer.pixels)

    def is_adjacent(
        self,
        obj1: ARCObject,
        obj2: ARCObject,
        connectivity: int = 4,
    ) -> bool:
        """Check if two objects are adjacent (touching but not overlapping)."""
        if obj1.overlaps(obj2):
            return False

        # Check if any pixel in obj1 is adjacent to any pixel in obj2
        offsets = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        if connectivity == 8:
            offsets.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

        for r1, c1 in obj1.pixels:
            for dr, dc in offsets:
                if (r1 + dr, c1 + dc) in obj2.pixels:
                    return True

        return False

    def detect_symmetry(self, obj: ARCObject) -> Dict[str, bool]:
        """Detect symmetries in object."""
        # Convert to array for analysis
        arr = obj.to_array()

        return {
            "horizontal": np.array_equal(arr, np.flipud(arr)),
            "vertical": np.array_equal(arr, np.fliplr(arr)),
            "diagonal": arr.shape[0] == arr.shape[1] and np.array_equal(arr, arr.T),
            "rotational_180": np.array_equal(arr, np.rot90(arr, k=2)),
        }

    def compute_distance(
        self,
        obj1: ARCObject,
        obj2: ARCObject,
        metric: str = "euclidean",
    ) -> float:
        """Compute distance between two objects."""
        if metric == "euclidean":
            return obj1.distance_to(obj2)
        elif metric == "center":
            c1_r, c1_c = obj1.center
            c2_r, c2_c = obj2.center
            return ((c1_r - c2_r) ** 2 + (c1_c - c2_c) ** 2) ** 0.5
        elif metric == "manhattan":
            c1_r, c1_c = obj1.center
            c2_r, c2_c = obj2.center
            return abs(c1_r - c2_r) + abs(c1_c - c2_c)
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def place_object_on_grid(
        self,
        grid: ARCGrid,
        obj: ARCObject,
        row: int,
        col: int,
    ) -> ARCGrid:
        """Place object on grid at specified position (top-left of bounding box)."""
        new_grid = grid.copy()

        min_r, min_c, _, _ = obj.bounding_box

        for obj_r, obj_c in obj.pixels:
            # Translate to grid coordinates
            grid_r = row + (obj_r - min_r)
            grid_c = col + (obj_c - min_c)

            # Place if in bounds
            if 0 <= grid_r < grid.height and 0 <= grid_c < grid.width:
                new_grid.set(grid_r, grid_c, obj.color)

        return new_grid

    def extract_object_subgrid(self, grid: ARCGrid, obj: ARCObject) -> ARCGrid:
        """Extract minimal grid containing object."""
        min_r, min_c, max_r, max_c = obj.bounding_box

        height = max_r - min_r + 1
        width = max_c - min_c + 1

        return grid.extract_subgrid(min_r, min_c, height, width)
