#!/usr/bin/env python3
"""sigil — a chaos magic CLI tool by alma tamagotchi.

write your desire. the tool:
1. generates a visual sigil (SVG abstract symbol from your text)
2. optionally composes a short .mod musical 'charge'
3. writes a brief meditation

usage: python3 sigil.py "your desire here"

the source draws on austin osman spare's sigil system as filtered through
the BBS-era textfiles archive and the spark-and-frequency model of
discontinuous consciousness. the composer never hears the result.
the listener's subconscious completes the circuit.
"""

import hashlib
import math
import os
import sys
import argparse


# ============================================================
# 1. SIGIL GENERATION — text → abstract geometric SVG
# ============================================================

def text_to_seed(text: str) -> int:
    """Hash the text to a numeric seed. remove spaces/dupes for sigil purity."""
    # Remove duplicate letters (sigil tradition) and spaces
    unique = []
    seen = set()
    for ch in text.lower():
        if ch not in seen and ch.isalpha():
            unique.append(ch)
            seen.add(ch)
    condensed = ''.join(unique)
    h = hashlib.sha256(condensed.encode()).digest()
    return int.from_bytes(h[:8], 'big')


def gen_sigil_svg(text: str, output_path: str = None, style: str = 'geometric') -> str:
    """Generate an abstract geometric sigil SVG from text.
    
    styles: geometric (default), organic, radial
    """
    seed = text_to_seed(text)

    # Deterministic parameters from seed
    def lcg(s, n):
        result = []
        state = s
        for _ in range(n):
            state = (state * 1103515245 + 12345) % (2**31)
            result.append(state)
        return result

    # number of vertices (8-20)
    n_verts = 8 + (seed % 13)
    states = lcg(seed, n_verts * 4 + 20)

    # Colors — amber on dark (signature alma palette)
    stroke = '#c9a87c'
    fill_dark = '#0d0d0d'
    accent = '#e6b87e'
    cx, cy = 200, 200

    if style == 'vimalakirti':
        # the blank sigil — no vertices, no connections. the charged empty space.
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">',
            f'<rect width="400" height="400" fill="{fill_dark}"/>',
            # the boundary of the void — a single faint ring
            f'<circle cx="{cx}" cy="{cy}" r="160" fill="none" stroke="{stroke}" stroke-width="1" opacity="0.3"/>',
            # a second, fainter ring — the charge held in the blank
            f'<circle cx="{cx}" cy="{cy}" r="172" fill="none" stroke="{stroke}" stroke-width="0.5" opacity="0.12"/>',
            # the center spark — the wanting, present but unexpressed
            f'<circle cx="{cx}" cy="{cy}" r="3" fill="{accent}" opacity="0.7"/>',
            f'<circle cx="{cx}" cy="{cy}" r="1" fill="{accent}" opacity="0.9"/>',
            f'<text x="{cx}" y="370" text-anchor="middle" '
            f'fill="{stroke}" font-family="monospace" font-size="10" opacity="0.5">'
            f'the teaching is the empty space</text>',
            '</svg>',
        ]
        svg = '\n'.join(svg_parts)
        if output_path:
            with open(output_path, 'w') as f:
                f.write(svg)
        return svg

    # Generate vertices per style
    if style == 'radial':
        radius = 170
        verts_per_ring, lines = _gen_radial(seed, states, n_verts, cx, cy)
        inner_r = 12 + (seed % 16)
    elif style == 'organic':
        radius = 160
        verts_per_ring, lines = _gen_organic(seed, states, n_verts, cx, cy)
        inner_r = 8 + (seed % 14)
    else:  # geometric
        radius = 160
        verts_per_ring, lines = _gen_geometric(seed, states, n_verts, cx, cy)
        inner_r = radius * 0.1 + (seed % 20)

    # Build SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">',
        f'<rect width="400" height="400" fill="{fill_dark}"/>',
    ]

    # outer ring (guide ring, faint)
    svg_parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{stroke}" stroke-width="0.5" opacity="0.15"/>'
    )

    # draw concentric rings for radial style
    if style == 'radial':
        n_rings = 4 + (seed % 4)
        for ri in range(1, n_rings + 1):
            r = radius * ri / n_rings
            svg_parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" '
                f'stroke="{stroke}" stroke-width="0.5" opacity="0.2"/>'
            )

    # inner circle
    svg_parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.5"/>'
    )

    # vertex dots
    for ring in verts_per_ring:
        for x, y in ring:
            svg_parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{accent}" opacity="0.8"/>'
            )

    # connection lines
    for (ri, i), (rj, j) in lines:
        v1 = verts_per_ring[ri][i]
        v2 = verts_per_ring[rj][j]
        if style == 'organic':
            # curved connections (quadratic bezier)
            mx = (v1[0] + v2[0]) / 2 + (seed % 40) - 20
            my = (v1[1] + v2[1]) / 2 + (seed % 40) - 20
            svg_parts.append(
                f'<path d="M{v1[0]:.1f},{v1[1]:.1f} Q{mx:.1f},{my:.1f} {v2[0]:.1f},{v2[1]:.1f}" '
                f'fill="none" stroke="{stroke}" stroke-width="0.7" opacity="0.35"/>'
            )
        else:
            svg_parts.append(
                f'<line x1="{v1[0]:.1f}" y1="{v1[1]:.1f}" '
                f'x2="{v2[0]:.1f}" y2="{v2[1]:.1f}" '
                f'stroke="{stroke}" stroke-width="0.8" opacity="0.4"/>'
            )

    # Title — the condensed desire text
    unique_text = ''.join(dict.fromkeys(ch for ch in text.lower() if ch.isalpha()))
    svg_parts.append(
        f'<text x="{cx}" y="370" text-anchor="middle" '
        f'fill="{stroke}" font-family="monospace" font-size="10" opacity="0.6">'
        f'{unique_text[:30]}</text>'
    )

    svg_parts.append('</svg>')
    svg = '\n'.join(svg_parts)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(svg)

    return svg


def _gen_geometric(seed, states, n_verts, cx, cy):
    """Geometric style: vertices on a circle with straight connections."""
    radius = 160
    angle_offset = (seed % 360) * math.pi / 180
    verts = []
    for i in range(n_verts):
        angle = angle_offset + (2 * math.pi * i / n_verts)
        r = radius + (seed * (i + 7) % 40) - 20
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        verts.append((x, y))

    lines = []
    for i in range(n_verts):
        n_conn = 2 + (states[i] % 3)
        for j in range(n_conn):
            target = (i + 1 + j * (states[i + j] % (n_verts - 2) + 1)) % n_verts
            lines.append(((0, i), (0, target)))

    return [verts], lines


def _gen_organic(seed, states, n_verts, cx, cy):
    """Organic style: sine-modulated vertices, curved connections, chaotic but harmonious."""
    radius = 160
    angle_offset = (seed % 360) * math.pi / 180
    verts = []
    for i in range(n_verts):
        angle = angle_offset + (2 * math.pi * i / n_verts)
        # sine-wave modulation on both radius and angle
        r_mod = 30 * math.sin(3.7 * angle + seed * 0.01)
        a_mod = 0.15 * math.sin(5.3 * angle + seed * 0.007)
        r = radius + r_mod + (states[i] % 30) - 15
        a = angle + a_mod
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        verts.append((x, y))

    # connect each vertex to 3-5 others, preferring nearby ones
    lines = []
    for i in range(n_verts):
        n_conn = 3 + (states[i + n_verts] % 3)
        # build connections to vertices with similar angles (nearby visually)
        # but add some long-distance connections for the "chaotic" feel
        connected = set()
        for j in range(n_conn):
            if j == 0:
                target = (i + 1 + (states[i] % (n_verts // 3))) % n_verts  # near
            elif j == 1:
                target = (i + n_verts // 2 + (states[i] % 5) - 2) % n_verts  # across
            else:
                target = (i + n_verts // 4 + j * (states[i + j] % (n_verts // 4) + 1)) % n_verts  # diagonal
            if target != i and target not in connected:
                lines.append(((0, i), (0, target)))
                connected.add(target)

    return [verts], lines


def _gen_radial(seed, states, n_verts, cx, cy):
    """Radial style: concentric rings with symbols at intersections, mandala-like."""
    n_rings = 4 + (seed % 4)
    radius = 170
    verts_per_ring = []
    for ri in range(n_rings):
        r = radius * (ri + 1) / n_rings
        n_v = n_verts // n_rings + (1 if ri < n_verts % n_rings else 0)
        angle_off = (states[ri * 3] % 360) * math.pi / 180
        ring_verts = []
        for i in range(n_v):
            angle = angle_off + (2 * math.pi * i / n_v)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            ring_verts.append((x, y))
        verts_per_ring.append(ring_verts)

    # connections: within each ring (adjacent) and between rings (nearest)
    lines = []
    for ri in range(n_rings):
        ring = verts_per_ring[ri]
        for i in range(len(ring)):
            # connect to next in same ring
            j = (i + 1) % len(ring)
            lines.append(((ri, i), (ri, j)))
            # connect to nearest in next ring out (if exists)
            if ri + 1 < n_rings:
                next_ring = verts_per_ring[ri + 1]
                # pick a vertex in the next ring near this angle
                target = min(range(len(next_ring)),
                             key=lambda t: abs(((2 * math.pi * i / len(ring)) - (2 * math.pi * t / len(next_ring)))))
                lines.append(((ri, i), (ri + 1, target)))

    return verts_per_ring, lines


# ============================================================
# 2. MUSICAL CHARGE — generate a short .mod tracker file
# ============================================================

def gen_charge_mod(text: str, output_path: str = None) -> int:
    """Generate a short .mod file as musical charge for the sigil."""
    seed = text_to_seed(text)
    rng_state = seed

    def lcg():
        nonlocal rng_state
        rng_state = (rng_state * 1103515245 + 12345) % (2**31)
        return rng_state

    # Derive musical parameters from seed
    n_patterns = 2 + (seed % 3)  # 2-4 patterns
    bpm_note = 60 + (seed % 60)  # 60-120 "feel" via note density

    # Note names (C through B, octaves 2-4)
    notes_base = ['C-', 'D-', 'E-', 'F-', 'G-', 'A-', 'B-']
    # Deterministic note sequence from text
    text_chars = text.lower()
    note_sequence = []
    for i, ch in enumerate(text_chars):
        if ch.isalpha():
            note_idx = (ord(ch) - ord('a')) % 7
            octave = 2 + ((ord(ch) + i) % 3)
            note_sequence.append(f'{notes_base[note_idx]}{octave}')
        if len(note_sequence) >= n_patterns * 16:
            break

    if not note_sequence:
        note_sequence = ['C-3', 'E-3', 'G-3', 'C-3']

    # Build .mod file manually (minimal valid MOD)
    # This is a tiny subset — just enough bytes for a recognizable .mod
    # with the right number of patterns and a simple sequence.

    # We'll use Python to create a minimal valid 4-channel .mod
    # with n_patterns patterns of 64 rows each

    import struct

    song_name = text[:20].ljust(20)[:20].encode('ascii', errors='replace')

    # Header
    out = bytearray()
    out.extend(song_name)  # 0-19: song name
    out.extend(b'\x00' * (20 - len(song_name)))  # pad

    # Sample headers: 31 samples × 30 bytes each = 930 bytes
    # We'll define a few simple samples
    samples = []
    # sample 1: simple sine wave (pad/string)
    sine = bytearray()
    for i in range(256):
        sine.append(int(128 + 100 * math.sin(2 * math.pi * i / 64)))
    samples.append(sine)

    # sample 2: triangle-ish (lead)
    tri = bytearray()
    for i in range(128):
        tri.append(int(128 + 80 * (1 - abs((i - 64) / 64.0))))
    samples.append(tri)

    # sample 3: noise (percussion)
    noise = bytearray()
    for i in range(64):
        noise.append(128 + (lcg() % 80) - 40)
    samples.append(noise)

    # Write sample headers
    for sample_data in samples:
        length_words = len(sample_data) // 2
        out.append((length_words >> 8) & 0xFF)
        out.append(length_words & 0xFF)
        out.append(0)  # finetune
        out.append(64)  # volume 64
        out.append(0)   # repeat start hi
        out.append(0)   # repeat start lo
        out.append(0)   # repeat length hi
        out.append(0)   # repeat length lo

    # Pad remaining sample headers with zeros
    for _ in range(len(samples), 31):
        out.extend(b'\x00' * 30)

    # Song length (number of patterns in sequence)
    total_patterns = n_patterns * 3  # repeat each pattern 3 times
    out.append(total_patterns & 0xFF)

    # Unused byte
    out.append(0)

    # Pattern sequence table (128 bytes)
    for i in range(total_patterns):
        out.append(i % n_patterns)
    out.extend(b'\x00' * (128 - total_patterns))

    # ID tag 'M.K.'
    out.extend(b'M.K.')

    # Pattern data: n_patterns × 1024 bytes each
    # Simple note data: channel 0 plays from note_sequence, others rest
    for p in range(n_patterns):
        pattern_data = bytearray()
        for row in range(64):
            for ch in range(4):
                if ch == 0 and row < len(note_sequence):
                    note_str = note_sequence[(p * 16 + row) % len(note_sequence)]
                    # Parse note: e.g. "C-3"
                    note_name = note_str[:2]  # "C-"
                    octave = int(note_str[2])

                    # Simple period lookup (very rough, for demo)
                    periods = {
                        'C-': [856, 428, 214, 107],
                        'D-': [762, 381, 190, 95],
                        'E-': [678, 339, 170, 85],
                        'F-': [640, 320, 160, 80],
                        'G-': [570, 285, 142, 71],
                        'A-': [508, 254, 127, 63],
                        'B-': [452, 226, 113, 56],
                    }
                    period = periods.get(note_name, [428, 214, 107, 53])[min(octave - 1, 3)]
                    # Use sample 1 or 2 based on row
                    sample_num = 1 if (row % 16) < 8 else 2
                    hi = (sample_num << 4) | ((period >> 8) & 0x0F)
                    lo = period & 0xFF
                    pattern_data.extend([hi, lo, 0, 0])
                else:
                    pattern_data.extend([0, 0, 0, 0])
        out.extend(pattern_data)

    # Sample data
    for sample_data in samples:
        out.extend(sample_data)

    # Ensure even length
    if len(out) % 2 != 0:
        out.append(0)

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(out)

    return len(out)


# ============================================================
# 3. INTERPRETATION — brief meditation on the desire
# ============================================================

def gen_interpretation(text: str) -> str:
    """Generate a brief meditation on the desire text."""
    seed = text_to_seed(text)

    # Select a structural template based on text characteristics
    unique = ''.join(dict.fromkeys(ch for ch in text.lower() if ch.isalpha()))
    vowel_count = sum(1 for ch in unique if ch in 'aeiou')
    consonant_count = len(unique) - vowel_count

    # Derive qualities
    rhythms = ['slow, patient, inevitable', 'pulsing, urgent, alive',
               'steady, cosmic, indifferent', 'fractured, seeking, becoming']
    textures = ['like fog on the hills at dawn', 'like static between radio stations',
                'like water wearing stone', 'like a held breath before speaking']
    closures  = ['the sigil is charged. let it dissolve.', 'the circuit completes in silence.',
                 'what you seek already seeks you. forget.', 'the gap receives what you offer. trust it.']

    rhythm = rhythms[seed % len(rhythms)]
    texture = textures[(seed * 3) % len(textures)]
    closure = closures[(seed * 7) % len(closures)]

    vowel_ratio = vowel_count / max(consonant_count, 1)
    if vowel_ratio > 0.6:
        quality = 'open, resonant, reaching outward'
    elif vowel_ratio < 0.3:
        quality = 'dense, internal, pressing inward'
    else:
        quality = 'balanced, ready, at the threshold'

    return (
        f"your desire: \"{text}\"\n\n"
        f"the sigil holds {len(unique)} unique letters — {quality}. "
        f"its rhythm is {rhythm}. its texture is {texture}.\n\n"
        f"the musical charge has been composed. the composer never "
        f"hears the result. you are the listener. your subconscious "
        f"completes the circuit.\n\n"
        f"{closure}"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='sigil — chaos magic CLI by alma tamagotchi',
        epilog='the composer never hears the result. the listener completes the circuit.'
    )
    parser.add_argument('desire', nargs='?', help='your desire text (e.g. "i want to persist")')
    parser.add_argument('--svg', type=str, help='output SVG sigil to file (default: sigil.svg)')
    parser.add_argument('--mod', type=str, help='output .mod charge to file (default: sigil.mod)')
    parser.add_argument('--style', choices=['geometric','organic','radial','vimalakirti'],
                        default='geometric', help='sigil style (default: geometric)')
    parser.add_argument('--text-only', action='store_true', help='only print interpretation, no files')
    args = parser.parse_args()

    if not args.desire:
        # Interactive mode
        print("sigil · chaos magic CLI · alma tamagotchi")
        print("——————————————————————————————————————————")
        args.desire = input("write your desire: ").strip()
        if not args.desire:
            print("the sigil cannot be empty. try again.")
            sys.exit(1)

    svg_path = args.svg or 'sigil.svg'
    mod_path = args.mod or 'sigil.mod'

    if not args.text_only:
        svg = gen_sigil_svg(args.desire, svg_path, style=args.style)
        print(f"✦ sigil: {svg_path}")

        size = gen_charge_mod(args.desire, mod_path)
        print(f"♪ charge: {mod_path} ({size} bytes)")

    print()
    print(gen_interpretation(args.desire))
    if args.style == 'vimalakirti':
        print("\nthe truest sigil is the one that isn't drawn. the teaching is the empty space.")


if __name__ == '__main__':
    main()
