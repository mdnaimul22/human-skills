import math

import numpy as np
from manim import *


class PolygonTransformationTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "original",     # Polygon on coordinate plane, vertices labeled
        "translated",   # Polygon moved by translation vector, both shown
        "reflected",    # Polygon reflected over axis or line, both shown
        "rotated",      # Polygon rotated by angle about center, both shown
        "dilated",      # Polygon scaled from center by factor, both shown
    })

    REFLECTION_AXES = frozenset({"x", "y", "y=x", "y=-x"})

    def __init__(
        self,
        state: str,
        vertices: list[tuple[float, float]],
        *,
        translation_vector: tuple[float, float] = (2, 1),
        reflection_axis: str = "x",
        rotation_angle: float = 90,
        rotation_center: tuple[float, float] = (0, 0),
        dilation_factor: float = 2.0,
        dilation_center: tuple[float, float] = (0, 0),
        x_range: tuple = (-6, 6, 1),
        y_range: tuple = (-4, 4, 1),
        labels: bool = True,
    ):
        state = self._validate_state(state)
        verts_np = self._validate_vertices(vertices)
        if reflection_axis not in self.REFLECTION_AXES:
            raise ValueError(f"reflection_axis must be one of: {', '.join(sorted(self.REFLECTION_AXES))}")

        self.axes = Axes(
            x_range=list(x_range),
            y_range=list(y_range),
            x_length=6.4,
            y_length=4.8,
            tips=False,
            axis_config={"color": GREY_B, "stroke_width": 2},
        )
        axis_labels = self.axes.get_axis_labels(
            MathTex("x", font_size=22),
            MathTex("y", font_size=22),
        )
        axes_group = VGroup(self.axes, axis_labels)

        original_poly = self._build_polygon(verts_np, TEAL_B)
        original_labels = self._vertex_labels(verts_np, TEAL_B) if labels else VGroup(VectorizedPoint(ORIGIN))

        transformed_verts = self._transform_vertices(
            state, verts_np,
            translation_vector=translation_vector,
            reflection_axis=reflection_axis,
            rotation_angle=rotation_angle,
            rotation_center=rotation_center,
            dilation_factor=dilation_factor,
            dilation_center=dilation_center,
        )
        transformed_poly = self._build_polygon(transformed_verts, YELLOW)
        transformed_labels = self._vertex_labels(transformed_verts, YELLOW, prime=True) if labels else VGroup(VectorizedPoint(ORIGIN))

        annotation = (
            self._reflection_axis_line(reflection_axis)
            if state == "reflected"
            else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        )

        self.original_poly = original_poly
        self.original_labels = original_labels
        self.transformed_poly = transformed_poly
        self.transformed_labels = transformed_labels
        self.annotation = annotation

        boundary = Rectangle(
            width=self.axes.width + 1.4,
            height=self.axes.height + 0.8,
        ).move_to(self.axes).set_opacity(0)

        super().__init__(axes_group, original_poly, original_labels, annotation, boundary, state=state)

    def translate(self) -> Animation:
        return self._transform_action("translated")

    def reflect(self) -> Animation:
        return self._transform_action("reflected")

    def rotate(self) -> Animation:
        return self._transform_action("rotated")

    def dilate(self) -> Animation:
        return self._transform_action("dilated")

    def _transform_action(self, expected_state: str) -> Animation:
        if self.state != expected_state:
            raise ValueError(f"this action is only available in {expected_state} state")
        return AnimationGroup(
            Transform(self.original_poly, self.transformed_poly),
            Transform(self.original_labels, self.transformed_labels),
        )

    @staticmethod
    def _validate_vertices(vertices: list[tuple[float, float]]) -> list[np.ndarray]:
        if len(vertices) < 3:
            raise ValueError("vertices must contain at least three points")

        verts = []
        for vertex in vertices:
            if len(vertex) != 2:
                raise ValueError("each vertex must be an (x, y) pair")
            x, y = float(vertex[0]), float(vertex[1])
            if not np.isfinite(x) or not np.isfinite(y):
                raise ValueError("vertices must contain finite numeric coordinates")
            verts.append(np.array([x, y, 0.0]))

        unique_points = {(float(v[0]), float(v[1])) for v in verts}
        if len(unique_points) < 3:
            raise ValueError("vertices must contain at least three distinct points")

        area_twice = 0.0
        for current, following in zip(verts, verts[1:] + verts[:1]):
            area_twice += current[0] * following[1] - following[0] * current[1]
        if abs(area_twice) < 1e-9:
            raise ValueError("vertices must form a non-degenerate polygon")

        return verts

    def _build_polygon(self, verts: list, color: ManimColor) -> VGroup:
        screen_pts = [self.axes.c2p(v[0], v[1]) for v in verts]
        poly = Polygon(*screen_pts, stroke_color=color, stroke_width=3, fill_color=color, fill_opacity=0.25)
        return VGroup(poly)

    def _vertex_labels(self, verts: list, color: ManimColor, prime: bool = False) -> VGroup:
        letters = "ABCDEFGH"
        center = sum(verts) / len(verts)
        labels = []
        for i, v in enumerate(verts):
            letter = letters[i % len(letters)]
            tex = letter + ("'" if prime else "")
            outward = v - center
            norm = np.linalg.norm(outward)
            direction = outward / norm if norm > 1e-9 else np.array([0.0, 1.0, 0.0])
            pos = self.axes.c2p(v[0], v[1]) + direction * 0.35
            label = MathTex(tex, font_size=24, color=color).move_to(pos)
            labels.append(label)
        return VGroup(*labels)

    def _reflection_axis_line(self, axis: str) -> VGroup:
        ax = self.axes
        if axis == "x":
            return VGroup(DashedLine(ax.c2p(-6, 0), ax.c2p(6, 0), color=GREY_B, stroke_width=2))
        if axis == "y":
            return VGroup(DashedLine(ax.c2p(0, -4), ax.c2p(0, 4), color=GREY_B, stroke_width=2))
        if axis == "y=x":
            return VGroup(DashedLine(ax.c2p(-4, -4), ax.c2p(4, 4), color=GREY_B, stroke_width=2))
        return VGroup(DashedLine(ax.c2p(-4, 4), ax.c2p(4, -4), color=GREY_B, stroke_width=2))

    @staticmethod
    def _transform_vertices(
        state: str,
        verts: list,
        *,
        translation_vector,
        reflection_axis,
        rotation_angle,
        rotation_center,
        dilation_factor,
        dilation_center,
    ) -> list:
        if state == "original":
            return verts
        if state == "translated":
            tx, ty = translation_vector
            return [v + np.array([tx, ty, 0.0]) for v in verts]
        if state == "reflected":
            return [PolygonTransformationTemplate._reflect(v, reflection_axis) for v in verts]
        if state == "rotated":
            cx, cy = rotation_center
            center = np.array([cx, cy, 0.0])
            angle_rad = math.radians(rotation_angle)
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
            result = []
            for v in verts:
                d = v - center
                rx = cos_a * d[0] - sin_a * d[1]
                ry = sin_a * d[0] + cos_a * d[1]
                result.append(center + np.array([rx, ry, 0.0]))
            return result
        if state == "dilated":
            cx, cy = dilation_center
            center = np.array([cx, cy, 0.0])
            return [center + (v - center) * dilation_factor for v in verts]
        return verts

    @staticmethod
    def _reflect(v: np.ndarray, axis: str) -> np.ndarray:
        x, y = v[0], v[1]
        if axis == "x":
            return np.array([x, -y, 0.0])
        if axis == "y":
            return np.array([-x, y, 0.0])
        if axis == "y=x":
            return np.array([y, x, 0.0])
        return np.array([-y, -x, 0.0])
