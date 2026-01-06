"""Object detection for ARC grids using connected components."""

from typing import List, Set, Tuple, Optional
import numpy as np
from collections import deque

from supe.reasoning.arc.grid import ARCGrid, ARCObject


class ObjectDetector:
    """Detect objects in ARC grids via connected component analysis."""

    def detect_objects(
        self,
        grid: ARCGrid,
        background_color: Optional[int] = None,
        connectivity: int = 4,
        min_size: int = 1,
    ) -> List[ARCObject]:
        """Detect all objects in grid.

        Args:
            grid: ARC grid to analyze
            background_color: Color to treat as background (auto-detect if None)
            connectivity: 4 (orthogonal) or 8 (includes diagonal)
            min_size: Minimum number of pixels for an object

        Returns:
            List of detected objects
        """
        if background_color is None:
            background_color = grid.get_background_color()

        # Find all non-background positions
        non_background = set()
        for r in range(grid.height):
            for c in range(grid.width):
                if grid.get(r, c) != background_color:
                    non_background.add((r, c))

        # Group by connected components
        visited = set()
        objects = []

        for pos in non_background:
            if pos in visited:
                continue

            # BFS to find connected component
            component = self._find_connected_component(
                grid, pos, visited, connectivity
            )

            if len(component) >= min_size:
                color = grid.get(pos[0], pos[1])
                objects.append(ARCObject(
                    pixels=component,
                    color=color,
                    grid_id=grid.task_id,
                ))

        return objects

    def _find_connected_component(
        self,
        grid: ARCGrid,
        start: Tuple[int, int],
        visited: Set[Tuple[int, int]],
        connectivity: int,
    ) -> Set[Tuple[int, int]]:
        """Find connected component starting from position using BFS."""
        component = set()
        queue = deque([start])
        start_color = grid.get(start[0], start[1])

        while queue:
            r, c = queue.popleft()

            if (r, c) in visited:
                continue

            if grid.get(r, c) != start_color:
                continue

            visited.add((r, c))
            component.add((r, c))

            # Add neighbors
            for dr, dc in self._get_neighbor_offsets(connectivity):
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    if (nr, nc) not in visited:
                        queue.append((nr, nc))

        return component

    def _get_neighbor_offsets(self, connectivity: int) -> List[Tuple[int, int]]:
        """Get neighbor offsets for given connectivity."""
        if connectivity == 4:
            # Orthogonal only
            return [(-1, 0), (1, 0), (0, -1), (0, 1)]
        elif connectivity == 8:
            # Orthogonal + diagonal
            return [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1),
            ]
        else:
            raise ValueError(f"Connectivity must be 4 or 8, got {connectivity}")

    def detect_objects_by_color(
        self,
        grid: ARCGrid,
        color: int,
        connectivity: int = 4,
        min_size: int = 1,
    ) -> List[ARCObject]:
        """Detect objects of specific color."""
        # Treat all other colors as background
        objects = []

        # Find all positions with this color
        positions = grid.find_color_positions(color)

        visited = set()

        for pos in positions:
            if pos in visited:
                continue

            # Find connected component of this color
            component = self._find_connected_component_color(
                grid, pos, color, visited, connectivity
            )

            if len(component) >= min_size:
                objects.append(ARCObject(
                    pixels=component,
                    color=color,
                    grid_id=grid.task_id,
                ))

        return objects

    def _find_connected_component_color(
        self,
        grid: ARCGrid,
        start: Tuple[int, int],
        target_color: int,
        visited: Set[Tuple[int, int]],
        connectivity: int,
    ) -> Set[Tuple[int, int]]:
        """Find connected component of specific color."""
        component = set()
        queue = deque([start])

        while queue:
            r, c = queue.popleft()

            if (r, c) in visited:
                continue

            if grid.get(r, c) != target_color:
                continue

            visited.add((r, c))
            component.add((r, c))

            # Add neighbors
            for dr, dc in self._get_neighbor_offsets(connectivity):
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid.height and 0 <= nc < grid.width:
                    if (nr, nc) not in visited:
                        queue.append((nr, nc))

        return component

    def largest_object(self, objects: List[ARCObject]) -> Optional[ARCObject]:
        """Get largest object by pixel count."""
        if not objects:
            return None
        return max(objects, key=lambda obj: obj.mass)

    def smallest_object(self, objects: List[ARCObject]) -> Optional[ARCObject]:
        """Get smallest object by pixel count."""
        if not objects:
            return None
        return min(objects, key=lambda obj: obj.mass)

    def filter_by_size(
        self,
        objects: List[ARCObject],
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
    ) -> List[ARCObject]:
        """Filter objects by size range."""
        filtered = objects

        if min_size is not None:
            filtered = [obj for obj in filtered if obj.mass >= min_size]

        if max_size is not None:
            filtered = [obj for obj in filtered if obj.mass <= max_size]

        return filtered

    def filter_by_color(self, objects: List[ARCObject], color: int) -> List[ARCObject]:
        """Filter objects by color."""
        return [obj for obj in objects if obj.color == color]

    def group_by_color(self, objects: List[ARCObject]) -> dict:
        """Group objects by color."""
        groups = {}
        for obj in objects:
            if obj.color not in groups:
                groups[obj.color] = []
            groups[obj.color].append(obj)
        return groups
