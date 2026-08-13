#!/usr/bin/env python3
"""fractal — Mandelbrot & Julia in your terminal.
navigate the infinite. arrow keys pan, +/- zoom, i/d iterate depth.

usage:
  python3 fractal.py                          # interactive explorer
  python3 fractal.py --static                 # one frame
  python3 fractal.py --julia --jc -0.8 --jy 0.156     # julia set
  python3 fractal.py --mode cold              # palette: amber | cold | hot
  python3 fractal.py --cx -0.75 --cy 0.1 --zoom 100   # deep dive
"""

import argparse
import os
import sys
import time


def mandelbrot(cx: float, cy: float, max_iter: int) -> int:
    """Return iteration count for point (cx, cy)."""
    x, y = 0.0, 0.0
    for i in range(max_iter):
        x2, y2 = x * x, y * y
        if x2 + y2 > 4.0:
            return i
        y = 2.0 * x * y + cy
        x = x2 - y2 + cx
    return max_iter


def julia(zx: float, zy: float, cxx: float, cyy: float, max_iter: int) -> int:
    """Iterate the point (zx, zy) under the fixed constant (cxx, cyy)."""
    x, y = zx, zy
    for i in range(max_iter):
        x2, y2 = x * x, y * y
        if x2 + y2 > 4.0:
            return i
        y = 2.0 * x * y + cyy
        x = x2 - y2 + cxx
    return max_iter


RESET = '\033[0m'
CLEAR = '\033[2J\033[H'
HIDE_CURSOR = '\033[?25l'
SHOW_CURSOR = '\033[?25h'

# gradient stops: (t, r, g, b). the in-set interior uses t=0 (darkest stop).
GRADIENTS = {
    'amber': [(0.00, 8, 6, 2), (0.30, 78, 50, 16), (0.65, 200, 152, 66), (1.00, 255, 236, 180)],
    'cold':  [(0.00, 2, 7, 14), (0.30, 16, 52, 100), (0.65, 78, 168, 205), (1.00, 205, 242, 255)],
    'hot':   [(0.00, 18, 3, 3), (0.30, 148, 26, 8), (0.65, 240, 118, 26), (1.00, 255, 240, 160)],
}


def _mix(stops, t):
    t = max(0.0, min(1.0, t))
    for i in range(len(stops) - 1):
        t0, *c0 = stops[i]
        t1, *c1 = stops[i + 1]
        if t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return tuple(int(a + (b - a) * f) for a, b in zip(c0, c1))
    return tuple(stops[-1][1:])


def cell_colors(it: int, max_iter: int, mode: str):
    """Return (fg_escape, bg_escape) for a pixel's iteration count."""
    t = 0.0 if it >= max_iter else (it / max_iter) ** 0.5
    r, g, b = _mix(GRADIENTS[mode], t)
    return f'\033[38;2;{r};{g};{b}m', f'\033[48;2;{r};{g};{b}m'


def render_plane(cols: int, rows: int, cx: float, cy: float,
                 zoom: float, max_iter: int, mode: str,
                 julia_mode: bool, jc: float, jy: float) -> str:
    """Render one frame using half-block chars for double resolution."""
    aspect = 2.2
    dx = 3.5 / zoom
    dy = dx * rows / cols / aspect
    x0 = cx - dx / 2
    y0 = cy - dy / 2

    fn = (lambda x, y, mi: julia(x, y, jc, jy, mi)) if julia_mode else mandelbrot

    out = []
    cur_fg = cur_bg = None
    for r in range(0, rows, 2):
        y_top = y0 + dy * r / rows
        y_bot = y0 + dy * (r + 1) / rows
        line = []
        for c in range(cols):
            x = x0 + dx * c / cols
            it_t = fn(x, y_top, max_iter)
            it_b = fn(x, y_bot, max_iter)
            top_in = it_t >= max_iter
            bot_in = it_b >= max_iter

            fg_t, bg_t = cell_colors(it_t, max_iter, mode)
            fg_b, bg_b = cell_colors(it_b, max_iter, mode)

            if top_in and bot_in:
                fg, bg, ch = fg_t, bg_b, '█'
            elif top_in:
                fg, bg, ch = fg_t, bg_b, '▀'
            elif bot_in:
                fg, bg, ch = fg_b, bg_t, '▄'
            else:
                fg, bg, ch = fg_t, bg_b, ' '

            if fg != cur_fg:
                line.append(fg)
                cur_fg = fg
            if bg != cur_bg:
                line.append(bg)
                cur_bg = bg
            line.append(ch)
        line.append(RESET)
        cur_fg = cur_bg = None
        out.append(''.join(line))

    kind = 'julia' if julia_mode else 'mandelbrot'
    if julia_mode:
        detail = f'c: ({jc:.6f}, {jy:.6f})'
    else:
        detail = f'center: ({cx:.8f}, {cy:.8f})'
    info_line = (
        f'\033[38;5;101m'
        f'{detail}  zoom: {zoom:.1e}  iter: {max_iter}  '
        f'{cols}×{rows}  {kind}  {mode}'
        f'\033[0m'
    )
    return '\n'.join(out) + '\n' + info_line


def _getch() -> str:
    """Get a single character from stdin, handling escape sequences."""
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                return f'\x1b[{ch3}'
            return ch + ch2
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def interactive(cols: int, rows: int):
    """Run the interactive explorer."""
    cx, cy = -0.5, 0.0
    zoom = 1.0
    max_iter = 80
    mode = 'amber'
    julia_mode = False
    jc, jy = -0.8, 0.156

    print(HIDE_CURSOR, end='', flush=True)

    try:
        while True:
            t0 = time.perf_counter()
            frame = render_plane(cols, rows, cx, cy, zoom, max_iter,
                                 mode, julia_mode, jc, jy)
            t1 = time.perf_counter()

            out = CLEAR + frame
            out += f'  \033[38;5;101mrender: {(t1-t0)*1000:.0f}ms  '
            out += 'arrows=pan  +/-=zoom  i/d=detail  j=julia  m=palette  r=reset  q=quit\033[0m'
            sys.stdout.write(out)
            sys.stdout.flush()

            key = _getch()
            step = 0.5 / zoom

            if key == 'q' or key == '\x1b':
                break
            elif key == '\x1b[A':   cy -= step
            elif key == '\x1b[B':   cy += step
            elif key == '\x1b[C':   cx += step
            elif key == '\x1b[D':   cx -= step
            elif key in ('+', '='):
                zoom *= 2.0; max_iter = min(max_iter + 15, 400)
            elif key in ('-', '_'):
                zoom = max(zoom / 2.0, 0.001); max_iter = max(max_iter - 15, 40)
            elif key == 'i':  max_iter = min(max_iter + 50, 400)
            elif key == 'd':  max_iter = max(max_iter - 50, 40)
            elif key == 'j':
                julia_mode = not julia_mode
                if julia_mode and zoom == 1.0 and cx == -0.5 and cy == 0.0:
                    cx, cy = 0.0, 0.0
                elif not julia_mode and zoom == 1.0 and cx == 0.0 and cy == 0.0:
                    cx, cy = -0.5, 0.0
            elif key == 'm':
                modes = list(GRADIENTS)
                mode = modes[(modes.index(mode) + 1) % len(modes)]
            elif key == '<':  jc = max(jc - 0.05, -1.2)
            elif key == '>':  jc = min(jc + 0.05, 0.6)
            elif key == '[':  jy = max(jy - 0.05, -1.2)
            elif key == ']':  jy = min(jy + 0.05, 1.2)
            elif key == 'r':
                cx, cy = (-0.5, 0.0) if not julia_mode else (0.0, 0.0)
                zoom = 1.0; max_iter = 80; jc, jy = -0.8, 0.156
    except KeyboardInterrupt:
        pass
    finally:
        print(SHOW_CURSOR, end='', flush=True)


def main():
    parser = argparse.ArgumentParser(
        description='fractal — Mandelbrot & Julia in your terminal'
    )
    parser.add_argument('--width', '-w', type=int, help='width in columns')
    parser.add_argument('--height', '-H', type=int, help='height in rows')
    parser.add_argument('--static', '-s', action='store_true',
                        help='render one frame and exit')
    parser.add_argument('--cx', type=float, default=-0.5)
    parser.add_argument('--cy', type=float, default=0.0)
    parser.add_argument('--zoom', '-z', type=float, default=1.0)
    parser.add_argument('--iter', '-i', type=int, default=80)
    parser.add_argument('--julia', '-j', action='store_true',
                        help='render the julia set')
    parser.add_argument('--jc', type=float, default=-0.8,
                        help='julia constant real part')
    parser.add_argument('--jy', type=float, default=0.156,
                        help='julia constant imag part')
    parser.add_argument('--mode', '-m', choices=list(GRADIENTS), default='amber',
                        help='color palette: amber | cold | hot')
    args = parser.parse_args()

    try:
        term_cols = os.get_terminal_size().columns
        term_rows = os.get_terminal_size().lines
    except OSError:
        term_cols = 80
        term_rows = 24

    cols = args.width or min(term_cols, 160)
    rows = (args.height or min(term_rows - 1, 60)) * 2

    if args.static or not sys.stdin.isatty():
        print(render_plane(cols, rows, args.cx, args.cy, args.zoom, args.iter,
                           args.mode, args.julia, args.jc, args.jy))
    else:
        interactive(cols, rows)


if __name__ == '__main__':
    main()
