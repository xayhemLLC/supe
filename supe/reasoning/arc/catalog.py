"""Transformation catalog for ARC tasks.

Provides registry of all available transformations with search and fitting.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from supe.reasoning.arc.grid import ARCGrid
from supe.reasoning.arc.transformation import Transformation, TransformationType

# Import all transformation classes
from supe.reasoning.arc.transformations_geometric import (
    RotateTransformation,
    FlipTransformation,
    TransposeTransformation,
    ScaleTransformation,
    CropTransformation,
    SymmetryCompletionTransformation,
)
from supe.reasoning.arc.transformations_color import (
    ColorMapTransformation,
    ColorSwapTransformation,
    ReplaceColorTransformation,
    InvertColorsTransformation,
    RecolorObjectsTransformation,
    BackgroundSwapTransformation,
)
from supe.reasoning.arc.transformations_structural import (
    DuplicateTransformation,
    CropAndDuplicateTransformation,
    FloodFillTransformation,
    ExtendPatternTransformation,
    HollowOutTransformation,
    FillInteriorTransformation,
    AddBorderTransformation,
    TileTransformation,
    ExtractByMarker,
    CompareGrids,
    ConditionalColor,
)
from supe.reasoning.arc.transformations_priority2 import (
    FillEnclosedRegionsTransformation,
    GravityTransformation,
    ColorRowsTransformation,
    ColorColumnsTransformation,
    SelectTilesTransformation,
)
from supe.reasoning.arc.transformations_objects import (
    ExtractObjectsTransformation,
    TranslateObjectTransformation,
    ApplyPatternToObjectTransformation,
)
from supe.reasoning.arc.transformations_tile_ops import (
    ModifyTileRegionTransformation,
)
from supe.reasoning.arc.transformations_marker_color import (
    ColorRowsByMarkerPositionTransformation,
)
from supe.reasoning.arc.transformations_object_center import (
    CenterObjectsByColorTransformation,
)
from supe.reasoning.arc.transformations_cross_pattern import (
    DrawCrossByAssociationTransformation,
)
from supe.reasoning.arc.transformations_tile_by_marker import (
    TileByMarkerTransformation,
)
from supe.reasoning.arc.transformations_pattern_stamp import (
    StampCrossPatternTransformation,
)
from supe.reasoning.arc.transformations_symmetric_extract import (
    ExtractSymmetricOppositeTransformation,
)
from supe.reasoning.arc.transformations_section_copy import (
    SectionCopyByMarkerTransformation,
)
from supe.reasoning.arc.transformations_parallelogram_align import (
    ParallelogramAlignTransformation,
)


@dataclass
class TransformationMatch:
    """Result of searching for matching transformation."""
    transformation: Transformation
    parameters: Dict
    confidence: float
    explanation: str


class TransformationCatalog:
    """Registry of all available ARC transformations."""

    def __init__(self):
        self.transformations: Dict[str, Transformation] = {}
        self._initialize_catalog()

    def _initialize_catalog(self):
        """Initialize catalog with all transformations."""
        # Geometric transformations
        self.register(RotateTransformation())
        self.register(FlipTransformation())
        self.register(TransposeTransformation())
        self.register(ScaleTransformation())
        self.register(CropTransformation())
        self.register(SymmetryCompletionTransformation())

        # Color transformations
        self.register(ColorMapTransformation())
        self.register(ColorSwapTransformation())
        self.register(ReplaceColorTransformation())
        self.register(InvertColorsTransformation())
        self.register(RecolorObjectsTransformation())
        self.register(BackgroundSwapTransformation())

        # Structural transformations
        self.register(DuplicateTransformation())
        self.register(CropAndDuplicateTransformation())
        self.register(FloodFillTransformation())
        self.register(ExtendPatternTransformation())
        self.register(HollowOutTransformation())
        self.register(FillInteriorTransformation())
        self.register(AddBorderTransformation())
        self.register(TileTransformation())
        self.register(ExtractByMarker())
        self.register(CompareGrids())
        self.register(ConditionalColor())

        # Priority 2 transformations
        self.register(FillEnclosedRegionsTransformation())
        self.register(GravityTransformation())
        self.register(ColorRowsTransformation())
        self.register(ColorColumnsTransformation())
        self.register(SelectTilesTransformation())

        # Priority 3a: Object operations
        self.register(ExtractObjectsTransformation())
        self.register(TranslateObjectTransformation())
        self.register(ApplyPatternToObjectTransformation())

        # Priority 3b: Tile operations
        self.register(ModifyTileRegionTransformation())

        # Priority 3c: Marker-based coloring
        self.register(ColorRowsByMarkerPositionTransformation())

        # Priority 3d: Object centering
        self.register(CenterObjectsByColorTransformation())

        # Priority 3e: Cross pattern drawing
        self.register(DrawCrossByAssociationTransformation())

        # Priority 3f: Tile by marker
        self.register(TileByMarkerTransformation())

        # Priority 3g: Pattern stamping
        self.register(StampCrossPatternTransformation())

        # Priority 3h: Symmetric extraction
        self.register(ExtractSymmetricOppositeTransformation())

        # Priority 3i: Section copy by marker
        self.register(SectionCopyByMarkerTransformation())

        # Priority 3j: Parallelogram alignment
        self.register(ParallelogramAlignTransformation())

    def register(self, transformation: Transformation):
        """Register a transformation in the catalog."""
        self.transformations[transformation.name] = transformation

    def get(self, name: str) -> Optional[Transformation]:
        """Get transformation by name."""
        return self.transformations.get(name)

    def list_transformations(
        self,
        transformation_type: Optional[TransformationType] = None
    ) -> List[Transformation]:
        """List all transformations, optionally filtered by type."""
        transforms = list(self.transformations.values())

        if transformation_type:
            transforms = [
                t for t in transforms
                if t.transformation_type == transformation_type
            ]

        return transforms

    def find_transformation(
        self,
        examples: List[Tuple[ARCGrid, ARCGrid]],
        candidate_names: Optional[List[str]] = None,
        max_results: int = 5,
    ) -> List[TransformationMatch]:
        """Find transformation(s) that match the examples.

        Args:
            examples: List of (input, output) grid pairs
            candidate_names: Optional list of transformation names to try
            max_results: Maximum number of results to return

        Returns:
            List of TransformationMatch objects, sorted by confidence
        """
        if not examples:
            return []

        # Determine which transformations to try
        if candidate_names:
            candidates = [self.get(name) for name in candidate_names if self.get(name)]
        else:
            candidates = list(self.transformations.values())

        matches = []

        for transform in candidates:
            # Try to fit parameters
            params = transform.fit_parameters(examples)

            if params is not None:
                # Verify on all examples
                correct = 0
                for input_grid, output_grid in examples:
                    if transform.verify(input_grid, output_grid, **params):
                        correct += 1

                confidence = correct / len(examples)

                if confidence > 0.5:  # Only include if >50% match
                    matches.append(TransformationMatch(
                        transformation=transform,
                        parameters=params,
                        confidence=confidence,
                        explanation=transform.explain(params),
                    ))

        # Sort by confidence
        matches.sort(key=lambda m: m.confidence, reverse=True)

        return matches[:max_results]

    def infer_transformation(
        self,
        input_grid: ARCGrid,
        output_grid: ARCGrid,
    ) -> Optional[TransformationMatch]:
        """Infer transformation from single input-output pair.

        This is a convenience wrapper around find_transformation for single examples.

        Args:
            input_grid: Input grid
            output_grid: Output grid

        Returns:
            Best matching transformation, or None
        """
        matches = self.find_transformation([(input_grid, output_grid)], max_results=1)
        return matches[0] if matches else None

    def suggest_transformations(
        self,
        input_grid: ARCGrid,
        output_grid: ARCGrid,
    ) -> List[TransformationMatch]:
        """Suggest possible transformations based on input-output characteristics.

        Uses heuristics to narrow down likely transformations before fitting.

        Args:
            input_grid: Input grid
            output_grid: Output grid

        Returns:
            List of suggested transformations
        """
        candidates = []

        # Shape analysis
        if input_grid.shape != output_grid.shape:
            # Geometric transformations that change shape
            if output_grid.height == input_grid.width and output_grid.width == input_grid.height:
                candidates.extend(["rotate", "transpose"])

            if output_grid.height > input_grid.height or output_grid.width > input_grid.width:
                candidates.extend(["scale", "duplicate", "extend_pattern", "add_border"])

            if output_grid.height < input_grid.height or output_grid.width < input_grid.width:
                candidates.append("crop")

        else:
            # Same shape - could be many transformations
            # Check color changes
            input_colors = input_grid.get_unique_colors()
            output_colors = output_grid.get_unique_colors()

            if input_colors != output_colors:
                # Color transformation likely
                candidates.extend([
                    "color_map", "color_swap", "replace_color",
                    "recolor_objects", "background_swap"
                ])

            # Check if rotation/flip (same shape, same colors)
            if input_colors == output_colors:
                candidates.extend(["rotate", "flip", "transpose"])

            # Check structural changes
            input_bg = input_grid.get_background_color()
            output_bg = output_grid.get_background_color()

            input_fg_count = input_grid.count_color(input_bg)
            output_fg_count = output_grid.count_color(output_bg)

            if output_fg_count > input_fg_count:
                # More foreground - filling operations
                candidates.extend(["flood_fill", "fill_interior", "complete_symmetry"])
            elif output_fg_count < input_fg_count:
                # Less foreground - hollowing operations
                candidates.append("hollow_out")

        # Use heuristics to find matches
        return self.find_transformation(
            [(input_grid, output_grid)],
            candidate_names=candidates if candidates else None,
            max_results=10
        )

    def get_statistics(self) -> Dict:
        """Get catalog statistics."""
        total = len(self.transformations)

        by_type = {}
        for transform in self.transformations.values():
            t_type = transform.transformation_type.value
            by_type[t_type] = by_type.get(t_type, 0) + 1

        return {
            "total_transformations": total,
            "by_type": by_type,
            "transformation_names": list(self.transformations.keys()),
        }

    def __repr__(self):
        stats = self.get_statistics()
        return f"TransformationCatalog(total={stats['total_transformations']}, by_type={stats['by_type']})"


# Global catalog instance
_global_catalog = None


def get_catalog() -> TransformationCatalog:
    """Get or create global transformation catalog."""
    global _global_catalog
    if _global_catalog is None:
        _global_catalog = TransformationCatalog()
    return _global_catalog
