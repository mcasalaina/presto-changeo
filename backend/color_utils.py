"""
Color Utilities for Theme Palette Generation
Algorithmic color palette derivation from a single primary color.

Uses Python's colorsys module (stdlib) for color space conversions.
This is faster than LLM-generated colors and produces better color harmony.
"""

from colorsys import rgb_to_hls, hls_to_rgb


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a hex color string to RGB tuple.

    Args:
        hex_color: Hex color string, e.g., "#1E88E5" or "#ABC"

    Returns:
        Tuple of (red, green, blue) integers 0-255

    Examples:
        >>> hex_to_rgb("#1E88E5")
        (30, 136, 229)
        >>> hex_to_rgb("#ABC")
        (170, 187, 204)
    """
    # Remove '#' prefix if present
    hex_color = hex_color.lstrip("#")

    # Handle short hex format (#RGB -> #RRGGBB)
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)

    # Parse RGB values
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hex color string.

    Args:
        r: Red component 0-255
        g: Green component 0-255
        b: Blue component 0-255

    Returns:
        Hex color string with '#' prefix, e.g., "#1e88e5"

    Examples:
        >>> rgb_to_hex(30, 136, 229)
        '#1e88e5'
    """
    # Clamp values to 0-255 range
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    return f"#{r:02x}{g:02x}{b:02x}"


def derive_theme_palette(primary_hex: str) -> dict:
    """
    Derive a complete ModeTheme-compatible palette from a single primary color.

    The function analyzes the primary color's lightness to determine whether
    to use a light or dark background scheme, then generates complementary
    colors algorithmically.

    Args:
        primary_hex: Primary color as hex string, e.g., "#1E88E5"

    Returns:
        Dict with all ModeTheme fields:
        - primary: The input color (unchanged)
        - secondary: Complementary color (hue +180 degrees, slightly desaturated)
        - background: Light (#f8fafc) or dark (#1e293b) based on primary lightness
        - surface: White (#ffffff) or dark gray (#334155) based on primary lightness
        - text: Dark (#0f172a) or light (#f8fafc) based on primary lightness
        - text_muted: #64748b (works with both light/dark schemes)

    Examples:
        >>> derive_theme_palette("#1E88E5")  # Blue
        {'primary': '#1e88e5', 'secondary': '#e5881e', ...}  # Orange complement

        >>> derive_theme_palette("#000088")  # Dark blue
        {'primary': '#000088', 'background': '#1e293b', ...}  # Dark scheme
    """
    # Convert hex to RGB
    r, g, b = hex_to_rgb(primary_hex)

    # Convert to HLS (Hue, Lightness, Saturation)
    # colorsys uses 0-1 range for RGB
    h, l, s = rgb_to_hls(r / 255, g / 255, b / 255)

    # Calculate complementary color (hue +0.5 = +180 degrees)
    # Slightly desaturate for better harmony (80% saturation)
    comp_h = (h + 0.5) % 1.0
    comp_l = l
    comp_s = s * 0.8

    # Convert complementary back to RGB
    comp_r, comp_g, comp_b = hls_to_rgb(comp_h, comp_l, comp_s)
    secondary = rgb_to_hex(
        int(comp_r * 255),
        int(comp_g * 255),
        int(comp_b * 255)
    )

    # Determine light/dark scheme based on primary lightness
    # Threshold: lightness > 0.5 means primary is light, use light background
    use_light_scheme = l > 0.5

    # Select appropriate background colors
    if use_light_scheme:
        background = "#f8fafc"  # Slate 50 (light gray)
        surface = "#ffffff"     # White
        text = "#0f172a"        # Slate 900 (dark)
    else:
        background = "#1e293b"  # Slate 800 (dark)
        surface = "#334155"     # Slate 700 (dark gray)
        text = "#f8fafc"        # Slate 50 (light)

    # text_muted works well with both schemes
    text_muted = "#64748b"  # Slate 500

    return {
        "primary": primary_hex.lower() if primary_hex.startswith("#") else f"#{primary_hex}".lower(),
        "secondary": secondary,
        "background": background,
        "surface": surface,
        "text": text,
        "text_muted": text_muted,
    }
