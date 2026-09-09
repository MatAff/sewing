#@title SVG Functions

def x(x, dx, sx=1):
  return (x * sx - SHIFT_X + dx) * SCALE

def y(y, dy, sy=1):
  return (HEIGHT - SHIFT_Y - y * sy - dy) * SCALE

def path_string(points, color='ff0000', close_path=True, dx=0, dy=0, sx=1, sy=1):
  path_data = []
  path_data.append(f"M {x(points[0][0], dx, sx)} {y(points[0][1], dy, sy)}")
  for i in range(1, len(points)):
    path_data.append(f"L {x(points[i][0], dx, sx)} {y(points[i][1], dy, sy)}")
  if close_path:
    path_data.append("Z")  # Close the path
  return f'<path style="fill:none;stroke:#{color}" d="' + " ".join(path_data) + '" />'

def line_string(start, end, drop=False, dash=False, dx=0, dy=0, sx=1, sy=1):
  dash_array = 'stroke-dasharray="2 2"' if dash else ''
  if drop : return ''
  return f'<line x1="{x(start[0], dx, sx)}" y1="{y(start[1], dy, sy)}" x2="{x(end[0], dx, sx)}" y2="{y(end[1], dy, sy)}" stroke="black" stroke-width="1" {dash_array} />'

def line_list_string(line_list, dx=0, dy=0, sx=1, sy=1):
  return '\n'.join([line_string(*line, dash=True, dx=dx, dy=dy, sx=sx, sy=sy) for line in line_list])


def bezier_path_string(points_data, color='ff0000', close_path=True, dx=0, dy=0, sx=1, sy=1):
  """
  Generates an SVG path string with cubic Bézier curves, allowing each side of
  an anchor point to be directed separately using control handles.

  Args:
    points_data: An OrderedDict (key is point name, value is point data) or
                 A list of dictionaries, where each dictionary represents
                 an anchor point and its associated control handles.
                 Each dictionary must have an 'anchor' key (x, y tuple).
                 Optional keys are 'handle_out' (x, y tuple for the
                 first control point of the outgoing curve segment) and
                 'handle_in' (x, y tuple for the second control point of
                 the incoming curve segment). If 'handle_out' or 'handle_in'
                 are missing, they will default to the 'anchor' point,
                 resulting in a sharper corner or straight line segment.
    color: Hex color string for the path stroke.
    close_path: Boolean, if True, closes the path with a straight line from the
                last anchor point to the first anchor point using the 'Z' command.

  Returns:
    A string representing the SVG <path> element.
  """
  if isinstance(points_data, OrderedDict):
    points_with_handles = list(points_data.values())
  else:
    points_with_handles = points_data

  if not points_with_handles:
    return ""

  path_data = []

  # Start with M command for the first anchor point
  first_anchor_x, first_anchor_y = points_with_handles[0]['anchor']
  path_data.append(f"M {x(first_anchor_x, dx, sx)} {y(first_anchor_y, dy, sy)}")

  # Loop through segments to draw cubic Bézier curves
  # A segment connects points_with_handles[i] to points_with_handles[i+1]
  for i in range(len(points_with_handles) - 1):
    current_anchor_data = points_with_handles[i]
    next_anchor_data = points_with_handles[i+1]

    # First control point (outgoing handle from current anchor)
    # Defaults to current anchor if not specified, making a straight line segment if cp2 also defaults to anchor
    cp1x, cp1y = current_anchor_data.get('handle_out', current_anchor_data['anchor'])

    # Second control point (incoming handle to next anchor)
    # Defaults to next anchor if not specified, making a straight line segment if cp1 also defaults to anchor
    cp2x, cp2y = next_anchor_data.get('handle_in', next_anchor_data['anchor'])

    # End point of the curve (next anchor)
    end_anchor_x, end_anchor_y = next_anchor_data['anchor']

    path_data.append(
        f"C {x(cp1x, dx, sx)} {y(cp1y, dy, sy)}, "
        f"{(x(cp2x, dx, sx))} {y(cp2y, dy, sy)}, "
        f"{(x(end_anchor_x, dx, sx))} {y(end_anchor_y, dy, sy)}"
    )

  # Close the path with 'Z' command, which draws a straight line to the starting point.
  # If a curved closure is desired, the 'points_with_handles' list should include
  # explicit handles for the segment connecting the last and first points.
  if close_path:
    path_data.append("Z")

  return f'<path style="fill:none;stroke:#{color}" d="' + " ".join(path_data) + '" />'

def create_handle(point, angle_degrees, distance):
  angle_radians = math.radians(angle_degrees)
  handle_x = point[0] + distance * math.cos(angle_radians)
  handle_y = point[1] + distance * math.sin(angle_radians)
  return (handle_x, handle_y)

def create_anchor_with_handles(point, in_angle_degrees=0, in_distance=0, out_angle_degrees=0, out_distance=0):
  return {
      'anchor': point,
      'handle_in': create_handle(point, in_angle_degrees, in_distance),
      'handle_out': create_handle(point, out_angle_degrees, out_distance),
      'in_angle': in_angle_degrees,
      'in_distance': in_distance,
      'out_angle': out_angle_degrees,
      'out_distance': out_distance,
  }


import numpy as np

def intersect_bezier_and_line(p0, p1, p2, p3, line_start, line_end, epsilon=1e-9):
  """
  Finds the intersection points between a cubic Bezier curve and a line segment.

  Args:
    p0: The start anchor point of the Bezier curve (x, y).
    p1: The first control point of the Bezier curve (handle_out of p0) (x, y).
    p2: The second control point of the Bezier curve (handle_in of p3) (x, y).
    p3: The end anchor point of the Bezier curve (x, y).
    line_start: The start point of the line segment (x, y).
    line_end: The end point of the line segment (x, y).
    epsilon: A small value for floating point comparisons.

  Returns:
    A list of (x, y, t) tuples, each representing an intersection point and its
    corresponding 't' parameter on the Bezier curve.
  """
  intersections = []

  # 1. Translate and Rotate the coordinate system so line_start is at origin and line_end is on positive x-axis.
  # Translation vector
  tx, ty = -line_start[0], -line_start[1]

  # Apply translation to all points
  lp0 = (p0[0] + tx, p0[1] + ty)
  lp1 = (p1[0] + tx, p1[1] + ty)
  lp2 = (p2[0] + tx, p2[1] + ty)
  lp3 = (p3[0] + tx, p3[1] + ty)
  ll_end = (line_end[0] + tx, line_end[1] + ty) # Transformed line_end

  # Rotation angle
  line_length_sq = ll_end[0]**2 + ll_end[1]**2
  if line_length_sq < epsilon**2: # Line is a point, assume no intersection with a curve segment.
      return []

  angle = math.atan2(ll_end[1], ll_end[0]) # Angle of transformed line_end with positive x-axis
  cos_a = math.cos(-angle) # Rotate to align with x-axis
  sin_a = math.sin(-angle)

  # Apply rotation to all translated Bezier points
  rp0 = (lp0[0] * cos_a - lp0[1] * sin_a, lp0[0] * sin_a + lp0[1] * cos_a)
  rp1 = (lp1[0] * cos_a - lp1[1] * sin_a, lp1[0] * sin_a + lp1[1] * cos_a)
  rp2 = (lp2[0] * cos_a - lp2[1] * sin_a, lp2[0] * sin_a + lp2[1] * cos_a)
  rp3 = (lp3[0] * cos_a - lp3[1] * sin_a, lp3[0] * sin_a + lp3[1] * cos_a)

  # The transformed line segment is now (0,0) to (sqrt(line_length_sq), 0)
  transformed_line_max_x = math.sqrt(line_length_sq)

  # 2. Find roots of the y-component of the transformed Bezier curve.
  # The Bezier curve y-component is P_y(t) = (1-t)^3*rp0[1] + 3(1-t)^2*t*rp1[1] + 3(1-t)*t^2*rp2[1] + t^3*rp3[1]
  # Coefficients for the cubic polynomial a*t^3 + b*t^2 + c*t + d = 0
  d = rp0[1]
  c = 3 * (rp1[1] - rp0[1])
  b = 3 * (rp0[1] - 2 * rp1[1] + rp2[1])
  a = -rp0[1] + 3 * rp1[1] - 3 * rp2[1] + rp3[1]

  # Solve the cubic equation for t
  roots = np.roots([a, b, c, d])

  # 3. Filter valid 't' values and check x-component.
  for t_val in roots:
    # Only consider real roots within [0, 1] (with epsilon tolerance)
    if np.isreal(t_val) and -epsilon <= t_val <= 1.0 + epsilon:
      t_val_real = np.real(t_val)
      # Clamp t_val_real to [0, 1] to handle epsilon-based boundaries properly
      t_val_real = max(0.0, min(1.0, t_val_real))

      # Calculate the corresponding point on the original Bezier curve using the existing helper
      intersect_point_on_bezier = _bezier_point(t_val_real, p0, p1, p2, p3)

      # Calculate its x-coordinate in the transformed system to check if it's on the line segment
      x_in_transformed = (1-t_val_real)**3 * rp0[0] + \
                         3 * (1-t_val_real)**2 * t_val_real * rp1[0] + \
                         3 * (1-t_val_real) * t_val_real**2 * rp2[0] + \
                         t_val_real**3 * rp3[0]

      if -epsilon <= x_in_transformed <= transformed_line_max_x + epsilon:
        # This means the intersection is on the line segment
        intersections.append((*intersect_point_on_bezier, t_val_real))

  # Remove potential duplicate intersection points due to floating point inaccuracies
  unique_intersections = []
  for p_xyz in intersections:
      # Round to a certain precision before checking for uniqueness. Exclude t for uniqueness check.
      rounded_p = (round(p_xyz[0], 6), round(p_xyz[1], 6))
      if rounded_p not in [(round(up_xyz[0], 6), round(up_xyz[1], 6)) for up_xyz in unique_intersections]:
          unique_intersections.append(p_xyz)

  return unique_intersections


import math

def rotate_by_angle(center, point, angle_radians):
  """
  Rotates a 'point' around a 'center' by a given angle (in radians).

  Args:
    center: A tuple (cx, cy) representing the center point.
    point: A tuple (px, py) representing the point to be rotated.
    angle_radians: A float, the angle in radians by which to rotate the point.

  Returns:
    A tuple (new_px, new_py) representing the rotated point.
  """
  cx, cy = center
  px, py = point

  # Translate point so center is at origin
  translated_x = px - cx
  translated_y = py - cy

  # Perform rotation
  rotated_x = translated_x * math.cos(angle_radians) - translated_y * math.sin(angle_radians)
  rotated_y = translated_x * math.sin(angle_radians) + translated_y * math.cos(angle_radians)

  # Translate point back
  new_px = rotated_x + cx
  new_py = rotated_y + cy

  return (new_px, new_py)

def rotate_point_by_distance(center, point, distance_along_circumference):
  cx, cy = center
  px, py = point

  # Calculate vector from center to point
  vx = px - cx
  vy = py - cy

  current_distance = math.sqrt(vx**2 + vy**2)

  if current_distance == 0:
    return center

  angle_to_rotate = distance_along_circumference / current_distance

  # Translate point so center is at origin
  translated_x = px - cx
  translated_y = py - cy

  # Perform rotation
  rotated_x = translated_x * math.cos(angle_to_rotate) - translated_y * math.sin(angle_to_rotate)
  rotated_y = translated_x * math.sin(angle_to_rotate) + translated_y * math.cos(angle_to_rotate)

  # Translate point back
  new_px = rotated_x + cx
  new_py = rotated_y + cy

  return (new_px, new_py), angle_to_rotate

def compute_line_length(start, end):
  x1, y1 = start
  x2, y2 = end
  return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def distance_along_line(start, end, distance):
  x1, y1 = start
  x2, y2 = end

  # Calculate the vector from start to end
  vx = x2 - x1
  vy = y2 - y1

  line_length = math.sqrt(vx**2 + vy**2)

  if line_length == 0:
    return start # Start and end are the same, no movement possible
  if distance >= line_length:
    return end   # If distance is beyond the end, return the end point
  if distance <= 0:
    return start # If distance is negative or zero, return the start point

  ratio = distance / line_length
  new_x = x1 + vx * ratio
  new_y = y1 + vy * ratio

  return (new_x, new_y)


def proportion_along_line(start, end, proportion):
  line_length = compute_line_length(start, end)
  return distance_along_line(start, end, proportion * line_length)


def middle_between_points(p1, p2):
  return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def _bezier_point(t, p0, p1, p2, p3):
  """
  Calculates a point on a cubic Bézier curve at parameter t.
  """
  one_minus_t = 1 - t
  return (
      one_minus_t**3 * p0[0] + 3 * one_minus_t**2 * t * p1[0] + 3 * one_minus_t * t**2 * p2[0] + t**3 * p3[0],
      one_minus_t**3 * p0[1] + 3 * one_minus_t**2 * t * p1[1] + 3 * one_minus_t * t**2 * p2[1] + t**3 * p3[1]
  )

def calculate_bezier_path_length(points_with_handles, num_segments=100):
  """
  Calculates the approximate total length of a Bézier path.

  Args:
    points_with_handles: A list of dictionaries, where each dictionary represents
                         an anchor point and its associated control handles.
                         Each dictionary must have an 'anchor' key (x, y tuple).
                         Optional keys are 'handle_out' (x, y tuple for the
                         first control point of the outgoing curve segment) and
                         'handle_in' (x, y tuple for the second control point of
                         the incoming curve segment).
    num_segments: The number of linear subdivisions to use for approximating
                  the length of each Bézier curve segment.

  Returns:
    A float, the approximate total length of the Bézier path.
  """
  total_bezier_length = 0
  if len(points_with_handles) < 2:
    return total_bezier_length

  for i in range(len(points_with_handles) - 1):
    current_anchor_data = points_with_handles[i]
    next_anchor_data = points_with_handles[i+1]

    p0 = current_anchor_data['anchor']
    p1 = current_anchor_data.get('handle_out', p0)
    p2 = next_anchor_data.get('handle_in', next_anchor_data['anchor'])
    p3 = next_anchor_data['anchor']

    # Approximate the length of this single Bézier segment
    segment_length = 0
    prev_point = p0
    for j in range(1, num_segments + 1):
      t = j / num_segments
      current_point = _bezier_point(t, p0, p1, p2, p3)
      segment_length += math.sqrt((current_point[0] - prev_point[0])**2 + (current_point[1] - prev_point[1])**2)
      prev_point = current_point
    total_bezier_length += segment_length

  return total_bezier_length

def angle_between_three_points(start_point, mid_point, end_point):
  """Return the angle between the paths at the mid point using three simple points"""
  # Vector from mid_point to start_point
  vec1_x = start_point[0] - mid_point[0]
  vec1_y = start_point[1] - mid_point[1]

  # Vector from mid_point to end_point
  vec2_x = end_point[0] - mid_point[0]
  vec2_y = end_point[1] - mid_point[1]

  # Calculate dot product
  dot_product = vec1_x * vec2_x + vec1_y * vec2_y

  # Calculate magnitudes
  magnitude1 = math.sqrt(vec1_x**2 + vec1_y**2)
  magnitude2 = math.sqrt(vec2_x**2 + vec2_y**2)

  # Avoid division by zero
  if magnitude1 == 0 or magnitude2 == 0:
    return 0.0

  # Calculate cosine of the angle
  cos_angle = dot_product / (magnitude1 * magnitude2)

  # Ensure cos_angle is within [-1, 1] due to floating point inaccuracies
  cos_angle = max(-1.0, min(1.0, cos_angle))

  # Calculate angle in radians and convert to degrees
  angle_radians = math.acos(cos_angle)
  angle_degrees = math.degrees(angle_radians)

  return angle_degrees


def bezier_path_angle_between_mid_point(start_anchor_data, mid_anchor_data, end_anchor_data):
  """
  Calculates the angle at the 'mid_anchor_data' point between two connected Bézier segments.
  The angle is derived from the tangent vectors of the incoming and outgoing curve segments.

  Args:
    start_anchor_data: Dictionary for the preceding anchor point in the path.
    mid_anchor_data: Dictionary for the anchor point at which to calculate the angle.
    end_anchor_data: Dictionary for the succeeding anchor point in the path.

  Returns:
    A float, the angle in degrees between the tangent vectors at the mid_anchor_data.
  """

  # Extract anchor points
  mid_anchor_point = mid_anchor_data['anchor']

  # --- Calculate tangent for the incoming segment (from start_anchor_data to mid_anchor_data) ---
  # P0_in = start_anchor_data['anchor']
  # P1_in = start_anchor_data.get('handle_out', P0_in)
  P2_in = mid_anchor_data.get('handle_in', mid_anchor_point) # This is the second control point for the incoming segment
  P3_in = mid_anchor_point # This is the end anchor point of the incoming segment

  # Tangent vector at t=1 for the incoming segment is 3 * (P3_in - P2_in)
  vec1_x = P3_in[0] - P2_in[0]
  vec1_y = P3_in[1] - P2_in[1]

  # --- Calculate tangent for the outgoing segment (from mid_anchor_data to end_anchor_data) ---
  P0_out = mid_anchor_point # This is the start anchor point of the outgoing segment
  P1_out = mid_anchor_data.get('handle_out', P0_out) # This is the first control point for the outgoing segment
  # P2_out = end_anchor_data.get('handle_in', end_anchor_data['anchor'])
  # P3_out = end_anchor_data['anchor']

  # Tangent vector at t=0 for the outgoing segment is 3 * (P1_out - P0_out)
  vec2_x = P1_out[0] - P0_out[0]
  vec2_y = P1_out[1] - P0_out[1]

  # Calculate dot product
  dot_product = vec1_x * vec2_x + vec1_y * vec2_y

  # Calculate magnitudes
  magnitude1 = math.sqrt(vec1_x**2 + vec1_y**2)
  magnitude2 = math.sqrt(vec2_x**2 + vec2_y**2)

  # Avoid division by zero
  if magnitude1 == 0 or magnitude2 == 0:
    return 0.0 # Or raise an error, depending on desired behavior for degenerate cases

  # Calculate cosine of the angle
  cos_angle = dot_product / (magnitude1 * magnitude2)

  # Ensure cos_angle is within [-1, 1] due to floating point inaccuracies
  cos_angle = max(-1.0, min(1.0, cos_angle))

  # Calculate angle in radians and convert to degrees
  angle_radians = math.acos(cos_angle)
  angle_degrees = math.degrees(angle_radians)

  return angle_degrees


# Helper function to normalize a vector
def _normalize_vector(vec):
    length = math.sqrt(vec[0]**2 + vec[1]**2)
    if length == 0:
        return (0, 0)
    return (vec[0] / length, vec[1] / length)

# Helper function to get the normal vector (assuming a consistent outward direction)
def _get_outward_normal(tangent_vec):
    # For a tangent (tx, ty), a normal pointing to the "left" (counter-clockwise rotation
    # from the tangent direction) is (-ty, tx). This is typically outward for patterns
    # drawn in a general CCW direction or following a specific convention.
    return (-tangent_vec[1], tangent_vec[0])

def get_bezier_path_points_with_seam_allowence(bezier_path_points_dict, offset=0.25):
  offset_bezier_points = OrderedDict()
  points_list = list(bezier_path_points_dict.items())
  num_points = len(points_list)

  if num_points == 0:
    return OrderedDict()
  if num_points == 1:
    # If only one point, seam allowance is not well-defined for a path segment
    return bezier_path_points_dict

  for i in range(num_points):
    key, current_anchor_data = points_list[i]
    anchor_point = current_anchor_data['anchor']

    # Determine incoming tangent vector (from handle_in of current point)
    if i == 0: # First point of an open path, treat its outgoing handle as its "incoming" direction
      p0_out_first = anchor_point
      p1_out_first = current_anchor_data.get('handle_out', p0_out_first)
      vec_in_x_at_point = p1_out_first[0] - p0_out_first[0]
      vec_in_y_at_point = p1_out_first[1] - p0_out_first[1]
    else:
      p2_in_current = current_anchor_data.get('handle_in', anchor_point)
      vec_in_x_at_point = anchor_point[0] - p2_in_current[0]
      vec_in_y_at_point = anchor_point[1] - p2_in_current[1]

    # Determine outgoing tangent vector (from handle_out of current point)
    if i == num_points - 1: # Last point of an open path, treat its incoming handle as its "outgoing" direction
      p2_in_last = current_anchor_data.get('handle_in', anchor_point)
      p3_in_last = anchor_point
      vec_out_x_at_point = p3_in_last[0] - p2_in_last[0]
      vec_out_y_at_point = p3_in_last[1] - p2_in_last[1]
    else:
      p0_out_current = anchor_point
      p1_out_current = current_anchor_data.get('handle_out', p0_out_current)
      vec_out_x_at_point = p1_out_current[0] - p0_out_current[0]
      vec_out_y_at_point = p1_out_current[1] - p0_out_current[1]

    # Normalize tangent vectors
    norm_vec_in = _normalize_vector((vec_in_x_at_point, vec_in_y_at_point))
    norm_vec_out = _normalize_vector((vec_out_x_at_point, vec_out_y_at_point))

    # Calculate the effective tangent direction at the anchor point
    # For intermediate points, use the bisector of the angle between incoming and outgoing tangents.
    # For endpoints, use the single available tangent.
    final_tangent = (0, 0)
    if i == 0: # First point
        final_tangent = norm_vec_out
    elif i == num_points - 1: # Last point
        final_tangent = norm_vec_in
    else: # Intermediate points
        if norm_vec_in == (0,0) and norm_vec_out == (0,0):
            final_tangent = (0,0)
        elif norm_vec_in == (0,0):
            final_tangent = norm_vec_out
        elif norm_vec_out == (0,0):
            final_tangent = norm_vec_in
        else:
            # Sum of normalized tangents bisects the angle
            final_tangent_sum = (norm_vec_in[0] + norm_vec_out[0], norm_vec_in[1] + norm_vec_out[1])
            final_tangent = _normalize_vector(final_tangent_sum)

    # Calculate the normal vector at the anchor point
    normal_vec = _get_outward_normal(final_tangent)

    # Calculate offset deltas
    offset_x = normal_vec[0] * offset
    offset_y = normal_vec[1] * offset

    # Offset anchor point
    new_anchor = (anchor_point[0] + offset_x, anchor_point[1] + offset_y)

    # Offset handles (simplistic: move handles by the same normal vector as the anchor)
    # This maintains the relative position of the handle to its anchor, which is a common approximation
    # for seam allowance in some CAD systems.
    new_handle_in = (current_anchor_data['handle_in'][0] + offset_x, current_anchor_data['handle_in'][1] + offset_y)
    new_handle_out = (current_anchor_data['handle_out'][0] + offset_x, current_anchor_data['handle_out'][1] + offset_y)

    offset_bezier_points[key] = {
        'anchor': new_anchor,
        'handle_in': new_handle_in,
        'handle_out': new_handle_out,
    }

  return offset_bezier_points

def cm_to_inch(cm):
  return cm / 2.54

def inch_to_cm(inch):
  return inch * 2.54

def point_perpendicular_to_line(start, end, proportion, distance):
  """Given the start and end point of a line. Calculate a point along the line based on proportion, then calculate a point perpendicular to the line at the given distance from the line."""
  # 1. Calculate the point P on the line at the given proportion.
  point_on_line = proportion_along_line(start, end, proportion)

  # 2. Calculate the vector representing the line (end - start).
  line_vector_x = end[0] - start[0]
  line_vector_y = end[1] - start[1]

  # 3. Calculate the perpendicular vector to the line vector.
  # We can get a perpendicular vector (vx, vy) as (-vy, vx). This will give a consistent 'left' normal.
  perp_vector_x = -line_vector_y
  perp_vector_y = line_vector_x

  # 4. Normalize the perpendicular vector.
  perp_vector_length = math.sqrt(perp_vector_x**2 + perp_vector_y**2)

  if perp_vector_length == 0:
    # If the start and end points are the same, there's no line to be perpendicular to.
    # In this case, return the point on the line (which is start/end).
    return point_on_line

  normalized_perp_x = perp_vector_x / perp_vector_length
  normalized_perp_y = perp_vector_y / perp_vector_length

  # 5. Multiply the normalized perpendicular vector by the distance to get the offset vector.
  offset_x = normalized_perp_x * distance
  offset_y = normalized_perp_y * distance

  # 6. Add the offset vector to point P to get the final perpendicular point.
  final_point_x = point_on_line[0] + offset_x
  final_point_y = point_on_line[1] + offset_y

  return (final_point_x, final_point_y)

def vertical_distance_along_line(start, end, vertical_distance):
  """Compute a point along a line at a given vertical distance from the start point."""
  x1, y1 = start
  x2, y2 = end
  delta_y = y2 - y1
  t = vertical_distance / delta_y
  return proportion_along_line(start, end, t)

def _lerp(p_start, p_end, t):
    """Linearly interpolates between two points."""
    return (p_start[0] * (1 - t) + p_end[0] * t,
            p_start[1] * (1 - t) + p_end[1] * t)

def split_bezier_curve(p0, p1, p2, p3, t):
    """
    Splits a cubic Bezier curve into two segments at a given parameter t.

    Args:
      p0: The start anchor point of the Bezier curve (x, y).
      p1: The first control point of the Bezier curve (x, y).
      p2: The second control point of the Bezier curve (x, y).
      p3: The end anchor point of the Bezier curve (x, y).
      t: The parameter (0.0 to 1.0) at which to split the curve.

    Returns:
      A tuple containing two tuples of control points:
      ( (p0_seg1, p1_seg1, p2_seg1, p3_seg1), (p0_seg2, p1_seg2, p2_seg2, p3_seg2) )
    """
    if not (0.0 <= t <= 1.0):
        raise ValueError("Parameter t must be between 0.0 and 1.0")

    # First level interpolation
    p01 = _lerp(p0, p1, t)
    p12 = _lerp(p1, p2, t)
    p23 = _lerp(p2, p3, t)

    # Second level interpolation
    p012 = _lerp(p01, p12, t)
    p123 = _lerp(p12, p23, t)

    # Third level interpolation (the split point on the curve)
    split_point = _lerp(p012, p123, t)

    # Control points for the first segment
    segment1_p0 = p0
    segment1_p1 = p01
    segment1_p2 = p012
    segment1_p3 = split_point

    # Control points for the second segment
    segment2_p0 = split_point
    segment2_p1 = p123
    segment2_p2 = p23
    segment2_p3 = p3

    return ((segment1_p0, segment1_p1, segment1_p2, segment1_p3),
            (segment2_p0, segment2_p1, segment2_p2, segment2_p3))

def points_to_vector_and_distance(start_point, end_point):
  """
  Converts two points into a starting point, the angle of the vector, and the distance.

  Args:
    start_point: A tuple (x, y) representing the starting point.
    end_point: A tuple (x, y) representing the ending point.

  Returns:
    A tuple containing:
      - start_point: The original start point (x, y).
      - angle_degrees: The angle of the direction vector in degrees relative to the positive x-axis.
      - distance: The Euclidean distance between start_point and end_point.
  """
  distance = compute_line_length(start_point, end_point)

  if distance == 0:
    return start_point, 0.0, 0.0 # Angle is undefined if start and end are the same

  direction_x = (end_point[0] - start_point[0]) / distance
  direction_y = (end_point[1] - start_point[1]) / distance

  angle_radians = math.atan2(direction_y, direction_x)
  angle_degrees = math.degrees(angle_radians)

  return start_point, angle_degrees, distance

def split_bezier_curve_wrapper(start_anchor_data, end_anchor_data, line_start, line_end):

  # Extract Bezier control points from start_anchor_data and end_anchor_data
  p0_curve = start_anchor_data['anchor']
  p1_curve = start_anchor_data.get('handle_out', p0_curve)
  p2_curve = end_anchor_data.get('handle_in', end_anchor_data['anchor'])
  p3_curve = end_anchor_data['anchor']

  # Find intersection(s) using intersect_bezier_and_line
  intersections = intersect_bezier_and_line(p0_curve, p1_curve, p2_curve, p3_curve, line_start, line_end)

  # Handle no intersections
  if not intersections:
    return None, None, None

  # Select the first intersection point to split the curve
  intersection_point_data = intersections[0]
  intersection_x, intersection_y, t_split = intersection_point_data
  intersection_point = (intersection_x, intersection_y)

  # Split the Bezier curve at t_split using split_bezier_curve
  (segment1_points, segment2_points) = split_bezier_curve(p0_curve, p1_curve, p2_curve, p3_curve, t_split)
  p0_seg1, p1_seg1, p2_seg1, p3_seg1 = segment1_points # p3_seg1 is the intersection_point
  p0_seg2, p1_seg2, p2_seg2, p3_seg2 = segment2_points # p0_seg2 is the intersection_point

  # Construct start_point_dict
  # No incoming vector for the start point
  _, out_angle_degrees, out_distance = points_to_vector_and_distance(p0_seg1, p1_seg1)
  start_point_dict = create_anchor_with_handles(p0_curve, 0, 0, out_angle_degrees, out_distance)

  # Construct mid_point_dict
  _, in_angle_degrees, in_distance = points_to_vector_and_distance(p2_seg1, p3_seg1)
  _, out_angle_degrees, out_distance = points_to_vector_and_distance(p0_seg2, p1_seg2)
  mid_point_dict = create_anchor_with_handles(intersection_point, in_angle_degrees + 180, in_distance, out_angle_degrees, out_distance)

  # Construct end_point_dict
  # No outgoing vector for the end point
  _, in_angle_degrees, in_distance = points_to_vector_and_distance(p2_seg2, p3_seg2)
  end_point_dict = create_anchor_with_handles(p3_curve, in_angle_degrees + 180, in_distance, 0, 0)

  return start_point_dict, mid_point_dict, end_point_dict