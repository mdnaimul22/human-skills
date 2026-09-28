import builtins
from .visual_kit import VisualTemplate, SafeScene, Layout

builtins.VisualTemplate = VisualTemplate
builtins.SafeScene = SafeScene
builtins.Layout = Layout

from .circle_theorems_template import CircleTheoremsTemplate
from .equation_template import EquationTemplate
from .fraction_model_template import FractionModelTemplate
from .function_graph_template import FunctionGraphTemplate
from .function_translation_template import FunctionTranslationTemplate
from .line_geometry_template import LineGeometryTemplate
from .linear_transformation_template import LinearTransformationTemplate
from .matrix_template import MatrixTemplate
from .number_line_template import NumberLineTemplate
from .polygon_transformation_template import PolygonTransformationTemplate
from .pythagorean_area_template import PythagoreanAreaTemplate
from .triangle_template import TriangleTemplate
from .unit_circle_template import UnitCircleTemplate
from .vector_template import VectorTemplate

__all__ = [
    "VisualTemplate",
    "SafeScene",
    "Layout",
    "CircleTheoremsTemplate",
    "EquationTemplate",
    "FractionModelTemplate",
    "FunctionGraphTemplate",
    "FunctionTranslationTemplate",
    "LineGeometryTemplate",
    "LinearTransformationTemplate",
    "MatrixTemplate",
    "NumberLineTemplate",
    "PolygonTransformationTemplate",
    "PythagoreanAreaTemplate",
    "TriangleTemplate",
    "UnitCircleTemplate",
    "VectorTemplate",
]
