import math

import numpy as np
from manim import *


class CircleTheoremsTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "radius_tangent",   # Radius to tangent point, 90° angle marked
        "chord",            # Chord with perpendicular bisector from center
        "secant",           # Two secants from external point with arc labels
        "arc_central",      # Arc with central angle labeled
        "inscribed_angle",  # Inscribed angle and arc span relationship
    })

    def __init__(
        self,
        state: str,
        *,
        radius: float = 2.0,
        center: tuple[float, float] = (0, 0),
        chord_angle: float = 60,
        secant_point: tuple[float, float] = (4, 0),
        arc_start_angle: float = 30,
        arc_end_angle: float = 150,
        inscribed_vertex_angle: float = 200,
        labels: bool = True,
    ):
        state = self._validate_state(state)
        if radius <= 0:
            raise ValueError("radius must be positive")

        self._radius = radius
        self._center = np.array([center[0], center[1], 0.0])
        self._chord_angle = chord_angle
        self._secant_point = np.array([secant_point[0], secant_point[1], 0.0])
        self._arc_start = arc_start_angle
        self._arc_end = arc_end_angle
        self._inscribed_vertex_angle = inscribed_vertex_angle
        self._labels = labels

        main_circle = Circle(radius=radius, color=WHITE, stroke_width=3).move_to(self._center)

        center_dot = Dot(self._center, radius=0.06, color=WHITE)
        center_label = MathTex("O", font_size=24, color=WHITE).next_to(center_dot, DL, buff=0.08) if labels else VGroup(VectorizedPoint(self._center))

        state_groups = {
            name: VGroup(VectorizedPoint(self._center))
            for name in self.VALID_STATES
        }
        state_groups[state] = self._build_state_content(state)

        boundary = Rectangle(
            width=max(main_circle.width + 1.6, 6.0),
            height=max(main_circle.height + 1.6, 5.0),
        ).move_to(self._center).set_opacity(0)

        self._state_groups = state_groups
        self._content = state_groups[state]

        super().__init__(
            main_circle,
            center_dot,
            center_label,
            *state_groups.values(),
            boundary,
            state=state,
        )

    def show_radius_tangent(self) -> Animation:
        return self._show_current_theorem({"radius_tangent"})

    def show_perpendicular_bisector(self) -> Animation:
        return self._show_current_theorem({"chord"})

    def show_arc_angle(self) -> Animation:
        return self._show_current_theorem({"secant", "arc_central"})

    def show_inscribed_relationship(self) -> Animation:
        return self._show_current_theorem({"inscribed_angle"})

    def _show_current_theorem(self, valid_states: set[str]) -> Animation:
        if self.state not in valid_states:
            expected = ", ".join(sorted(valid_states))
            raise ValueError(f"the theorem action requires state: {expected}")
        return Indicate(self._state_groups[self.state], scale_factor=1.02)

    def _build_state_content(self, state: str) -> VGroup:
        if state == "radius_tangent":
            return self._radius_tangent_content()
        if state == "chord":
            return self._chord_content()
        if state == "secant":
            return self._secant_content()
        if state == "arc_central":
            return self._arc_central_content()
        return self._inscribed_angle_content()

    def _point_on_circle(self, angle_deg: float) -> np.ndarray:
        rad = math.radians(angle_deg)
        return self._center + np.array([self._radius * math.cos(rad), self._radius * math.sin(rad), 0.0])

    def _radius_tangent_content(self) -> VGroup:
        tangent_angle_deg = 0
        tangent_pt = self._point_on_circle(tangent_angle_deg)
        radius_line = Line(self._center, tangent_pt, color=YELLOW, stroke_width=3)

        tangent_dir = np.array([0.0, 1.0, 0.0])
        tangent_line = Line(
            tangent_pt - tangent_dir * self._radius,
            tangent_pt + tangent_dir * self._radius,
            color=TEAL_B,
            stroke_width=3,
        )
        right_angle = RightAngle(
            Line(tangent_pt, self._center),
            Line(tangent_pt, tangent_pt + tangent_dir),
            length=0.22,
            color=ORANGE,
        )
        parts = [radius_line, tangent_line, right_angle]
        if self._labels:
            r_label = MathTex("r", font_size=24, color=YELLOW).move_to(
                (self._center + tangent_pt) / 2 + UP * 0.2
            )
            angle_label = MathTex(r"90^\circ", font_size=22, color=ORANGE).next_to(right_angle, UL, buff=0.05)
            parts += [r_label, angle_label]
        return VGroup(*parts)

    def _chord_content(self) -> VGroup:
        half = self._chord_angle / 2
        pt1 = self._point_on_circle(90 + half)
        pt2 = self._point_on_circle(90 - half)
        chord = Line(pt1, pt2, color=TEAL_B, stroke_width=3)
        mid = (pt1 + pt2) / 2
        bisector = Line(self._center, mid, color=YELLOW, stroke_width=3)
        right_angle = RightAngle(
            Line(mid, pt1),
            Line(mid, self._center),
            length=0.2,
            color=ORANGE,
        )
        parts = [chord, bisector, right_angle]
        if self._labels:
            dot1 = Dot(pt1, radius=0.06, color=TEAL_B)
            dot2 = Dot(pt2, radius=0.06, color=TEAL_B)
            mid_dot = Dot(mid, radius=0.06, color=YELLOW)
            parts += [dot1, dot2, mid_dot]
        return VGroup(*parts)

    def _secant_content(self) -> VGroup:
        ext = self._secant_point
        if np.linalg.norm(ext - self._center) <= self._radius:
            raise ValueError("secant_point must be outside the circle")

        center_direction = math.degrees(math.atan2(
            self._center[1] - ext[1],
            self._center[0] - ext[0],
        ))
        distance_to_center = float(np.linalg.norm(ext - self._center))
        angular_radius = math.degrees(math.asin(self._radius / distance_to_center))
        secant_offset = max(1.0, angular_radius * 0.55)
        p1_near, p1_far = self._secant_ray_points(center_direction - secant_offset)
        p2_near, p2_far = self._secant_ray_points(center_direction + secant_offset)

        sec1 = Line(ext, p1_far, color=TEAL_B, stroke_width=3)
        sec2 = Line(ext, p2_far, color=ORANGE, stroke_width=3)
        arc1 = self._arc_between_points(p1_far, p2_far, TEAL_B)
        arc2 = self._arc_between_points(p1_near, p2_near, ORANGE)

        parts = [sec1, sec2, arc1, arc2]
        if self._labels:
            ext_dot = Dot(ext, radius=0.07, color=WHITE)
            ext_label = MathTex("P", font_size=24, color=WHITE).next_to(ext_dot, RIGHT, buff=0.1)
            near_dots = VGroup(
                Dot(p1_near, radius=0.055, color=TEAL_B),
                Dot(p2_near, radius=0.055, color=ORANGE),
            )
            far_dots = VGroup(
                Dot(p1_far, radius=0.055, color=TEAL_B),
                Dot(p2_far, radius=0.055, color=ORANGE),
            )
            parts += [ext_dot, ext_label, near_dots, far_dots]
        return VGroup(*parts)

    def _secant_ray_points(self, direction_angle_deg: float) -> tuple[np.ndarray, np.ndarray]:
        direction = np.array([
            math.cos(math.radians(direction_angle_deg)),
            math.sin(math.radians(direction_angle_deg)),
            0.0,
        ])
        offset = self._secant_point - self._center
        b = 2 * float(np.dot(offset, direction))
        c = float(np.dot(offset, offset) - self._radius**2)
        discriminant = b * b - 4 * c
        if discriminant <= 1e-9:
            raise ValueError("secant ray must cross the circle in two distinct points")
        root = math.sqrt(discriminant)
        t1 = (-b - root) / 2
        t2 = (-b + root) / 2
        positive = sorted(t for t in (t1, t2) if t > 1e-9)
        if len(positive) != 2:
            raise ValueError("secant ray must point from the external point through the circle")
        near = self._secant_point + positive[0] * direction
        far = self._secant_point + positive[1] * direction
        return near, far

    def _arc_between_points(
        self,
        start_point: np.ndarray,
        end_point: np.ndarray,
        color: ManimColor,
    ) -> Arc:
        start_angle = math.atan2(
            start_point[1] - self._center[1],
            start_point[0] - self._center[0],
        )
        end_angle = math.atan2(
            end_point[1] - self._center[1],
            end_point[0] - self._center[0],
        )
        span = end_angle - start_angle
        while span <= -math.pi:
            span += 2 * math.pi
        while span > math.pi:
            span -= 2 * math.pi
        return Arc(
            radius=self._radius,
            start_angle=start_angle,
            angle=span,
            color=color,
            stroke_width=5,
        ).move_arc_center_to(self._center)

    def _arc_central_content(self) -> VGroup:
        start_rad = math.radians(self._arc_start)
        end_rad = math.radians(self._arc_end)
        span_rad = end_rad - start_rad

        arc = Arc(
            radius=self._radius,
            start_angle=start_rad,
            angle=span_rad,
            color=YELLOW,
            stroke_width=5,
        ).move_arc_center_to(self._center)

        pt_start = self._point_on_circle(self._arc_start)
        pt_end = self._point_on_circle(self._arc_end)
        radius1 = Line(self._center, pt_start, color=TEAL_B, stroke_width=3)
        radius2 = Line(self._center, pt_end, color=TEAL_B, stroke_width=3)

        central_angle_arc = Angle(
            Line(self._center, pt_start),
            Line(self._center, pt_end),
            radius=0.45,
            color=ORANGE,
        )

        return VGroup(arc, radius1, radius2, central_angle_arc)

    def _inscribed_angle_content(self) -> VGroup:
        vertex_pt = self._point_on_circle(self._inscribed_vertex_angle)
        intercept_start_pt = self._point_on_circle(self._arc_start)
        intercept_end_pt = self._point_on_circle(self._arc_end)

        leg1 = Line(vertex_pt, intercept_start_pt, color=YELLOW, stroke_width=3)
        leg2 = Line(vertex_pt, intercept_end_pt, color=YELLOW, stroke_width=3)

        span_rad = math.radians(self._arc_end - self._arc_start)
        intercepted_arc = Arc(
            radius=self._radius,
            start_angle=math.radians(self._arc_start),
            angle=span_rad,
            color=ORANGE,
            stroke_width=5,
        ).move_arc_center_to(self._center)

        inscribed_angle_deg = (self._arc_end - self._arc_start) / 2
        parts = [leg1, leg2, intercepted_arc]
        if self._labels:
            v_dot = Dot(vertex_pt, radius=0.07, color=YELLOW)
            inscribed_label = MathTex(rf"\angle={inscribed_angle_deg:g}^\circ", font_size=22, color=YELLOW)
            inscribed_label.move_to(
                vertex_pt + self._outward_direction(self._inscribed_vertex_angle) * 0.72
            )
            parts += [v_dot, inscribed_label]
        return VGroup(*parts)

    def _outward_direction(self, angle_deg: float) -> np.ndarray:
        rad = math.radians(angle_deg)
        return np.array([math.cos(rad), math.sin(rad), 0.0])
