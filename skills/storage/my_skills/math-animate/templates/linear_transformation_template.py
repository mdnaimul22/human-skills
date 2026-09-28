from manim import *


class LinearTransformationTemplate(VisualTemplate):
    VALID_STATES = frozenset({"setup", "comparison"})
    VECTOR_COLORS = (TEAL_B, ORANGE, GREEN_B, PURPLE_B, RED_C)

    def __init__(
        self,
        state: str,
        *,
        matrix: list[list[float]],
        vectors: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        vector_labels: list[str] | tuple[str, ...] | None = None,
        active_index: int = 0,
        show_span: bool = False,
        show_matrix_label: bool = True,
        x_range: tuple[float, float, float] = (-5, 6, 1),
        y_range: tuple[float, float, float] = (-5, 6, 1),
    ):
        state = self._validate_state(state)
        self.matrix = self._validate_matrix(matrix)
        self.vectors = self._validate_vectors(vectors)
        self.transformed_vectors = [self._transform(vector) for vector in self.vectors]
        self.active_index = self._validate_index(active_index)
        self.show_span = show_span

        labels = list(vector_labels) if vector_labels is not None else [
            rf"v_{{{index + 1}}}" for index in range(len(self.vectors))
        ]
        if len(labels) != len(self.vectors):
            raise ValueError("vector_labels must match vectors length")

        self.axes = Axes(
            x_range=list(x_range),
            y_range=list(y_range),
            x_length=7,
            y_length=5.2,
            tips=False,
            axis_config={"color": GREY_B, "stroke_width": 2},
        )
        axes_group = VGroup(
            self.axes,
            self.axes.get_axis_labels(MathTex("x", font_size=24), MathTex("y", font_size=24)),
        )
        self.vector_labels = labels
        active_vectors = self.vectors if state == "setup" else self.transformed_vectors
        active_labels = labels if state == "setup" else [rf"A{label}" for label in labels]
        self.active_vectors = VGroup(*[
            self._vector_bundle(vector, label, color)
            for vector, label, color in zip(active_vectors, active_labels, self._colors())
        ])
        self.reference_vectors = VGroup(*[
            self._vector_bundle(vector, label, color)
            for vector, label, color in zip(self.vectors, labels, self._colors())
        ])
        self.spans = VGroup(*[
            self._span(vector, color)
            for vector, color in zip(self.vectors, self._colors())
        ])
        self.matrix_label = self._matrix_label() if show_matrix_label else VGroup(VectorizedPoint())

        self._apply_state_opacity(state)
        boundary = Rectangle(width=9.6, height=6).move_to(self.axes).set_opacity(0)
        super().__init__(
            axes_group,
            self.spans,
            self.reference_vectors,
            self.active_vectors,
            self.matrix_label,
            boundary,
            state=state,
        )

    def apply_transformation(self) -> Animation:
        if self.state != "setup":
            raise ValueError("apply_transformation is only available in setup state")
        target_vectors = VGroup(*[
            self._vector_bundle(vector, rf"A{label}", color)
            for vector, label, color in zip(
                self.transformed_vectors,
                self.vector_labels,
                self._colors(),
            )
        ])
        return Transform(self.active_vectors, target_vectors)

    def highlight_vector(self, index: int) -> Animation:
        index = self._validate_index(index)
        return Circumscribe(self.active_vectors[index], color=YELLOW, buff=0.12, fade_out=True)

    def highlight_span(self, index: int) -> Animation:
        index = self._validate_index(index)
        if not self.show_span:
            raise ValueError("highlight_span requires show_span=True")
        return Circumscribe(self.spans[index], color=YELLOW, buff=0.1, fade_out=True)

    def _apply_state_opacity(self, state: str) -> None:
        self.spans.set_opacity(1 if self.show_span else 0)
        self.reference_vectors.set_opacity(0)

        if state == "comparison":
            self.reference_vectors.set_opacity(0.3)

    def _vector_bundle(self, vector, label: str, color: ManimColor) -> VGroup:
        endpoint = self.axes.c2p(*vector)
        arrow = Arrow(self.axes.c2p(0, 0), endpoint, buff=0, color=color, stroke_width=5)
        text = MathTex(label, font_size=25, color=color).next_to(endpoint, UR, buff=0.08)
        return VGroup(arrow, text)

    def _span(self, vector, color: ManimColor) -> VGroup:
        factor = 4.5 / max(abs(vector[0]), abs(vector[1]))
        return VGroup(DashedLine(
            self.axes.c2p(-factor * vector[0], -factor * vector[1]),
            self.axes.c2p(factor * vector[0], factor * vector[1]),
            color=color,
            stroke_opacity=0.55,
        ))

    def _matrix_label(self) -> VGroup:
        a, b = self.matrix[0]
        c, d = self.matrix[1]
        label = MathTex(
            rf"A=\begin{{bmatrix}}{a:g}&{b:g}\\{c:g}&{d:g}\end{{bmatrix}}",
            font_size=27,
        ).move_to(self.axes.get_corner(UR) + LEFT * 0.65 + DOWN * 0.35)
        return VGroup(label)

    def _transform(self, vector) -> tuple[float, float]:
        x, y = vector
        return (
            self.matrix[0][0] * x + self.matrix[0][1] * y,
            self.matrix[1][0] * x + self.matrix[1][1] * y,
        )

    def _validate_index(self, index: int) -> int:
        if not isinstance(index, int) or not 0 <= index < len(self.vectors):
            raise ValueError("active vector index is outside vectors")
        return index

    @staticmethod
    def _validate_matrix(matrix) -> list[list[float]]:
        if (
            not isinstance(matrix, list)
            or len(matrix) != 2
            or any(not isinstance(row, list) or len(row) != 2 for row in matrix)
            or any(not isinstance(value, (int, float)) for row in matrix for value in row)
        ):
            raise ValueError("matrix must be a numeric 2x2 list")
        return matrix

    @staticmethod
    def _validate_vectors(vectors) -> list[tuple[float, float]]:
        if not isinstance(vectors, (list, tuple)) or not vectors:
            raise ValueError("vectors must be a non-empty list")
        if any(
            not isinstance(vector, (list, tuple))
            or len(vector) != 2
            or any(not isinstance(value, (int, float)) for value in vector)
            or vector == (0, 0)
            or vector == [0, 0]
            for vector in vectors
        ):
            raise ValueError("vectors must contain non-zero numeric 2D vectors")
        return [tuple(vector) for vector in vectors]

    def _colors(self):
        return [
            self.VECTOR_COLORS[index % len(self.VECTOR_COLORS)]
            for index in range(len(self.vectors))
        ]
