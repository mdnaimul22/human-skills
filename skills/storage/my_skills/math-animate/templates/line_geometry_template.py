import numpy as np
from manim import *


class LineGeometryTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "point_plot",       # One or two labeled coordinate points on axes
        "slope_rise_run",   # Rise-over-run triangle between two points
        "midpoint",         # Midpoint marker between two points
        "distance",         # Geometric distance segment between two points
        "line_equation",    # Full line drawn on the coordinate axes
        "intercepts",       # x- and y-intercept markers labeled
        "intersection",     # Two lines crossing with solution point labeled
    })

    def __init__(
        self,
        state: str,
        point_a: tuple[float, float],
        point_b: tuple[float, float] | None = None,
        *,
        slope: float | None = None,
        y_intercept: float | None = None,
        line2_slope: float | None = None,
        line2_y_intercept: float | None = None,
        x_range: tuple = (-6, 6, 1),
        y_range: tuple = (-4, 4, 1),
        labels: bool = True,
    ):
        state = self._validate_state(state)
        if state in {"slope_rise_run", "midpoint", "distance"} and point_b is None:
            raise ValueError(f"{state} requires point_b")
        if state == "intersection" and (
            line2_slope is None or line2_y_intercept is None
        ):
            raise ValueError("intersection requires line2_slope and line2_y_intercept")

        slope, y_intercept, vertical_x = self._resolve_line(
            point_a,
            point_b,
            slope,
            y_intercept,
        )

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

        self._slope = slope
        self._y_intercept = y_intercept
        self._vertical_x = vertical_x
        self._point_a = np.array([point_a[0], point_a[1], 0.0])
        self._point_b = np.array([point_b[0], point_b[1], 0.0]) if point_b is not None else None
        self._labels = labels

        point_a_dot, point_a_label = self._labeled_dot(point_a, YELLOW)
        point_b_dot, point_b_label = (
            self._labeled_dot(point_b, TEAL_B)
            if point_b is not None
            else (VGroup(VectorizedPoint(self.axes.c2p(0, 0))),
                  VGroup(VectorizedPoint(self.axes.c2p(0, 0))))
        )
        points_group = VGroup(point_a_dot, point_a_label, point_b_dot, point_b_label)

        line_graph = self._build_line(
            slope,
            y_intercept,
            x_range,
            y_range,
            color=YELLOW,
            vertical_x=vertical_x,
        )
        rise_run_triangle = self._rise_run_triangle(point_a, point_b) if point_b is not None else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        midpoint_marker = self._midpoint_marker(point_a, point_b) if point_b is not None else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        distance_visual = self._distance_visual(point_a, point_b) if point_b is not None else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        intercept_markers = self._intercept_markers(
            slope,
            y_intercept,
            x_range,
            y_range,
            vertical_x=vertical_x,
        )

        line2_group = VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        intersection_marker = VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        if state == "intersection":
            line2_group = self._build_line(
                line2_slope,
                line2_y_intercept,
                x_range,
                y_range,
                color=TEAL_B,
            )
            sol = self._solve_intersection(
                slope,
                y_intercept,
                line2_slope,
                line2_y_intercept,
                vertical_x=vertical_x,
            )
            if sol is not None:
                intersection_marker = self._labeled_intersection(sol)

        self._apply_state_visibility(
            state,
            points_group=points_group,
            line_graph=line_graph,
            rise_run_triangle=rise_run_triangle,
            midpoint_marker=midpoint_marker,
            distance_visual=distance_visual,
            intercept_markers=intercept_markers,
            line2_group=line2_group,
            intersection_marker=intersection_marker,
        )

        boundary = Rectangle(
            width=self.axes.width + 1.4,
            height=self.axes.height + 0.8,
        ).move_to(self.axes).set_opacity(0)

        self.rise_run_triangle = rise_run_triangle
        self.midpoint_marker = midpoint_marker
        self.distance_visual = distance_visual
        self.intercept_markers = intercept_markers
        self.intersection_marker = intersection_marker
        self.line_graph = line_graph

        super().__init__(
            axes_group,
            points_group,
            line_graph,
            rise_run_triangle,
            midpoint_marker,
            distance_visual,
            intercept_markers,
            line2_group,
            intersection_marker,
            boundary,
            state=state,
        )

    def show_slope_triangle(self) -> Animation:
        return Indicate(self.rise_run_triangle, color=ORANGE, scale_factor=1.05)

    def show_midpoint(self) -> Animation:
        return Indicate(self.midpoint_marker, color=YELLOW, scale_factor=1.1)

    def show_distance(self) -> Animation:
        return Indicate(self.distance_visual, color=GREEN_B, scale_factor=1.05)

    def show_intercepts(self) -> Animation:
        return Indicate(self.intercept_markers, color=YELLOW, scale_factor=1.1)

    def show_intersection(self) -> Animation:
        return Indicate(self.intersection_marker, color=YELLOW, scale_factor=1.1)

    def _apply_state_visibility(self, state, **groups):
        visible = {
            "point_plot": {"points_group"},
            "slope_rise_run": {"points_group", "line_graph", "rise_run_triangle"},
            "midpoint": {"points_group", "line_graph", "midpoint_marker"},
            "distance": {"points_group", "distance_visual"},
            "line_equation": {"line_graph"},
            "intercepts": {"line_graph", "intercept_markers"},
            "intersection": {"line_graph", "line2_group", "intersection_marker"},
        }[state]
        for name, group in groups.items():
            if name not in visible:
                group.set_opacity(0)

    def _labeled_dot(self, point: tuple[float, float], color: ManimColor):
        x, y = point
        dot = Dot(self.axes.c2p(x, y), radius=0.07, color=color)
        label = MathTex(rf"({x:g},\,{y:g})", font_size=24, color=color).next_to(dot, UR, buff=0.08)
        return VGroup(dot), VGroup(label)

    def _labeled_intersection(self, point: tuple[float, float]):
        x, y = point
        dot = Dot(self.axes.c2p(x, y), radius=0.09, color=RED)
        label = MathTex(rf"({x:g},\,{y:g})", font_size=24, color=RED).next_to(dot, UR, buff=0.09)
        return VGroup(dot, label)

    def _build_line(
        self,
        slope: float | None,
        y_intercept: float | None,
        x_range: tuple,
        y_range: tuple,
        color: ManimColor,
        *,
        vertical_x: float | None = None,
    ) -> VGroup:
        x_min, x_max = self._inset_axis_range(x_range)
        y_min, y_max = self._inset_axis_range(y_range)
        if vertical_x is not None:
            if not x_min <= vertical_x <= x_max:
                raise ValueError("vertical line is outside the visible graph area")
            line = Line(
                self.axes.c2p(vertical_x, y_min),
                self.axes.c2p(vertical_x, y_max),
                color=color,
                stroke_width=4,
            )
            return VGroup(line)
        if abs(slope) < 1e-9:
            if not y_min <= y_intercept <= y_max:
                raise ValueError("line is outside the visible graph area")
        else:
            first = (y_min - y_intercept) / slope
            second = (y_max - y_intercept) / slope
            x_min = max(x_min, min(first, second))
            x_max = min(x_max, max(first, second))
        if x_min >= x_max:
            raise ValueError("line is outside the visible graph area")
        line = self.axes.plot(lambda x: slope * x + y_intercept, x_range=[x_min, x_max], color=color, stroke_width=4)
        return VGroup(line)

    @staticmethod
    def _inset_axis_range(axis_range: tuple) -> tuple[float, float]:
        lower, upper = float(axis_range[0]), float(axis_range[1])
        step = abs(float(axis_range[2]))
        inset = min(step * 0.25, (upper - lower) * 0.1)
        return lower + inset, upper - inset

    def _rise_run_triangle(self, point_a: tuple, point_b: tuple) -> VGroup:
        ax, ay = point_a
        bx, by = point_b
        run_end = (bx, ay)
        p1 = self.axes.c2p(ax, ay)
        p2 = self.axes.c2p(bx, ay)
        p3 = self.axes.c2p(bx, by)
        run_line = Line(p1, p2, color=ORANGE, stroke_width=4)
        rise_line = Line(p2, p3, color=GREEN_B, stroke_width=4)
        run_label = MathTex(rf"\text{{run}}={bx - ax:g}", font_size=22, color=ORANGE).next_to(
            run_line, DOWN, buff=0.1
        )
        rise_label = MathTex(rf"\text{{rise}}={by - ay:g}", font_size=22, color=GREEN_B).next_to(
            rise_line, RIGHT, buff=0.1
        )
        return VGroup(run_line, rise_line, run_label, rise_label)

    def _midpoint_marker(self, point_a: tuple, point_b: tuple) -> VGroup:
        mx = (point_a[0] + point_b[0]) / 2
        my = (point_a[1] + point_b[1]) / 2
        dot = Dot(self.axes.c2p(mx, my), radius=0.09, color=PURPLE_A)
        label = MathTex(rf"M=({mx:g},\,{my:g})", font_size=24, color=PURPLE_A).next_to(dot, UR, buff=0.09)
        return VGroup(dot, label)

    def _distance_visual(self, point_a: tuple, point_b: tuple) -> VGroup:
        p1 = self.axes.c2p(*point_a)
        p2 = self.axes.c2p(*point_b)
        seg = Line(p1, p2, color=YELLOW, stroke_width=4)
        return VGroup(seg)

    def _intercept_markers(
        self,
        slope: float | None,
        y_intercept: float | None,
        x_range: tuple,
        y_range: tuple,
        *,
        vertical_x: float | None = None,
    ) -> VGroup:
        parts = []
        y_range_min, y_range_max = float(y_range[0]), float(y_range[1])
        if vertical_x is not None:
            if x_range[0] <= vertical_x <= x_range[1] and y_range_min <= 0 <= y_range_max:
                dot = Dot(self.axes.c2p(vertical_x, 0), radius=0.08, color=ORANGE)
                label = MathTex(rf"({vertical_x:g},0)", font_size=24, color=ORANGE).next_to(dot, DOWN, buff=0.1)
                parts.extend([dot, label])
            return VGroup(*parts) if parts else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        if abs(slope) > 1e-9:
            xi = -y_intercept / slope
            if x_range[0] <= xi <= x_range[1]:
                dot = Dot(self.axes.c2p(xi, 0), radius=0.08, color=ORANGE)
                label = MathTex(rf"({xi:g},0)", font_size=24, color=ORANGE).next_to(dot, DOWN, buff=0.1)
                parts.extend([dot, label])
        yi = y_intercept
        if y_range_min <= yi <= y_range_max:
            dot = Dot(self.axes.c2p(0, yi), radius=0.08, color=GREEN_B)
            label = MathTex(rf"(0,{yi:g})", font_size=24, color=GREEN_B).next_to(dot, LEFT, buff=0.1)
            parts.extend([dot, label])
        if not parts:
            return VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        return VGroup(*parts)

    @staticmethod
    def _resolve_line(
        point_a: tuple,
        point_b: tuple | None,
        slope: float | None,
        y_intercept: float | None,
    ) -> tuple[float | None, float | None, float | None]:
        vertical_x = None
        if slope is None and point_b is not None:
            dx = point_b[0] - point_a[0]
            dy = point_b[1] - point_a[1]
            if abs(dx) < 1e-9:
                return None, None, point_a[0]
            slope = dy / dx
        if slope is None:
            slope = 1.0
        if y_intercept is None:
            y_intercept = point_a[1] - slope * point_a[0]
        return slope, y_intercept, vertical_x

    @staticmethod
    def _solve_intersection(
        m1: float | None,
        b1: float | None,
        m2: float,
        b2: float,
        *,
        vertical_x: float | None = None,
    ) -> tuple[float, float] | None:
        if vertical_x is not None:
            x = vertical_x
            y = m2 * x + b2
            return (round(x, 4), round(y, 4))
        if abs(m1 - m2) < 1e-9:
            return None
        x = (b2 - b1) / (m1 - m2)
        y = m1 * x + b1
        return (round(x, 4), round(y, 4))
