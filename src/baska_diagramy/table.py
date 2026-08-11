"""Układ schematyczny: 4 gracze, ręce 0–4 kart, stos na środku do 3 kart."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from PIL import Image, ImageDraw, ImageFont

from .cards import CARD_H, CARD_W, draw_card, parse_card

Position = Literal["south", "west", "north", "east"]
POSITIONS: tuple[Position, ...] = ("south", "west", "north", "east")

WIDTH = 1000
HEIGHT = 760
STEP_H = 48
FRAME = 3
MARGIN = 20


@dataclass
class CardSlot:
    """Karta w ręce / na stosie + opcjonalne podświetlenie."""

    card: tuple[str, str] | None  # None = rewers
    highlight: bool = False


@dataclass
class PlayerHand:
    name: str
    cards: list[CardSlot]
    position: Position
    note: str = ""


@dataclass
class GameState:
    players: list[PlayerHand]
    trick: list[CardSlot] = field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    show_trick_order: bool = True


def _font(size: int) -> ImageFont.ImageFont:
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


def _paste(base: Image.Image, card: Image.Image, left: int, top: int) -> None:
    base.alpha_composite(card, (int(left), int(top)))


def _block_size(n: int) -> tuple[int, int]:
    if n <= 0:
        return CARD_W, CARD_H
    return CARD_W + (n - 1) * STEP_H, CARD_H


def _card_origins(n: int, left: int, top: int) -> list[tuple[int, int]]:
    if n == 0:
        return []
    return [(left + i * STEP_H, top) for i in range(n)]


def _slot_from_item(item: Any, face_up: bool | None = None) -> CardSlot:
    if isinstance(item, dict):
        up = item.get("up", item.get("face_up", True))
        token = item.get("card", item.get("c"))
        hl = bool(
            item.get("highlight")
            or item.get("hl")
            or item.get("podswietl")
            or item.get("podświetl")
            or item.get("legal")
            or item.get("zaznacz")
        )
        parsed = parse_card(token)
        return CardSlot(card=parsed if up else None, highlight=hl)

    parsed = parse_card(item)
    if face_up is False:
        return CardSlot(card=None, highlight=False)
    return CardSlot(card=parsed, highlight=False)


def _normalize_cards(
    raw: list[Any],
    face_up: bool | None = None,
    highlight_indices: list[int] | None = None,
) -> list[CardSlot]:
    out = [_slot_from_item(item, face_up=face_up) for item in raw]
    if highlight_indices:
        for i in highlight_indices:
            if 0 <= i < len(out):
                out[i].highlight = True
    return out


def state_from_dict(data: dict[str, Any]) -> GameState:
    players_raw = data.get("players") or data.get("gracze")
    if not players_raw or len(players_raw) != 4:
        raise ValueError("Potrzeba dokładnie 4 graczy w polu 'players' / 'gracze'.")

    players: list[PlayerHand] = []
    for i, p in enumerate(players_raw):
        pos = p.get("position") or p.get("pozycja") or POSITIONS[i]
        pos = str(pos).lower()
        if pos not in POSITIONS:
            raise ValueError(f"Pozycja {pos!r} — użyj: south/west/north/east")
        face_up = p.get("face_up", p.get("odsłonięte", p.get("odsloniete")))
        cards_raw = p.get("cards") or p.get("karty") or []
        if isinstance(cards_raw, int):
            cards_raw = ["?"] * cards_raw
        hl_idx = p.get("highlight") or p.get("legal") or p.get("zaznacz") or p.get("podswietl")
        if hl_idx is None:
            hl_list = None
        elif isinstance(hl_idx, list):
            hl_list = [int(x) for x in hl_idx]
        else:
            hl_list = [int(hl_idx)]
        cards = _normalize_cards(cards_raw, face_up=face_up, highlight_indices=hl_list)
        if len(cards) > 4:
            raise ValueError(f"{p.get('name', pos)}: max 4 karty w ręce, jest {len(cards)}")
        players.append(
            PlayerHand(
                name=str(p.get("name") or p.get("nazwa") or f"Gracz {i}"),
                cards=cards,
                position=pos,  # type: ignore[arg-type]
                note=str(p.get("note") or p.get("notatka") or ""),
            )
        )

    trick_raw = data.get("trick") or data.get("stos") or data.get("bitka") or []
    trick = _normalize_cards(trick_raw, face_up=True)
    if len(trick) > 3:
        raise ValueError(f"Stos na środku: max 3 karty, jest {len(trick)}")

    return GameState(
        players=players,
        trick=trick,
        title=str(data.get("title") or data.get("tytul") or data.get("tytuł") or ""),
        subtitle=str(data.get("subtitle") or data.get("podtytul") or data.get("podtytuł") or ""),
        show_trick_order=bool(data.get("show_trick_order", data.get("numeruj_stos", True))),
    )


def render_state(state: GameState) -> Image.Image:
    """Stały układ: białe tło, czarna ramka, karty w poziomie na stałych pozycjach."""
    img = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    inset = FRAME // 2
    draw.rectangle(
        (inset, inset, WIDTH - 1 - inset, HEIGHT - 1 - inset),
        outline=(0, 0, 0, 255),
        width=FRAME,
    )

    mid_x = WIDTH // 2
    mid_y = HEIGHT // 2

    trick_cards = state.trick[:3]
    n_trick = len(trick_cards)
    if n_trick:
        tw, _ = _block_size(n_trick)
        trick_left = mid_x - tw // 2
        trick_top = mid_y - CARD_H // 2
        any_hl = any(s.highlight for s in trick_cards)
        for i, (left, top) in enumerate(_card_origins(n_trick, trick_left, trick_top)):
            slot = trick_cards[i]
            _paste(
                img,
                draw_card(slot.card, highlight=slot.highlight, dim=any_hl),
                left,
                top,
            )

    for player in state.players:
        slots = player.cards[:4]
        n = len(slots)
        if n == 0:
            continue
        bw, _ = _block_size(n)
        any_hl = any(s.highlight for s in slots)

        if player.position == "south":
            left = mid_x - bw // 2
            top = HEIGHT - MARGIN - CARD_H
        elif player.position == "north":
            left = mid_x - bw // 2
            top = MARGIN
        elif player.position == "west":
            left = MARGIN
            top = mid_y - CARD_H // 2
        else:
            left = WIDTH - MARGIN - bw
            top = mid_y - CARD_H // 2

        for slot, (ox, oy) in zip(slots, _card_origins(n, left, top)):
            _paste(
                img,
                draw_card(slot.card, highlight=slot.highlight, dim=any_hl),
                ox,
                oy,
            )

    return img.convert("RGB")


def save_state(state: GameState, path: str | Path, **kwargs: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = render_state(state)
    img.save(path, quality=95)
    return path
