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


class AnsiMonokaiStyle(monokai.MonokaiStyle):
    styles = dict(monokai.MonokaiStyle.styles)  # noqa: RUF012
    styles.update(color_tokens(fg_colors, bg_colors))
    styles[pygments.token.Token.Color.Faint.Cyan] = "#0867AC"


class AnsiDefaultStyle(default.DefaultStyle):
    styles = dict(default.DefaultStyle.styles)  # noqa: RUF012
    styles.update(color_tokens(fg_colors, bg_colors))
    styles[pygments.token.Token.Color.Faint.Cyan] = "#0867AC"
