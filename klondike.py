import pygame
import sys
import random
import math
import time
import copy  # Geri alma (Undo) için derin kopyalama
import pickle  # Kaydetme (Save/Load) için ikili dosya sistemi

pygame.init()
pygame.mixer.init()  # Ses sistemi için başlatma

# --- Sabitler ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Renkler
BG_COLOR = (20, 100, 45)  # Koyu yeşil masa
BG_PATTERN = (18, 90, 40)
CARD_BG = (252, 248, 240)  # Krem kart rengi
CARD_BACK1 = (30, 60, 140)  # Kart arkası
CARD_BACK2 = (20, 40, 110)
RED_COLOR = (200, 30, 30)
BLACK_COLOR = (25, 25, 25)
GOLD = (220, 180, 60)
SHADOW = (0, 0, 0, 80)
EMPTY_SLOT = (15, 80, 35)
EMPTY_BORDER = (25, 120, 55)
HIGHLIGHT = (255, 255, 100, 120)
WIN_GOLD = (255, 215, 0)

CARD_W, CARD_H = 80, 112
CARD_RADIUS = 8
STACK_OFFSET_Y = 28  # Kapalı kart aralığı
OPEN_OFFSET_Y = 22  # Açık kart aralığı

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
SUIT_COLORS = {'♠': BLACK_COLOR, '♥': RED_COLOR, '♦': RED_COLOR, '♣': BLACK_COLOR}
RED_SUITS = {'♥', '♦'}
BLACK_SUITS = {'♠', '♣'}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Solitaire")
clock = pygame.time.Clock()

# Fontlar
try:
    font_card_rank = pygame.font.SysFont("segoeui", 22, bold=True)
    font_card_suit = pygame.font.SysFont("segoeui", 28)
    font_center_suit = pygame.font.SysFont("segoeui", 40)
    font_ui = pygame.font.SysFont("segoeui", 18)
    font_big = pygame.font.SysFont("segoeui", 52, bold=True)
    font_med = pygame.font.SysFont("segoeui", 26)
except:
    font_card_rank = pygame.font.Font(None, 24)
    font_card_suit = pygame.font.Font(None, 30)
    font_center_suit = pygame.font.Font(None, 42)
    font_ui = pygame.font.Font(None, 20)
    font_big = pygame.font.Font(None, 54)
    font_med = pygame.font.Font(None, 28)


# ─────────────────────────────────────────────
# KART ÇİZİMİ
# ─────────────────────────────────────────────
def draw_card(surface, x, y, rank, suit, face_up=True, highlight=False, alpha=255):
    """Tek bir kartı yüzey üzerine çizer."""
    shadow_surf = pygame.Surface((CARD_W + 4, CARD_H + 4), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 60), (0, 0, CARD_W + 4, CARD_H + 4), border_radius=CARD_RADIUS + 2)
    surface.blit(shadow_surf, (x + 3, y + 3))

    if not face_up:
        _draw_card_back(surface, x, y, alpha)
        return

    card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*CARD_BG, alpha), (0, 0, CARD_W, CARD_H), border_radius=CARD_RADIUS)
    pygame.draw.rect(card_surf, (200, 195, 185, alpha), (0, 0, CARD_W, CARD_H), 1, border_radius=CARD_RADIUS)

    color = SUIT_COLORS[suit]

    r_surf = font_card_rank.render(rank, True, color)
    s_surf = font_card_suit.render(suit, True, color)
    card_surf.blit(r_surf, (5, 2))
    card_surf.blit(s_surf, (4, 18))

    r_surf2 = font_card_rank.render(rank, True, color)
    s_surf2 = font_card_suit.render(suit, True, color)
    r_rot = pygame.transform.rotate(r_surf2, 180)
    s_rot = pygame.transform.rotate(s_surf2, 180)
    card_surf.blit(r_rot, (CARD_W - r_rot.get_width() - 5, CARD_H - r_rot.get_height() - 2))
    card_surf.blit(s_rot, (CARD_W - s_rot.get_width() - 4, CARD_H - s_rot.get_height() - 18))

    big = font_center_suit.render(suit, True, color)
    card_surf.blit(big, (CARD_W // 2 - big.get_width() // 2, CARD_H // 2 - big.get_height() // 2))

    if highlight:
        hl = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        pygame.draw.rect(hl, (255, 255, 100, 80), (0, 0, CARD_W, CARD_H), border_radius=CARD_RADIUS)
        card_surf.blit(hl, (0, 0))
        pygame.draw.rect(card_surf, (255, 220, 0), (0, 0, CARD_W, CARD_H), 2, border_radius=CARD_RADIUS)

    surface.blit(card_surf, (x, y))


def _draw_card_back(surface, x, y, alpha=255):
    surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(surf, (*CARD_BACK1, alpha), (0, 0, CARD_W, CARD_H), border_radius=CARD_RADIUS)
    for row in range(3, CARD_H - 3, 8):
        for col in range(3, CARD_W - 3, 8):
            pygame.draw.rect(surf, (*CARD_BACK2, alpha), (col, row, 6, 6), border_radius=2)
    pygame.draw.rect(surf, (200, 200, 255, alpha), (0, 0, CARD_W, CARD_H), 2, border_radius=CARD_RADIUS)
    surface.blit(surf, (x, y))


def draw_empty_slot(surface, x, y, label=''):
    pygame.draw.rect(surface, EMPTY_SLOT, (x, y, CARD_W, CARD_H), border_radius=CARD_RADIUS)
    pygame.draw.rect(surface, EMPTY_BORDER, (x, y, CARD_W, CARD_H), 2, border_radius=CARD_RADIUS)
    if label:
        t = font_ui.render(label, True, (40, 140, 70))
        surface.blit(t, (x + CARD_W // 2 - t.get_width() // 2, y + CARD_H // 2 - t.get_height() // 2))


# ─────────────────────────────────────────────
# ANIMASYON SİSTEMİ
# ─────────────────────────────────────────────
class AnimCard:
    def __init__(self, rank, suit, face_up, start, end, duration=0.35, on_done=None):
        self.rank = rank
        self.suit = suit
        self.face_up = face_up
        self.sx, self.sy = start
        self.ex, self.ey = end
        self.duration = duration
        self.elapsed = 0.0
        self.done = False
        self.on_done = on_done

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.done = True
            if self.on_done: self.on_done()

    def draw(self, surface):
        t = self.elapsed / self.duration
        t2 = 1 - (1 - t) ** 3
        x = self.sx + (self.ex - self.sx) * t2
        y = self.sy + (self.ey - self.sy) * t2
        arc = -30 * math.sin(t2 * math.pi)
        draw_card(surface, int(x), int(y) + int(arc), self.rank, self.suit, self.face_up)


class FlipAnim:
    def __init__(self, x, y, rank, suit, duration=0.25, on_done=None):
        self.x = x
        self.y = y
        self.rank = rank
        self.suit = suit
        self.duration = duration
        self.elapsed = 0.0
        self.done = False
        self.on_done = on_done

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.done = True
            if self.on_done: self.on_done()

    def draw(self, surface):
        t = self.elapsed / self.duration
        if t < 0.5:
            scale = 1.0 - t * 2
            face_up = False
        else:
            scale = (t - 0.5) * 2
            face_up = True
        w = max(2, int(CARD_W * scale))
        offset = (CARD_W - w) // 2
        tmp = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        draw_card(tmp, 0, 0, self.rank, self.suit, face_up)
        scaled = pygame.transform.scale(tmp, (w, CARD_H))
        surface.blit(scaled, (self.x + offset, self.y))


# ─────────────────────────────────────────────
# OYUN MANTIĞI
# ─────────────────────────────────────────────
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.face_up = False

    def color(self): return 'red' if self.suit in RED_SUITS else 'black'

    def rank_val(self): return RANKS.index(self.rank)


class Solitaire:
    def __init__(self):
        # Ses efekti yüklemesi
        try:
            self.card_sound = pygame.mixer.Sound("sound.wav")
        except:
            self.card_sound = None
            print("sound.wav bulunamadı, oyun sessiz çalışıyor.")

        self.reset()

    def reset(self):
        deck = [Card(r, s) for s in SUITS for r in RANKS]
        random.shuffle(deck)

        self.tableau = [[] for _ in range(7)]
        idx = 0
        for col in range(7):
            for row in range(col + 1):
                c = deck[idx]
                idx += 1
                c.face_up = (row == col)
                self.tableau[col].append(c)

        self.stock = deck[idx:]
        for c in self.stock: c.face_up = False
        self.waste = []
        self.foundations = [[] for _ in range(4)]

        self.drag_cards = []
        self.drag_src = None
        self.drag_offset = (0, 0)

        self.animations = []
        self.flip_anims = []

        self.moves = 0
        self.t_start = time.time()
        self.time_spent = 0.0
        self.won = False

        self.history = []  # Undo geçmişi

    def save_state(self):
        state = {
            'tableau': copy.deepcopy(self.tableau),
            'stock': copy.deepcopy(self.stock),
            'waste': copy.deepcopy(self.waste),
            'foundations': copy.deepcopy(self.foundations),
            'moves': self.moves,
            'time_spent': time.time() - self.t_start
        }
        self.history.append(state)

    def undo(self):
        if not self.history: return False
        state = self.history.pop()
        self.tableau = state['tableau']
        self.stock = state['stock']
        self.waste = state['waste']
        self.foundations = state['foundations']
        self.moves = state['moves']
        self.t_start = time.time() - state['time_spent']

        self.drag_cards = []
        self.drag_src = None
        self.animations = []
        self.flip_anims = []
        self.won = False
        return True

    def save_to_file(self, filename="save.dat"):
        try:
            current_state = {
                'tableau': self.tableau, 'stock': self.stock, 'waste': self.waste,
                'foundations': self.foundations, 'moves': self.moves,
                'time_spent': time.time() - self.t_start, 'history': self.history
            }
            with open(filename, "wb") as f:
                pickle.dump(current_state, f)
            return True
        except:
            return False

    def load_from_file(self, filename="save.dat"):
        try:
            with open(filename, "rb") as f:
                state = pickle.load(f)
            self.tableau = state['tableau']
            self.stock = state['stock']
            self.waste = state['waste']
            self.foundations = state['foundations']
            self.moves = state['moves']
            self.t_start = time.time() - state['time_spent']
            self.history = state.get('history', [])
            self.drag_cards = []
            self.drag_src = None
            self.animations = []
            self.flip_anims = []
            self._check_win()
            return True
        except:
            return False

    def stock_pos(self):
        return (self.tableau_col_x(0), 20)

    def waste_pos(self):
        return (self.tableau_col_x(1), 20)

    def foundation_pos(self, i):
        return (self.tableau_col_x(i + 3), 20)

    def tableau_col_x(self, col):
        return 30 + col * (CARD_W + 14)

    def tableau_card_y(self, col, idx):
        y = 160
        col_cards = self.tableau[col]
        for i in range(min(idx, len(col_cards))):
            c = col_cards[i]
            y += STACK_OFFSET_Y if not c.face_up else OPEN_OFFSET_Y
        return y

    def can_place_tableau(self, card, col):
        tc = self.tableau[col]
        if not tc: return card.rank == 'K'
        top = tc[-1]
        if not top.face_up: return False
        return (top.rank_val() - card.rank_val() == 1 and top.color() != card.color())

    def can_place_foundation(self, card, fi):
        fd = self.foundations[fi]
        if not fd: return card.rank == 'A'
        top = fd[-1]
        return (top.suit == card.suit and card.rank_val() - top.rank_val() == 1)

    def click_stock(self):
        self.save_state()

        if self.card_sound:
            self.card_sound.play()

        if self.stock:
            c = self.stock.pop()
            c.face_up = True
            sx, sy = self.stock_pos()
            ex, ey = self.waste_pos()

            def place():
                self.waste.append(c)

            self.animations.append(AnimCard(c.rank, c.suit, True, (sx, sy), (ex, ey), 0.3, place))
            self.moves += 1
        else:
            # --- ANIMASYONLU DESTE YENİLEME ---
            waste_cards = list(self.waste)
            self.waste.clear()  # Waste alanını hemen temizle ki üst üste binmesin

            sx, sy = self.waste_pos()
            ex, ey = self.stock_pos()

            # Kartları ters sırada (en üsttekinden başlayarak) sola doğru uçuruyoruz
            for idx, c in enumerate(reversed(waste_cards)):
                c.face_up = False  # Geri dönerken kartlar kapansın

                def return_to_stock(card=c):
                    self.stock.append(card)

                # Kartların bir şerit halinde akması için kademeli gecikme (delay) süresi uyguluyoruz
                anim_duration = 0.22 + (idx * 0.06)

                self.animations.append(
                    AnimCard(c.rank, c.suit, False, (sx, sy), (ex, ey), duration=anim_duration, on_done=return_to_stock)
                )
            self.moves += 1

    def start_drag(self, mx, my):
        for i in range(4):
            fx, fy = self.foundation_pos(i)
            if self.foundations[i] and fx <= mx < fx + CARD_W and fy <= my < fy + CARD_H:
                self.drag_cards = [self.foundations[i][-1]]
                self.drag_src = ('foundation', i)
                self.drag_offset = (mx - fx, my - fy)
                return

        wx, wy = self.waste_pos()
        if self.waste and wx <= mx < wx + CARD_W and wy <= my < wy + CARD_H:
            self.drag_cards = [self.waste[-1]]
            self.drag_src = ('waste',)
            self.drag_offset = (mx - wx, my - wy)
            return

        for col in range(7):
            tc = self.tableau[col]
            for idx in range(len(tc) - 1, -1, -1):
                c = tc[idx]
                if not c.face_up: continue
                cx = self.tableau_col_x(col)
                cy = self.tableau_card_y(col, idx)
                if cx <= mx < cx + CARD_W and cy <= my < cy + CARD_H:
                    self.drag_cards = tc[idx:]
                    self.drag_src = ('tableau', col, idx)
                    self.drag_offset = (mx - cx, my - cy)
                    return

    def end_drag(self, mx, my):
        if not self.drag_cards: return
        card = self.drag_cards[0]
        placed = False

        if len(self.drag_cards) == 1:
            for i in range(4):
                fx, fy = self.foundation_pos(i)
                if fx <= mx < fx + CARD_W and fy <= my < fy + CARD_H:
                    if self.can_place_foundation(card, i):
                        self.save_state()
                        self._remove_drag_src()
                        self.foundations[i].append(card)
                        placed = True
                        self.moves += 1
                        self._check_win()
                        break

        if not placed:
            for col in range(7):
                cx = self.tableau_col_x(col)
                tc = self.tableau[col]
                cy = self.tableau_card_y(col, len(tc) - 1) if tc else 160
                if cx <= mx < cx + CARD_W and cy - 20 <= my < cy + CARD_H:
                    if self.can_place_tableau(card, col):
                        self.save_state()
                        self._remove_drag_src()
                        self.tableau[col].extend(self.drag_cards)
                        placed = True
                        self.moves += 1
                        break

        self.drag_cards = []
        self.drag_src = None
        self._flip_uncovered()

    def _remove_drag_src(self):
        src = self.drag_src
        if src[0] == 'tableau':
            self.tableau[src[1]] = self.tableau[src[1]][:src[2]]
        elif src[0] == 'waste':
            self.waste.pop()
        elif src[0] == 'foundation':
            self.foundations[src[1]].pop()

    def _flip_uncovered(self):
        for col in range(7):
            tc = self.tableau[col]
            if tc and not tc[-1].face_up:
                c = tc[-1]
                cx = self.tableau_col_x(col)
                cy = self.tableau_card_y(col, len(tc) - 1)

                def flip_done(card=c): card.face_up = True

                self.flip_anims.append(FlipAnim(cx, cy, c.rank, c.suit, 0.28, flip_done))

    def _check_win(self):
        if all(len(f) == 13 for f in self.foundations): self.won = True

    def double_click(self, mx, my):
        card = None
        src = None
        wx, wy = self.waste_pos()
        if self.waste and wx <= mx < wx + CARD_W and wy <= my < wy + CARD_H:
            card = self.waste[-1]
            src = ('waste',)

        if card is None:
            for col in range(7):
                tc = self.tableau[col]
                if tc:
                    idx = len(tc) - 1
                    c = tc[idx]
                    if not c.face_up: continue
                    cx = self.tableau_col_x(col)
                    cy = self.tableau_card_y(col, idx)
                    if cx <= mx < cx + CARD_W and cy <= my < cy + CARD_H:
                        card = c
                        src = ('tableau', col, idx)
                        break

        if card is None: return

        for i in range(4):
            if self.can_place_foundation(card, i):
                self.save_state()
                if src[0] == 'waste':
                    self.waste.pop()
                else:
                    self.tableau[src[1]].pop()
                    self._flip_uncovered()

                if src[0] == 'waste':
                    sx, sy = self.waste_pos()
                else:
                    sx, sy = self.tableau_col_x(src[1]), self.tableau_card_y(src[1], src[2])

                ex, ey = self.foundation_pos(i)
                fi = i

                def place(c=card, idx=fi):
                    self.foundations[idx].append(c)
                    self._check_win()

                self.animations.append(AnimCard(card.rank, card.suit, True, (sx, sy), (ex, ey), 0.3, place))
                self.moves += 1
                return


# ─────────────────────────────────────────────
# GÖRSEL VE UI FONKSİYONLARI
# ─────────────────────────────────────────────
def draw_background(surface):
    surface.fill(BG_COLOR)
    for y in range(0, HEIGHT, 40):
        for x in range(0, WIDTH, 40):
            pygame.draw.rect(surface, BG_PATTERN, (x, y, 38, 38), border_radius=4)


def draw_custom_button(surface, rect, label):
    pygame.draw.rect(surface, (30, 110, 55), rect, border_radius=8)
    pygame.draw.rect(surface, (60, 180, 90), rect, 2, border_radius=8)
    text = font_ui.render(label, True, (220, 255, 220))
    surface.blit(text,
                 (rect.x + rect.width // 2 - text.get_width() // 2, rect.y + rect.height // 2 - text.get_height() // 2))


def draw_ui(surface, game):
    elapsed = int(time.time() - game.t_start)
    m, s = divmod(elapsed, 60)
    time_str = f"⏱ {m:02d}:{s:02d}"
    moves_str = f"🎯 {game.moves} hamle"

    t1 = font_ui.render(time_str, True, (200, 240, 200))
    t2 = font_ui.render(moves_str, True, (200, 240, 200))
    surface.blit(t1, (WIDTH - t1.get_width() - 16, 8))
    surface.blit(t2, (WIDTH - t2.get_width() - 16, 28))

    btn_y = HEIGHT - 48
    btn_w, btn_h = 104, 36

    undo_rect = pygame.Rect(30, btn_y, btn_w, btn_h)
    save_rect = pygame.Rect(30 + 115, btn_y, btn_w, btn_h)
    load_rect = pygame.Rect(30 + 230, btn_y, btn_w, btn_h)
    new_rect = pygame.Rect(WIDTH - 134, btn_y, btn_w, btn_h)

    draw_custom_button(surface, undo_rect, "Geri Al")
    draw_custom_button(surface, save_rect, "Kaydet")
    draw_custom_button(surface, load_rect, "Yükle")
    draw_custom_button(surface, new_rect, "Yeni Oyun")

    return undo_rect, save_rect, load_rect, new_rect


def draw_win_screen(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    t1 = font_big.render("Tebrikler! 🎉", True, WIN_GOLD)
    t2 = font_med.render("Oyunu Kazandınız!", True, (255, 255, 200))
    surface.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 70))
    surface.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 10))


def draw_game(surface, game):
    draw_background(surface)

    sx, sy = game.stock_pos()
    if game.stock:
        _draw_card_back(surface, sx, sy)
    else:
        draw_empty_slot(surface, sx, sy, '↺')

    wx, wy = game.waste_pos()
    if game.waste:
        draw_card(surface, wx, wy, game.waste[-1].rank, game.waste[-1].suit, True,
                  highlight=('waste',) == game.drag_src)
    else:
        draw_empty_slot(surface, wx, wy)

    for i, suit in enumerate(SUITS):
        fx, fy = game.foundation_pos(i)
        if game.foundations[i]:
            c = game.foundations[i][-1]
            draw_card(surface, fx, fy, c.rank, c.suit, True, highlight=game.drag_src == ('foundation', i))
        else:
            draw_empty_slot(surface, fx, fy, suit)

    drag_src = game.drag_src
    for col in range(7):
        tc = game.tableau[col]
        cx = game.tableau_col_x(col)
        if not tc: draw_empty_slot(surface, cx, 160, 'K'); continue
        for idx, c in enumerate(tc):
            cy = game.tableau_card_y(col, idx)
            if drag_src and drag_src[0] == 'tableau' and drag_src[1] == col and idx >= drag_src[2]: continue
            hl = (drag_src == ('tableau', col, idx))
            draw_card(surface, cx, cy, c.rank, c.suit, c.face_up, highlight=hl)

    if game.drag_cards:
        ox, oy = game.drag_offset
        mx, my = pygame.mouse.get_pos()
        bx = mx - ox
        by = my - oy
        for i, c in enumerate(game.drag_cards): draw_card(surface, bx, by + i * OPEN_OFFSET_Y, c.rank, c.suit, True)

    for a in game.animations: a.draw(surface)
    for f in game.flip_anims: f.draw(surface)

    if game.won: draw_win_screen(surface)

    return draw_ui(surface, game)


# ─────────────────────────────────────────────
# OYUN DÖNGÜSÜ
# ─────────────────────────────────────────────
def main():
    game = Solitaire()
    undo_rect = save_rect = load_rect = new_rect = pygame.Rect(0, 0, 0, 0)
    last_click_time, last_click_pos = 0, (0, 0)
    DOUBLE_CLICK_MS = 400

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if new_rect.collidepoint(mx, my):
                    game = Solitaire()
                    continue
                elif undo_rect.collidepoint(mx, my):
                    game.undo()
                    continue
                elif save_rect.collidepoint(mx, my):
                    game.save_to_file()
                    continue
                elif load_rect.collidepoint(mx, my):
                    game.load_from_file()
                    continue

                sx, sy = game.stock_pos()
                if sx <= mx < sx + CARD_W and sy <= my < sy + CARD_H:
                    game.click_stock()
                    continue

                now = pygame.time.get_ticks()
                if (now - last_click_time < DOUBLE_CLICK_MS and
                        abs(mx - last_click_pos[0]) < 10 and abs(my - last_click_pos[1]) < 10):
                    game.double_click(mx, my)
                    last_click_time = 0
                    continue
                last_click_time = now
                last_click_pos = (mx, my)

                if not game.won: game.start_drag(mx, my)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mx, my = event.pos
                if game.drag_cards: game.end_drag(mx, my)

        for a in game.animations[:]:
            a.update(dt)
            if a.done: game.animations.remove(a)
        for f in game.flip_anims[:]:
            f.update(dt)
            if f.done: game.flip_anims.remove(f)

        undo_rect, save_rect, load_rect, new_rect = draw_game(screen, game)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()