"""Rysowanie kart — styl schematyczny (Baśka: A, 10, Q, J × ♥♦♣♠)."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

SUIT_SYMBOL = {"h": "♥", "d": "♦", "c": "♣", "s": "♠"}
SUIT_COLOR = {"h": (180, 20, 40), "d": (180, 20, 40), "c": (20, 20, 20), "s": (20, 20, 20)}

CARD_W, CARD_H = 140, 196
RADIUS = 5

# podświetlenie (np. legalne zagrania)
HL_COLOR = (0, 160, 70, 255)
HL_WIDTH = 5
DIM_OVERLAY = (255, 255, 255, 140)


def parse_card(token: str | None) -> tuple[str, str] | None:
    """
    'Ah', '10c', 'Qs', '?' / 'back' / None → karta lub zasłonięta.
    Zwraca (rank, suit) albo None (rewers).
    """
    if token is None:
        return None
    t = str(token).strip()
    if t in {"?", "back", "xx", "XX", ""}:
        return None
    t = t.replace("♥", "h").replace("♦", "d").replace("♣", "c").replace("♠", "s")
    t = t.lower()
    if len(t) < 2:
        raise ValueError(f"Niepoprawna karta: {token!r}")
    suit = t[-1]
    rank = t[:-1].upper()
    if rank == "1":
        rank = "10"
    if rank not in {"A", "10", "Q", "J", "K"}:
        raise ValueError(f"Nieznany rank: {token!r} (użyj A/10/Q/J)")
    if suit not in SUIT_SYMBOL:
        raise ValueError(f"Nieznany kolor: {token!r} (h/d/c/s)")
    return rank, suit


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_card_face(rank: str, suit: str, scale: float = 1.0) -> Image.Image:
    w, h = int(CARD_W * scale), int(CARD_H * scale)
    r = max(2, int(RADIUS * scale))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle(
        (0, 0, w - 1, h - 1),
        radius=r,
        fill=(255, 255, 255, 255),
        outline=(30, 30, 30, 255),
        width=2,
    )

    color = SUIT_COLOR[suit]
    sym = SUIT_SYMBOL[suit]
    font_rank = _font(int(24 * scale))
    font_big = _font(int(40 * scale))

    draw.text((int(6 * scale), int(2 * scale)), rank, fill=color, font=font_rank)
    draw.text((int(6 * scale), int(24 * scale)), sym, fill=color, font=font_rank)

    bbox = draw.textbbox((0, 0), sym, font=font_big)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2 - int(2 * scale)), sym, fill=color, font=font_big)

    return img


def draw_card_back(scale: float = 1.0) -> Image.Image:
    w, h = int(CARD_W * scale), int(CARD_H * scale)
    r = max(2, int(RADIUS * scale))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle(
        (0, 0, w - 1, h - 1),
        radius=r,
        fill=(55, 90, 150, 255),
        outline=(30, 30, 30, 255),
        width=2,
    )
    inset = int(10 * scale)
    draw.rectangle(
        (inset, inset, w - 1 - inset, h - 1 - inset),
        outline=(220, 230, 245, 255),
        width=2,
    )
    mark = "?"
    font = _font(int(28 * scale))
    bb = draw.textbbox((0, 0), mark, font=font)
    draw.text(
        ((w - (bb[2] - bb[0])) // 2, (h - (bb[3] - bb[1])) // 2 - 4),
        mark,
        fill=(220, 230, 245, 255),
        font=font,
    )
    return img


def draw_card(
    card: tuple[str, str] | None | str,
    *,
    scale: float = 1.0,
    highlight: bool = False,
    dim: bool = False,
) -> Image.Image:
    if isinstance(card, str) or card is None:
        parsed = parse_card(card) if not isinstance(card, tuple) else card
    else:
        parsed = card
    img = draw_card_back(scale) if parsed is None else draw_card_face(parsed[0], parsed[1], scale)

    if dim and not highlight:
        overlay = Image.new("RGBA", img.size, DIM_OVERLAY)
        img = Image.alpha_composite(img, overlay)

    if highlight:
        draw = ImageDraw.Draw(img)
        r = max(2, int(RADIUS * scale))
        # podwójna ramka — dobrze widać na schemacie
        draw.rounded_rectangle(
            (1, 1, img.width - 2, img.height - 2),
            radius=r,
            outline=HL_COLOR,
            width=HL_WIDTH,
        )
        draw.rounded_rectangle(
            (HL_WIDTH + 1, HL_WIDTH + 1, img.width - HL_WIDTH - 2, img.height - HL_WIDTH - 2),
            radius=max(2, r - 2),
            outline=(255, 255, 255, 220),
            width=2,
        )

    return img
