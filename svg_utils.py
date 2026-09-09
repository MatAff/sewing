def x(x, dx, sx=1):
  return (x * sx - SHIFT_X + dx) * SCALE


def y(y, dy, sy=1):
  return (HEIGHT - SHIFT_Y - y * sy - dy) * SCALE