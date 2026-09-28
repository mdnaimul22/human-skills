from manim import *


class FunctionTranslationTemplate(VisualTemplate):
    VALID_STATES = frozenset({"parent", "comparison"})

    def __init__(
        self,
        state: str,
        parent_function=lambda x: x**2,
        *,
        h: float = 0,
        k: float = 0,
        a: float | None = None,
        anchor_point: tuple[float, float] | None = (0, 0),
        x_range: tuple[float, float, float] = (-4, 5, 1),
        y_range: tuple[float, float, float] = (-3, 7, 1),
        graph_x_range: tuple[float, float] = (-2.4, 2.4),
        parent_label: str = r"f(x)",
        transformed_label: str | None = None,
    ):
        state = self._validate_state(state)
        self.h = 0 if state == "parent" else h
        self.k = 0 if state == "parent" else k
        self.a = 1.0 if state == "parent" or a is None else a
        self._validate_scale_value(self.a)
        self.anchor_point = anchor_point
        self._parent_function = parent_function
        self._graph_x_range = graph_x_range
        self._parent_label = parent_label

        self.axes = Axes(
            x_range=list(x_range),
            y_range=list(y_range),
            x_length=6.4,
            y_length=4.8,
            tips=False,
            axis_config={"color": GREY_B, "stroke_width": 2},
        )
        axes_group = VGroup(
            self.axes,
            self.axes.get_axis_labels(
                MathTex("x", font_size=24),
                MathTex("y", font_size=24),
            ),
        )

        reference_graph_bundle = self._graph_bundle(
            h=0,
            k=0,
            a=1,
            color=TEAL_B,
            label=parent_label,
            stroke_width=4,
        )
        self.active_graph_bundle = self._graph_bundle(
            h=self.h,
            k=self.k,
            a=self.a,
            color=YELLOW,
            label=(
                parent_label
                if state == "parent"
                else transformed_label or self._transformed_label(self.h, self.k, self.a)
            ),
            stroke_width=5,
        )
        self.active_anchor = self._anchor_marker(self.h, self.k, self.a, YELLOW)
        reference_anchor = self._anchor_marker(0, 0, 1, TEAL_B)
        self.annotations = VGroup(VectorizedPoint(self._anchor_position(self.h, self.k, self.a)))

        if state != "comparison":
            reference_graph_bundle.set_opacity(0)
            reference_anchor.set_opacity(0)

        plot_boundary = Rectangle(
            width=self.axes.width + 1.4,
            height=self.axes.height + 0.8,
        ).move_to(self.axes).set_opacity(0)
        super().__init__(
            axes_group,
            self.active_graph_bundle,
            self.active_anchor,
            reference_graph_bundle,
            reference_anchor,
            self.annotations,
            plot_boundary,
            state=state,
        )

    def shift_horizontal(self, target_h: float) -> Animation:
        start = self._anchor_position(self.h, self.k, self.a)
        self.h = target_h
        return self._transformation_animation(start, ORANGE)

    def shift_vertical(self, target_k: float) -> Animation:
        start = self._anchor_position(self.h, self.k, self.a)
        self.k = target_k
        return self._transformation_animation(start, GREEN_B)

    def scale_horizontal(self, target_a: float) -> Animation:
        self._validate_scale_value(target_a)
        start = self._anchor_position(self.h, self.k, self.a)
        self.a = target_a
        return self._transformation_animation(start, ORANGE)

    def _transformation_animation(self, start, arrow_color: ManimColor) -> Animation:
        target_graph = self._graph_bundle(
            h=self.h,
            k=self.k,
            a=self.a,
            color=YELLOW,
            label=self._transformed_label(self.h, self.k, self.a),
            stroke_width=5,
        )
        target_anchor = self._anchor_marker(self.h, self.k, self.a, YELLOW)
        end = self._anchor_position(self.h, self.k, self.a)
        target_annotations = self._movement_arrow(start, end, arrow_color)
        return AnimationGroup(
            Transform(self.active_graph_bundle, target_graph),
            Transform(self.active_anchor, target_anchor),
            Transform(self.annotations, target_annotations),
        )

    def _graph_bundle(
        self,
        *,
        h: float,
        k: float,
        a: float,
        color: ManimColor,
        label: str,
        stroke_width: float,
    ) -> VGroup:
        graph_x_range = [
            self._graph_x_range[0] / a + h,
            self._graph_x_range[1] / a + h,
        ]
        graph = self.axes.plot(
            lambda x: self._parent_function(a * (x - h)) + k,
            x_range=graph_x_range,
            color=color,
            stroke_width=stroke_width,
        )
        graph_label = self.axes.get_graph_label(
            graph,
            label=MathTex(label, font_size=27, color=color),
            x_val=graph_x_range[1] - 0.45,
            direction=UR,
        ).shift(UP * 0.16 + RIGHT * 0.08)
        return VGroup(graph, graph_label)

    def _anchor_marker(
        self,
        h: float,
        k: float,
        a: float,
        color: ManimColor,
    ) -> VGroup:
        position = self._anchor_position(h, k, a)
        if self.anchor_point is None:
            return VGroup(VectorizedPoint(position))
        x, y = self._transformed_anchor(h, k, a)
        dot = Dot(position, radius=0.065, color=color)
        label = MathTex(
            rf"({x:g},{y:g})",
            font_size=24,
            color=color,
        ).next_to(dot, DOWN, buff=0.12).shift(RIGHT * 0.18)
        return VGroup(dot, label)

    def _anchor_position(self, h: float, k: float, a: float):
        if self.anchor_point is None:
            return self.axes.c2p(0, 0)
        return self.axes.c2p(*self._transformed_anchor(h, k, a))

    def _transformed_anchor(self, h: float, k: float, a: float) -> tuple[float, float]:
        x, y = self.anchor_point
        return x / a + h, y + k

    @staticmethod
    def _movement_arrow(start, end, color: ManimColor) -> VGroup:
        if all(abs(value) < 1e-9 for value in end - start):
            return VGroup(VectorizedPoint(start))
        return VGroup(Arrow(start, end, buff=0, color=color, stroke_width=4))

    def _transformed_label(self, h: float, k: float, a: float) -> str:
        expression = "x"
        if abs(h) > 1e-9:
            expression = rf"x-{h:g}" if h > 0 else rf"x+{abs(h):g}"
        if abs(a - 1) > 1e-9:
            expression = rf"{a:g}({expression})"
        label = rf"f({expression})"
        if abs(k) > 1e-9:
            label += rf"+{k:g}" if k > 0 else rf"{k:g}"
        return label

    @staticmethod
    def _validate_scale_value(a: float) -> None:
        if not isinstance(a, (int, float)) or a <= 0:
            raise ValueError("horizontal scale factor a must be positive")
