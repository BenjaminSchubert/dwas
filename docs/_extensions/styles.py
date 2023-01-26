import pygments
from pygments.styles import default, monokai
from pygments_ansi_color import color_tokens

fg_colors = bg_colors = {
    "Black": "#000000",
    "Red": "#EF2929",
    "Green": "#8AE234",
    "Yellow": "#FCE94F",
    "Blue": "#3465A4",
    "Magenta": "#c509c5",
    "Cyan": "#34E2E2",
    "White": "#ffffff",
}


class AnsiMonokaiStyle(monokai.MonokaiStyle):  # type: ignore
    styles = dict(monokai.MonokaiStyle.styles)
    styles.update(color_tokens(fg_colors, bg_colors))
    styles[pygments.token.Token.Color.Faint.Cyan] = "#0867AC"


class AnsiDefaultStyle(default.DefaultStyle):  # type: ignore
    styles = dict(default.DefaultStyle.styles)
    styles.update(color_tokens(fg_colors, bg_colors))
    styles[pygments.token.Token.Color.Faint.Cyan] = "#0867AC"
