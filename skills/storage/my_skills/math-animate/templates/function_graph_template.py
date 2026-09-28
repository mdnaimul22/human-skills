import math

from manim import *


class FunctionGraphTemplate(VisualTemplate):
    VALID_STATES = frozenset({
        "curve",
        "marked_points",
        "secant",
        "tangent",
        "area",
        "comparison",
        "signed_areas",
    })
    VALID_FUNCTION_TYPES = frozenset({
        "linear",
        "quadratic",
        "polynomial",
        "absolute_value",
        "exponential",
        "reciprocal",
    })

    def __init__(
        self,
        state: str,
        *,
        function_type: str = "quadratic",
        function_parameters: dict | None = None,
        function_label: str = r"f(x)",
        comparison_function_type: str | None = None,
        comparison_function_parameters: dict | None = None,
        comparison_label: str = r"g(x)",
        x_range: tuple[float, float, float] = (-5, 6, 1),
        y_range: tuple[float, float, float] = (-4, 7, 1),
        graph_x_range: tuple[float, float] = (-4.5, 4.5),
        marked_xs: list[float] | tuple[float, ...] = (),
        secant_xs: tuple[float, float] = (-1, 2),
        tangent_x: float = 1,
        area_interval: tuple[float, float] = (0.5, 2),
        segments: list[tuple[float, float, float]] | tuple[tuple[float, float, float], ...] = (),
        segment_labels: list[str] | tuple[str, ...] | None = None,
    ):
        state = self._validate_state(state)
        self.function_type = self._validate_function_type(function_type)
        self.function_parameters = dict(function_parameters or {})
        self.function = self._function(self.function_type, self.function_parameters)
        self.graph_x_range = graph_x_range
        self.graph_y_range = self._inset_range(y_range)
        self.secant_xs = secant_xs
        self.tangent_x = tangent_x
        self.area_interval = area_interval
        self.segments = self._validate_segments(segments) if state == "signed_areas" else []

        self.axes = Axes(
            x_range=list(x_range),
            y_range=list(y_range),
            x_length=7.4,
            y_length=4.9,
            tips=False,
            axis_config={"color": GREY_B, "stroke_width": 2},
        )
        axes_group = VGroup(
            self.axes,
            self.axes.get_axis_labels(MathTex("x", font_size=24), MathTex("y", font_size=24)),
        )
        self.graph = self._plot(
            self.function,
            self.function_type,
            self.function_parameters,
            color=TEAL_B,
        )
        graph_label = MathTex(function_label, font_size=28, color=TEAL_B).to_corner(UR)
        graph_label.move_to(self.axes.get_corner(UR) + LEFT * 0.35 + DOWN * 0.25)
        graph_bundle = VGroup(self.graph, graph_label)
        if state == "signed_areas":
            graph_bundle.set_opacity(0)

        points_bundle = (
            VGroup(*[self._point_bundle(x, color=YELLOW) for x in marked_xs])
            if state == "marked_points"
            else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        )
        self.secant_bundle = (
            self._secant_bundle(*secant_xs)
            if state == "secant"
            else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        )
        self.tangent_bundle = (
            self._tangent_bundle(tangent_x)
            if state == "tangent"
            else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        )
        self.area_bundle = (
            self._area_bundle(*area_interval)
            if state == "area"
            else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        )
        self.intercept_bundle = self._intercept_bundle()

        comparison_bundle = VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        if state == "comparison":
            if comparison_function_type is None:
                raise ValueError("comparison state requires comparison_function_type")
            comparison_type = self._validate_function_type(comparison_function_type)
            comparison_parameters = dict(comparison_function_parameters or {})
            comparison_function = self._function(comparison_type, comparison_parameters)
            comparison_graph = self._plot(
                comparison_function,
                comparison_type,
                comparison_parameters,
                color=ORANGE,
            )
            comparison_graph_label = MathTex(
                comparison_label,
                font_size=28,
                color=ORANGE,
            ).move_to(self.axes.get_corner(UL) + RIGHT * 0.35 + DOWN * 0.25)
            comparison_bundle = VGroup(comparison_graph, comparison_graph_label)
        signed_areas_bundle = (
            self._signed_areas_bundle(self.segments, segment_labels)
            if state == "signed_areas"
            else VGroup(VectorizedPoint(self.axes.c2p(0, 0)))
        )

        self.intercept_bundle.set_opacity(0)

        boundary = Rectangle(width=9.4, height=6).move_to(self.axes).set_opacity(0)
        super().__init__(
            axes_group,
            graph_bundle,
            points_bundle,
            self.secant_bundle,
            self.tangent_bundle,
            self.area_bundle,
            comparison_bundle,
            signed_areas_bundle,
            self.intercept_bundle,
            boundary,
            state=state,
        )

    def move_secant_point(self, target_x: float) -> Animation:
        if self.state != "secant":
            raise ValueError("move_secant_point is only available in secant state")
        first_x, _ = self.secant_xs
        if target_x == first_x:
            raise ValueError("secant points must have different x values")
        target = self._secant_bundle(first_x, target_x)
        self.secant_xs = (first_x, target_x)
        return Transform(self.secant_bundle, target)

    def reveal_tangent(self) -> Animation:
        target = self._tangent_bundle(self.tangent_x)
        return Transform(self.tangent_bundle, target)

    def shade_interval(self, start: float, end: float) -> Animation:
        target = self._area_bundle(start, end)
        self.area_interval = (start, end)
        return Transform(self.area_bundle, target)

    def highlight_intercept(self) -> Animation:
        if len(self.intercept_bundle.submobjects) == 0:
            raise ValueError("the configured function has no visible intercept")
        return AnimationGroup(
            self.intercept_bundle.animate.set_opacity(1),
            Circumscribe(self.intercept_bundle, color=YELLOW, buff=0.12, fade_out=True),
        )

    @classmethod
    def _validate_function_type(cls, function_type: str) -> str:
        if function_type not in cls.VALID_FUNCTION_TYPES:
            valid = ", ".join(sorted(cls.VALID_FUNCTION_TYPES))
            raise ValueError(f"function_type must be one of: {valid}")
        return function_type

    @staticmethod
    def _function(function_type: str, parameters: dict):
        if function_type == "linear":
            m, b = parameters.get("m", 1), parameters.get("b", 0)
            return lambda x: m * x + b
        if function_type == "quadratic":
            a, b, c = parameters.get("a", 1), parameters.get("b", 0), parameters.get("c", 0)
            return lambda x: a * x**2 + b * x + c
        if function_type == "polynomial":
            coefficients = parameters.get("coefficients", [1, 0])
            if not isinstance(coefficients, (list, tuple)) or not coefficients:
                raise ValueError("polynomial coefficients must be a non-empty list")
            return lambda x: sum(coefficient * x**power for power, coefficient in enumerate(reversed(coefficients)))
        if function_type == "absolute_value":
            a, h, k = parameters.get("a", 1), parameters.get("h", 0), parameters.get("k", 0)
            return lambda x: a * abs(x - h) + k
        if function_type == "exponential":
            a, base, k = parameters.get("a", 1), parameters.get("base", 2), parameters.get("k", 0)
            if base <= 0 or base == 1:
                raise ValueError("exponential base must be positive and not equal to one")
            return lambda x: a * base**x + k
        a, h, k = parameters.get("a", 1), parameters.get("h", 0), parameters.get("k", 0)
        return lambda x: a / (x - h) + k

    def _plot(
        self,
        function,
        function_type: str,
        parameters: dict,
        *,
        color: ManimColor,
    ) -> VGroup:
        left, right = self.graph_x_range
        source_ranges = [(left, right)]
        if function_type == "reciprocal":
            h = parameters.get("h", 0)
            epsilon = 0.08
            source_ranges = []
            if left < h - epsilon:
                source_ranges.append((left, h - epsilon))
            if right > h + epsilon:
                source_ranges.append((h + epsilon, right))

        visible_ranges = self._visible_x_ranges(function, source_ranges)
        parts = VGroup()
        for visible_left, visible_right in visible_ranges:
            parts.add(self.axes.plot(
                function,
                x_range=[visible_left, visible_right],
                color=color,
                stroke_width=4,
                use_smoothing=False,
            ))
        if not parts.submobjects:
            raise ValueError("configured function is outside the visible y range")
        parts.visible_x_ranges = visible_ranges
        return parts

    def _point_bundle(self, x: float, *, color: ManimColor) -> VGroup:
        y = self.function(x)
        if not math.isfinite(y):
            raise ValueError("point is not defined on the configured function")
        if not self._is_visible_y(y):
            raise ValueError("point must lie inside the visible y range")
        dot = Dot(self.axes.c2p(x, y), radius=0.065, color=color)
        label = MathTex(rf"({x:g},{y:g})", font_size=22, color=color).next_to(dot, UR, buff=0.08)
        return VGroup(dot, label)

    def _secant_bundle(self, first_x: float, second_x: float) -> VGroup:
        if first_x == second_x:
            raise ValueError("secant points must have different x values")
        first = self._point_bundle(first_x, color=YELLOW)
        second = self._point_bundle(second_x, color=ORANGE)
        line = Line(first[0].get_center(), second[0].get_center(), color=ORANGE, stroke_width=4)
        return VGroup(line, first, second)

    def _tangent_bundle(self, x: float) -> VGroup:
        delta = 1e-4
        y = self.function(x)
        slope = (self.function(x + delta) - self.function(x - delta)) / (2 * delta)
        half_width = 1.4
        left = max(self.graph_x_range[0], x - half_width)
        right = min(self.graph_x_range[1], x + half_width)
        left, right = self._clip_linear_domain(slope, y - slope * x, left, right)
        line = Line(
            self.axes.c2p(left, slope * left + y - slope * x),
            self.axes.c2p(right, slope * right + y - slope * x),
            color=GREEN_B,
            stroke_width=5,
        )
        return VGroup(line, self._point_bundle(x, color=YELLOW))

    def _area_bundle(self, start: float, end: float) -> VGroup:
        if start >= end:
            raise ValueError("area interval start must be less than end")
        graph = next((
            graph_part
            for graph_part, (left, right) in zip(self.graph, self.graph.visible_x_ranges)
            if left <= start and end <= right
        ), None)
        if graph is None:
            raise ValueError("area interval must lie inside one visible graph segment")
        area = self.axes.get_area(graph, x_range=(start, end), color=BLUE, opacity=0.35)
        return VGroup(area)

    def _signed_areas_bundle(self, segments, segment_labels) -> VGroup:
        labels = list(segment_labels) if segment_labels is not None else [
            rf"A={velocity * (end - start):g}"
            for start, end, velocity in segments
        ]
        if len(labels) != len(segments):
            raise ValueError("segment_labels must match segments length")

        bundle = VGroup()
        for (start, end, velocity), label in zip(segments, labels):
            if not self._is_visible_y(velocity):
                raise ValueError("segment values must lie inside the visible y range")
            color = TEAL_B if velocity >= 0 else RED_C
            line = Line(
                self.axes.c2p(start, velocity),
                self.axes.c2p(end, velocity),
                color=color,
                stroke_width=5,
            )
            area = Polygon(
                self.axes.c2p(start, 0),
                self.axes.c2p(start, velocity),
                self.axes.c2p(end, velocity),
                self.axes.c2p(end, 0),
                color=color,
                fill_color=color,
                fill_opacity=0.3,
                stroke_opacity=0,
            )
            area_label = MathTex(label, font_size=27, color=color).next_to(
                self.axes.c2p((start + end) / 2, velocity),
                UP if velocity >= 0 else DOWN,
                buff=0.14,
            )
            bundle.add(VGroup(area, line, area_label))
        return bundle

    @staticmethod
    def _inset_range(axis_range) -> tuple[float, float]:
        lower, upper = float(axis_range[0]), float(axis_range[1])
        step = abs(float(axis_range[2]))
        inset = min(step * 0.25, (upper - lower) * 0.1)
        return lower + inset, upper - inset

    def _is_visible_y(self, value: float) -> bool:
        return math.isfinite(value) and self.graph_y_range[0] <= value <= self.graph_y_range[1]

    def _visible_x_ranges(self, function, source_ranges) -> list[tuple[float, float]]:
        ranges = []
        for left, right in source_ranges:
            sample_count = 400
            xs = [left + (right - left) * index / sample_count for index in range(sample_count + 1)]
            visible = [self._function_is_visible(function, x) for x in xs]
            index = 0
            while index <= sample_count:
                if not visible[index]:
                    index += 1
                    continue
                start_index = index
                while index < sample_count and visible[index + 1]:
                    index += 1
                end_index = index
                visible_left = xs[start_index]
                visible_right = xs[end_index]
                if start_index > 0:
                    visible_left = self._visibility_boundary(function, xs[start_index], xs[start_index - 1])
                if end_index < sample_count:
                    visible_right = self._visibility_boundary(function, xs[end_index], xs[end_index + 1])
                if visible_right - visible_left > 1e-6:
                    ranges.append((visible_left, visible_right))
                index += 1
        return ranges

    def _function_is_visible(self, function, x: float) -> bool:
        try:
            return self._is_visible_y(function(x))
        except (ArithmeticError, OverflowError, ValueError):
            return False

    def _visibility_boundary(self, function, visible_x: float, hidden_x: float) -> float:
        for _ in range(24):
            midpoint = (visible_x + hidden_x) / 2
            if self._function_is_visible(function, midpoint):
                visible_x = midpoint
            else:
                hidden_x = midpoint
        return visible_x

    def _clip_linear_domain(
        self,
        slope: float,
        intercept: float,
        left: float,
        right: float,
    ) -> tuple[float, float]:
        if abs(slope) < 1e-9:
            if not self._is_visible_y(intercept):
                raise ValueError("line is outside the visible y range")
            return left, right
        first = (self.graph_y_range[0] - intercept) / slope
        second = (self.graph_y_range[1] - intercept) / slope
        left = max(left, min(first, second))
        right = min(right, max(first, second))
        if left >= right:
            raise ValueError("line is outside the visible graph area")
        return left, right

    @staticmethod
    def _validate_segments(segments) -> list[tuple[float, float, float]]:
        if not isinstance(segments, (list, tuple)) or not segments:
            raise ValueError("signed_areas state requires non-empty segments")
        if any(
            not isinstance(segment, (list, tuple))
            or len(segment) != 3
            or any(not isinstance(value, (int, float)) for value in segment)
            or segment[0] >= segment[1]
            for segment in segments
        ):
            raise ValueError("segments must contain numeric (start, end, value) entries")
        return [tuple(segment) for segment in segments]

    def _intercept_bundle(self) -> VGroup:
        intercepts = VGroup()
        try:
            y = self.function(0)
            if abs(y) < 1e6:
                intercepts.add(self._point_bundle(0, color=YELLOW))
        except (ArithmeticError, ValueError, OverflowError):
            pass
        return intercepts
