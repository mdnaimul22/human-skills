# 14 Mathematical Templates — Full API Specification & Signature Reference

This reference document contains the exhaustive, empirically verified constructor signatures, supported states, parameter constraints, and animation action methods for all 14 visual templates in `templates/`.

---

## 1. `EquationTemplate`
Subclasses `VisualTemplate`. Manages LaTeX mathematical formulas, derivations, multi-step history, and expression morphing.

### Constructor Signature:
```python
EquationTemplate(
    state: str,
    expression: str | None = None,
    expressions: list[str] | tuple[str, ...] | None = None
)
```

### Valid States & Constraints:
- `"display"`: Single formula. Requires non-empty string in `expression`. Raises `ValueError` if `expressions` is passed.
- `"derivation"`: 1 to 3 step derivation history. Requires list of 1 to 3 strings in `expressions`. Raises `ValueError` if `expression` is passed.
- `"statements"`: Up to 3 equivalent statements displayed together. Requires list of 1 to 3 strings in `expressions`. Raises `ValueError` if `expression` is passed.

### Action Animation Methods:
- `set_expression(expression: str) -> Animation`: Morphs current equation into a new expression (`display` state only).
- `advance_step(expression: str) -> Animation`: Advances derivation history with the next step (`derivation` state only).
- `highlight_formula(index: int | None = None) -> Animation`: Pulses yellow outline highlight around target formula.

---

## 2. `FunctionGraphTemplate`
Subclasses `VisualTemplate`. Renders function curves on coordinate axes with tangents, secants, definite integrals, marked points, and comparative graphs.

### Constructor Signature:
```python
FunctionGraphTemplate(
    state: str,
    *,
    function_type: str = "quadratic",
    function_parameters: dict | None = None,
    function_label: str = "f(x)",
    comparison_function_type: str | None = None,
    comparison_function_parameters: dict | None = None,
    comparison_label: str = "g(x)",
    x_range: tuple[float, float, float] = (-5, 6, 1),
    y_range: tuple[float, float, float] = (-4, 7, 1),
    graph_x_range: tuple[float, float] = (-4.5, 4.5),
    marked_xs: list[float] | tuple[float, ...] = (),
    secant_xs: tuple[float, float] = (-1, 2),
    tangent_x: float = 1,
    area_interval: tuple[float, float] = (0.5, 2),
    segments: list[tuple[float, float, float]] | tuple[tuple[float, float, float], ...] = (),
    segment_labels: list[str] | tuple[str, ...] | None = None
)
```

### Supported Function Types:
`"quadratic"`, `"cubic"`, `"sine"`, `"cosine"`, `"exponential"`, `"linear"`, `"rational"`.

### Valid States:
`"curve"`, `"marked_points"`, `"secant"`, `"tangent"`, `"area"`, `"signed_areas"`, `"comparison"`.

### Action Animation Methods:
- `reveal_tangent() -> Animation`: Draws tangent line at `tangent_x`.
- `move_secant_point(target_x: float) -> Animation`: Slides secant point along the curve towards limit.
- `shade_interval(start: float, end: float) -> Animation`: Dynamically shades area under the curve between `start` and `end`.
- `highlight_intercept() -> Animation`: Pulses markers at x- and y-intercepts.

---

## 3. `VectorTemplate`
Subclasses `VisualTemplate`. Renders 2D vectors, orthogonal components, vector addition (triangle law), subtraction, scalar multiplication, and projections.

### Constructor Signature:
```python
VectorTemplate(
    state: str,
    *,
    vector_a: tuple[float, float],
    vector_b: tuple[float, float] | None = None,
    scalar: float = 2.0,
    vector_a_label: str = "a",
    vector_b_label: str = "b",
    result_label: str = "r",
    show_grid: bool = True,
    show_coordinate_labels: bool = True,
    x_range: tuple[float, float, float] = (-5, 6, 1),
    y_range: tuple[float, float, float] = (-5, 6, 1)
)
```

### Valid States:
`"single"`, `"components"`, `"addition"`, `"subtraction"`, `"scalar_multiple"`, `"projection"`.

### Action Animation Methods:
- `reveal_components() -> Animation`: Draws orthogonal dashed component vectors $a_x\hat{i}$ and $a_y\hat{j}$.
- `reveal_resultant() -> Animation`: Draws resultant vector arrow for addition $\vec{a} + \vec{b}$.
- `set_scalar(target_scalar: float) -> Animation`: Smoothly scales vector by `target_scalar`.
- `highlight_vector(role: str) -> Animation`: Highlights vector by role (`"a"`, `"b"`, or `"r"`).
- `highlight_projection() -> Animation`: Projects vector $\vec{a}$ onto vector $\vec{b}$.

---

## 4. `MatrixTemplate`
Subclasses `VisualTemplate`. Visualizes matrix representations, row/column operations, and step-by-step matrix multiplication.

### Constructor Signature:
```python
MatrixTemplate(
    state: str,
    *,
    matrix: list[list[float]] | None = None,
    label: str = "A",
    left_matrix: list[list[float]] | None = None,
    right_matrix: list[list[float]] | None = None,
    left_label: str = "A",
    right_label: str = "B",
    result_label: str = "C",
    active_row: int = 0,
    active_column: int = 0
)
```

### Valid States:
`"display"`, `"product_setup"`, `"product_progress"`, `"product_complete"`.

### Action Animation Methods:
- `reveal_product_cell() -> Animation`: Computes dot product calculation for `active_row` and `active_column`.
- `select_product_cell(row: int, column: int) -> Animation`: Shifts active selection focus to specified cell.
- `highlight_row(row: int) -> Animation`: Outlines target row in yellow.
- `highlight_column(column: int) -> Animation`: Outlines target column in yellow.
- `highlight_cell(row: int, column: int) -> Animation`: Pulses target entry cell.

---

## 5. `NumberLineTemplate`
Subclasses `VisualTemplate`. Renders real number lines, intervals, arithmetic hops, and distances.

### Constructor Signature:
```python
NumberLineTemplate(
    state: str,
    *,
    x_range: tuple[float, float, float] = (-5, 6, 1),
    points: list[float] | tuple[float, ...] = (),
    point_labels: list[str] | tuple[str, ...] | None = None,
    start: float = -2,
    end: float = 2,
    left_closed: bool = True,
    right_closed: bool = True,
    intervals: list[tuple[float, float, bool, bool]] | tuple[tuple[float, float, bool, bool], ...] = (),
    excluded_points: list[float] | tuple[float, ...] = (),
    value: float = 0,
    value_label: str | None = None,
    title: str | None = None,
    center: float | None = None,
    radius: float | None = None
)
```

### Valid States:
`"points"`, `"interval"`, `"intervals"`, `"operation"`, `"distance"`.

### Action Animation Methods:
- `move_point(target_value: float) -> Animation`: Slides marker along the number line to `target_value`.
- `set_interval(start: float, end: float, left_closed: bool, right_closed: bool) -> Animation`: Updates interval bounds.
- `highlight_distance() -> Animation`: Highlights segment between center and radius.

---

## 6. `UnitCircleTemplate`
Subclasses `VisualTemplate`. Renders trigonometric unit circle, angles, coordinates $(\cos\theta, \sin\theta)$, and reference triangles.

### Constructor Signature:
```python
UnitCircleTemplate(
    state: str,
    *,
    angle_degrees: float = 30,
    angle_label: str | None = None,
    coordinate_label: str | None = None,
    cosine_label: str = r"\cos\theta",
    sine_label: str = r"\sin\theta",
    radius_label: str = "1",
    show_axes_labels: bool = True
)
```

### Valid States:
`"base"`, `"angle"`, `"coordinates"`, `"reference_triangle"`.

### Action Animation Methods:
- `rotate_to_angle(target_degrees: float, angle_label=None, coordinate_label=None) -> Animation`: Rotates radius ray to `target_degrees`.
- `reveal_coordinates() -> Animation`: Displays $(\cos\theta, \sin\theta)$ coordinate point.
- `reveal_reference_triangle() -> Animation`: Draws right reference triangle inside circle.
- `highlight_projection(axis: str) -> Animation`: Pulses projection onto `"x"` or `"y"` axis.

---

## 7. `LinearTransformationTemplate`
Subclasses `VisualTemplate`. Visualizes 2D linear matrix transformations $T(\vec{x}) = A\vec{x}$ on grid lines and basis vectors.

### Constructor Signature:
```python
LinearTransformationTemplate(
    state: str,
    *,
    matrix: list[list[float]],
    vectors: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    vector_labels: list[str] | tuple[str, ...] | None = None,
    active_index: int = 0,
    show_span: bool = False,
    show_matrix_label: bool = True,
    x_range: tuple[float, float, float] = (-5, 6, 1),
    y_range: tuple[float, float, float] = (-5, 6, 1)
)
```

### Valid States:
`"setup"`, `"comparison"`.

### Action Animation Methods:
- `apply_transformation() -> Animation`: Morphs 2D coordinate grid and basis vectors using matrix $A$.
- `highlight_vector(index: int) -> Animation`: Pulses vector at `index`.
- `highlight_span(index: int) -> Animation`: Highlights 1D span line.

---

## 8. `TriangleTemplate`
Subclasses `VisualTemplate`. Triangle geometry, side lengths, angles, altitudes, medians, and angle bisectors.

### Constructor Signature:
```python
TriangleTemplate(
    state: str,
    leg_a: float | None = None,
    leg_b: float | None = None,
    *,
    triangle_type: str = "scalene",
    width: float = 3.2,
    height: float = 2.2,
    apex_offset: float = 0.15,
    vertex_labels: tuple[str, str, str] = ('A', 'B', 'C'),
    side_labels: tuple[str, str, str] = ('a', 'b', 'c'),
    active_vertex: str = 'A'
)
```

### Valid States:
`"right_base"`, `"right_labeled"`, `"right_hypotenuse_highlighted"`, `"right_squares"`, `"general_base"`, `"general_labeled"`, `"altitude"`, `"median"`, `"angle_bisector"`, `"non_right_labeled"`.

### Action Animation Methods:
- `highlight_side(side: str) -> Animation`: Outlines side (`side="a"`, `"b"`, or `"c"`).
- `highlight_angle(vertex: str) -> Animation`: Highlights angle arc at vertex (`vertex="A"`, `"B"`, or `"C"`).
- `highlight_construction() -> Animation`: Emphasizes altitude, median, or bisector.

---

## 9. `PythagoreanAreaTemplate`
Subclasses `VisualTemplate`. Geometric proof of $a^2 + b^2 = c^2$ with attached squares.

### Constructor Signature:
```python
PythagoreanAreaTemplate(
    state: str,
    leg_a: float = 1.35,
    leg_b: float = 2.15,
    include_side_labels: bool = True
)
```

### Valid States:
`"c_square"`, `"ab_squares"`.

---

## 10. `LineGeometryTemplate`
Subclasses `VisualTemplate`. 2D Coordinate geometry, slopes, rise-over-run triangles, midpoints, segment distances, and line intersections.

### Constructor Signature:
```python
LineGeometryTemplate(
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
    labels: bool = True
)
```

### Valid States:
`"point_plot"`, `"slope_rise_run"`, `"midpoint"`, `"distance"`, `"line_equation"`, `"intercepts"`, `"intersection"`.

### Action Animation Methods:
- `show_slope_triangle() -> Animation`: Draws rise-over-run right triangle.
- `show_midpoint() -> Animation`: Displays midpoint dot and coordinate label.
- `show_distance() -> Animation`: Highlights segment distance with length label.
- `show_intercepts() -> Animation`: Highlights $x$- and $y$-intercept markers.
- `show_intersection() -> Animation`: Points to intersection coordinate of two lines.

---

## 11. `CircleTheoremsTemplate`
Subclasses `VisualTemplate`. Circle theorems: tangent-radius perpendicularity, chords, secants, central angles, and inscribed angles.

### Constructor Signature:
```python
CircleTheoremsTemplate(
    state: str,
    *,
    radius: float = 2.0,
    center: tuple[float, float] = (0, 0),
    chord_angle: float = 60,
    secant_point: tuple[float, float] = (4, 0),
    arc_start_angle: float = 30,
    arc_end_angle: float = 150,
    inscribed_vertex_angle: float = 200,
    labels: bool = True
)
```

### Valid States:
`"radius_tangent"`, `"chord"`, `"secant"`, `"arc_central"`, `"inscribed_angle"`.

### Action Animation Methods:
- `show_radius_tangent() -> Animation`: Marks $90^\circ$ right angle between radius and tangent line.
- `show_perpendicular_bisector() -> Animation`: Draws chord bisector through circle center.
- `show_arc_angle() -> Animation`: Highlights central angle and subtended arc.
- `show_inscribed_relationship() -> Animation`: Demonstrates inscribed angle is half of central angle.

---

## 12. `PolygonTransformationTemplate`
Subclasses `VisualTemplate`. 2D Rigid transformations of arbitrary polygons: translations, reflections over axes, rotations about a center, and dilations.

### Constructor Signature:
```python
PolygonTransformationTemplate(
    state: str,
    vertices: list[tuple[float, float]],
    *,
    translation_vector: tuple[float, float] = (2, 1),
    reflection_axis: str = 'x',
    rotation_angle: float = 90,
    rotation_center: tuple[float, float] = (0, 0),
    dilation_factor: float = 2.0,
    dilation_center: tuple[float, float] = (0, 0),
    x_range: tuple = (-6, 6, 1),
    y_range: tuple = (-4, 4, 1),
    labels: bool = True
)
```

### Valid States:
`"original"`, `"translated"`, `"reflected"`, `"rotated"`, `"dilated"`.

### Action Animation Methods:
- `translate() -> Animation`: Slides polygon along `translation_vector`.
- `reflect() -> Animation`: Flips polygon across `reflection_axis`.
- `rotate() -> Animation`: Rotates polygon by `rotation_angle`.
- `dilate() -> Animation`: Scales polygon by `dilation_factor`.

---

## 13. `FunctionTranslationTemplate`
Subclasses `VisualTemplate`. Function shifts $f(x - h) + k$ and horizontal scaling $f(ax)$ against parent curves.

### Constructor Signature:
```python
FunctionTranslationTemplate(
    state: str,
    parent_function = lambda x: x**2,
    *,
    h: float = 0,
    k: float = 0,
    a: float | None = None,
    anchor_point: tuple[float, float] | None = (0, 0),
    x_range: tuple[float, float, float] = (-4, 5, 1),
    y_range: tuple[float, float, float] = (-3, 7, 1),
    graph_x_range: tuple[float, float] = (-2.4, 2.4),
    parent_label: str = "f(x)",
    transformed_label: str | None = None
)
```

### Valid States:
`"parent"`, `"comparison"`.

### Action Animation Methods:
- `shift_horizontal(target_h: float) -> Animation`: Animates horizontal translation.
- `shift_vertical(target_k: float) -> Animation`: Animates vertical translation.
- `scale_horizontal(target_a: float) -> Animation`: Scales curve horizontally.

---

## 14. `FractionModelTemplate`
Subclasses `VisualTemplate`. Visual fraction models: horizontal fraction bars, circular pie models, and partition grids.

### Constructor Signature:
```python
FractionModelTemplate(
    state: str,
    *,
    numerator: int = 1,
    denominator: int = 2,
    show_label: bool = True,
    label: str | None = None,
    grid_shape: tuple[int, int] | None = None,
    show_part_numbers: bool = False
)
```

### Valid States:
`"bar"`, `"grid"`, `"circle"`.

### Action Animation Methods:
- `set_fraction(numerator: int, denominator: int) -> Animation`: Updates filled portions.
- `highlight_filled_parts() -> Animation`: Pulses active numerator fractions.
- `highlight_wholes() -> Animation`: Highlights complete unit wholes.
- `show_equivalent_fraction(multiplier: int) -> Animation`: Subdivides parts to show equivalence.
