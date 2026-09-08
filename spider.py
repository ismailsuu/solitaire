import pygame
import sys
import random
import math
import time
import copy
import pickle

pygame.init()
pygame.mixer.init()

# --- Sabitler ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Renkler
BG_COLOR = (20, 100, 45)  # Koyu yeşil masa
BG_PATTERN = (18, 90, 40)
CARD_BG = (252, 248, 240)
CARD_BACK1 = (30, 60, 140)
CARD_BACK2 = (20, 40, 110)
RED_COLOR = (200, 30, 30)
BLACK_COLOR = (25, 25, 25)
SHADOW = (0, 0, 0, 80)
EMPTY_SLOT = (15, 80, 35)
EMPTY_BORDER = (25, 120, 55)
WIN_GOLD = (255, 215, 0)

# Kart Boyutları (10 sütun sığması için 800x600 ekrana göre daraltıldı)
CARD_W, CARD_H = 68, 96
CARD_RADIUS = 5
STACK_OFFSET_Y = 10  # Kapalı kart aralığı
OPEN_OFFSET_Y = 18  # Açık kart aralığı

SUITS = ['♠'] # Sadece Maça ile Spider Solitaire (Kolay Mod)
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
SUIT_COLORS = {'♠': BLACK_COLOR, '♥': RED_COLOR, '♦': RED_COLOR, '♣': BLACK_COLOR}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spider Solitaire")
clock = pygame.time.Clock()

# Fontlar
try:
    font_card_rank = pygame.font.SysFont("segoeui", 20, bold=True)
    font_card_suit = pygame.font.SysFont("segoeui", 26)
    font_center_suit = pygame.font.SysFont("segoeui", 36)
    font_ui = pygame.font.SysFont("segoeui", 18)
    font_big = pygame.font.SysFont("segoeui", 52, bold=True)
    font_med = pygame.font.SysFont("segoeui", 26)
except:
    font_card_rank = pygame.font.Font(None, 22)
    font_card_suit = pygame.font.Font(None, 28)
    font_center_suit = pygame.font.Font(None, 38)
    font_ui = pygame.font.Font(None, 20)
    font_big = pygame.font.Font(None, 54)
    font_med = pygame.font.Font(None, 28)

# ─────────────────────────────────────────────
# KART ÇİZİMİ
# ─────────────────────────────────────────────
def draw_card(surface, x, y, rank, suit, face_up=True, highlight=False, alpha=255):
    shadow_surf = pygame.Surface((CARD_W + 4, CARD_H + 4), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 60), (0, 0, CARD_W + 4, CARD_H + 4), border_radius=CARD_RADIUS + 2)
    surface.blit(shadow_surf, (x + 2, y + 2))

    if not face_up:
        _draw_card_back(surface, x, y, alpha)
        return

    card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, (*CARD_BG, alpha), (0, 0, CARD_W, CARD_H), border_radius=CARD_RADIUS)
    pygame.draw.rect(card_surf, (200, 195, 185, alpha), (0, 0, CARD_W, CARD_H), 1, border_radius=CARD_RADIUS)

    color = SUIT_COLORS[suit]

    r_surf = font_card_rank.render(rank, True, color)
    s_surf = font_card_suit.render(suit, True, color)
    card_surf.blit(r_surf, (4, 2))
    card_surf.blit(s_surf, (3, 16))

    r_rot = pygame.transform.rotate(r_surf, 180)
    s_rot = pygame.transform.rotate(s_surf, 180)
    card_surf.blit(r_rot, (CARD_W - r_rot.get_width() - 4, CARD_H - r_rot.get_height() - 2))
    card_surf.blit(s_rot, (CARD_W - s_rot.get_width() - 3, CARD_H - s_rot.get_height() - 16))

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
    for row in range(3, CARD_H - 3, 6):
        for col in range(3, CARD_W - 3, 6):
            pygame.draw.rect(surf, (*CARD_BACK2, alpha), (col, row, 4, 4), border_radius=1)
    pygame.draw.rect(surf, (200, 200, 255, alpha), (0, 0, CARD_W, CARD_H), 2, border_radius=CARD_RADIUS)
    surface.blit(surf, (x, y))

def draw_empty_slot(surface, x, y):
    pygame.draw.rect(surface, EMPTY_SLOT, (x, y, CARD_W, CARD_H), border_radius=CARD_RADIUS)
    pygame.draw.rect(surface, EMPTY_BORDER, (x, y, CARD_W, CARD_H), 2, border_radius=CARD_RADIUS)

# ─────────────────────────────────────────────
# ANIMASYON SİSTEMİ
# ─────────────────────────────────────────────
class AnimCard:
    def __init__(self, rank, suit, face_up, start, end, duration=0.35, on_done=None, z_index=0):
        self.rank = rank
        self.suit = suit
        self.face_up = face_up
        self.sx, self.sy = start
        self.ex, self.ey = end
        self.duration = duration
        self.elapsed = 0.0
        self.done = False
        self.on_done = on_done
        self.z_index = z_index

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

    def rank_val(self): return RANKS.index(self.rank)

class SpiderSolitaire:
    def __init__(self):
        try:
            self.card_sound = pygame.mixer.Sound("sound.wav")
        except:
            self.card_sound = None

        self.reset()

    def reset(self):
        # 104 kart (8 tam set Maça)
        deck = [Card(r, '♠') for r in RANKS for _ in range(8)]
        random.shuffle(deck)

        self.tableau = [[] for _ in range(10)]
        idx = 0
        # İlk 4 sütuna 6 kart, kalan 6 sütuna 5 kart
        for col in range(10):
            num_cards = 6 if col < 4 else 5
            for row in range(num_cards):
                c = deck[idx]
                idx += 1
                c.face_up = (row == num_cards - 1)
                self.tableau[col].append(c)

        self.stock = deck[idx:] # 50 kart
        for c in self.stock: c.face_up = False
        
        self.completed_sets = 0

        self.drag_cards = []
        self.drag_src = None
        self.drag_offset = (0, 0)

        self.animations = []
        self.flip_anims = []

        self.moves = 0
        self.t_start = time.time()
        self.time_spent = 0.0
        self.won = False
        self.history = []

    def save_state(self):
        state = {
            'tableau': copy.deepcopy(self.tableau),
            'stock': copy.deepcopy(self.stock),
            'completed_sets': self.completed_sets,
            'moves': self.moves,
            'time_spent': time.time() - self.t_start
        }
        self.history.append(state)

    def undo(self):
        if not self.history: return False
        state = self.history.pop()
        self.tableau = state['tableau']
        self.stock = state['stock']
        self.completed_sets = state['completed_sets']
        self.moves = state['moves']
        self.t_start = time.time() - state['time_spent']

        self.drag_cards = []
        self.drag_src = None
        self.animations = []
        self.flip_anims = []
        self.won = False
        return True

    def save_to_file(self, filename="save2.dat"):
        try:
            state = {
                'tableau': self.tableau, 'stock': self.stock, 
                'completed_sets': self.completed_sets, 'moves': self.moves,
                'time_spent': time.time() - self.t_start, 'history': self.history
            }
            with open(filename, "wb") as f:
                pickle.dump(state, f)
            return True
        except:
            return False

    def load_from_file(self, filename="save2.dat"):
        try:
            with open(filename, "rb") as f:
                state = pickle.load(f)
            self.tableau = state['tableau']
            self.stock = state['stock']
            self.completed_sets = state['completed_sets']
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
        return (WIDTH - 120, HEIGHT - 130)

    def foundation_pos(self, i):
        return (30 + i * 20, HEIGHT - 130)

    def tableau_col_x(self, col):
        padding = (WIDTH - (10 * CARD_W)) // 11
        return padding + col * (CARD_W + padding)

    def tableau_card_y(self, col, idx):
        y = 60
        col_cards = self.tableau[col]
        for i in range(min(idx, len(col_cards))):
            c = col_cards[i]
            y += STACK_OFFSET_Y if not c.face_up else OPEN_OFFSET_Y
        return y

    def is_valid_sequence(self, cards):
        for i in range(len(cards) - 1):
            if cards[i].suit != cards[i+1].suit or cards[i].rank_val() != cards[i+1].rank_val() + 1:
                return False
        return True

    def can_place_tableau(self, card, col):
        tc = self.tableau[col]
        if not tc: return True
        top = tc[-1]
        return top.rank_val() == card.rank_val() + 1

    def click_stock(self):
        if not self.stock: return
        
        # Spider kuralları gereği genellikle boş sütun varken kağıt dağıtılamaz.
        if any(len(t) == 0 for t in self.tableau):
            return 
            
        self.save_state()
        if self.card_sound: self.card_sound.play()

        sx, sy = self.stock_pos()
        
        # 10 sütuna da birer kart dağıtılacak
        cards_to_deal = self.stock[-10:]
        self.stock = self.stock[:-10]
        
        for i, c in enumerate(reversed(cards_to_deal)):
            c.face_up = True
            ex = self.tableau_col_x(i)
            ey = self.tableau_card_y(i, len(self.tableau[i]))
            
            def place_card(col=i, card=c):
                self.tableau[col].append(card)
                self._check_complete_series(col)
                
            anim_duration = 0.2 + (i * 0.05)
            self.animations.append(
                AnimCard(c.rank, c.suit, True, (sx, sy), (ex, ey), duration=anim_duration, on_done=place_card)
            )
        self.moves += 1

    def start_drag(self, mx, my):
        for col in range(10):
            tc = self.tableau[col]
            for idx in range(len(tc)):
                c = tc[idx]
                if not c.face_up: continue
                
                if not self.is_valid_sequence(tc[idx:]):
                    continue
                    
                cx = self.tableau_col_x(col)
                cy = self.tableau_card_y(col, idx)
                
                if cx <= mx < cx + CARD_W and cy <= my < cy + CARD_H + (len(tc)-1-idx)*OPEN_OFFSET_Y:
                    clicked_idx = -1
                    for j in range(idx, len(tc)):
                        c_y = self.tableau_card_y(col, j)
                        h = CARD_H if j == len(tc) - 1 else OPEN_OFFSET_Y
                        if c_y <= my < c_y + h:
                            clicked_idx = j
                            break
                            
                    if clicked_idx != -1 and clicked_idx >= idx:
                        self.drag_cards = tc[idx:]
                        self.drag_src = ('tableau', col, idx)
                        c_cy = self.tableau_card_y(col, idx)
                        self.drag_offset = (mx - cx, my - c_cy)
                        return

    def end_drag(self, mx, my):
        if not self.drag_cards: return
        card = self.drag_cards[0]
        placed = False

        for col in range(10):
            cx = self.tableau_col_x(col)
            tc = self.tableau[col]
            cy = self.tableau_card_y(col, len(tc) - 1) if tc else 60
            
            if cx - 10 <= mx < cx + CARD_W + 10 and cy - 50 <= my < cy + CARD_H + 50:
                if self.can_place_tableau(card, col) and self.drag_src[1] != col:
                    self.save_state()
                    
                    src_col, src_idx = self.drag_src[1], self.drag_src[2]
                    self.tableau[src_col] = self.tableau[src_col][:src_idx]
                    
                    self.tableau[col].extend(self.drag_cards)
                    placed = True
                    self.moves += 1
                    
                    self._flip_uncovered(src_col)
                    self._check_complete_series(col)
                    break

        self.drag_cards = []
        self.drag_src = None

    def _flip_uncovered(self, col):
        tc = self.tableau[col]
        if tc and not tc[-1].face_up:
            c = tc[-1]
            cx = self.tableau_col_x(col)
            cy = self.tableau_card_y(col, len(tc) - 1)

            def flip_done(card=c): card.face_up = True
            self.flip_anims.append(FlipAnim(cx, cy, c.rank, c.suit, 0.28, flip_done))

    def _check_complete_series(self, col):
        tc = self.tableau[col]
        if len(tc) < 13: return
        
        last_13 = tc[-13:]
        if last_13[0].rank == 'K' and self.is_valid_sequence(last_13):
            self.completed_sets += 1
            
            fx, fy = self.foundation_pos(self.completed_sets - 1)
            
            self.tableau[col] = tc[:-13]
            
            for i, c in enumerate(last_13):
                sx = self.tableau_col_x(col)
                sy = self.tableau_card_y(col, len(tc) - 13 + i)
                
                self.animations.append(AnimCard(c.rank, c.suit, True, (sx, sy), (fx, fy), 0.4 + i*0.02, z_index=i))
            
            self._flip_uncovered(col)
            self._check_win()

    def _check_win(self):
        if self.completed_sets == 8: self.won = True


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
    surface.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2, rect.y + rect.height // 2 - text.get_height() // 2))

def draw_ui(surface, game):
    elapsed = int(time.time() - game.t_start)
    m, s = divmod(elapsed, 60)
    time_str = f"⏱ {m:02d}:{s:02d}"
    moves_str = f"🎯 {game.moves} hamle"

    t1 = font_ui.render(time_str, True, (200, 240, 200))
    t2 = font_ui.render(moves_str, True, (200, 240, 200))
    surface.blit(t1, (WIDTH - t1.get_width() - 16, 8))
    surface.blit(t2, (WIDTH - t2.get_width() - 16, 28))

    btn_y = 10
    btn_w, btn_h = 90, 32

    undo_rect = pygame.Rect(16, btn_y, btn_w, btn_h)
    save_rect = pygame.Rect(16 + 100, btn_y, btn_w, btn_h)
    load_rect = pygame.Rect(16 + 200, btn_y, btn_w, btn_h)
    new_rect = pygame.Rect(16 + 300, btn_y, btn_w, btn_h)

    draw_custom_button(surface, undo_rect, "Geri Al")
    draw_custom_button(surface, save_rect, "Kaydet")
    draw_custom_button(surface, load_rect, "Yükle")
    draw_custom_button(surface, new_rect, "Yeni Oyun")

    if any(len(t) == 0 for t in game.tableau) and len(game.stock) > 0:
        warn = font_ui.render("Kart dağıtmak için boş sütun olmamalı!", True, (255, 200, 100))
        surface.blit(warn, (WIDTH // 2 - warn.get_width() // 2, 20))

    return undo_rect, save_rect, load_rect, new_rect

def draw_win_screen(surface):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    t1 = font_big.render("Tebrikler! 🎉", True, WIN_GOLD)
    t2 = font_med.render("Spider Solitaire Kazandınız!", True, (255, 255, 200))
    surface.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT // 2 - 70))
    surface.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 + 10))

def draw_game(surface, game):
    draw_background(surface)

    undo_rect, save_rect, load_rect, new_rect = draw_ui(surface, game)

    sx, sy = game.stock_pos()
    if game.stock:
        piles = len(game.stock) // 10
        for i in range(piles):
            _draw_card_back(surface, sx + i*4, sy)
    else:
        draw_empty_slot(surface, sx, sy)

    for i in range(8):
        fx, fy = game.foundation_pos(i)
        if i < game.completed_sets:
            draw_card(surface, fx, fy, 'K', '♠', True)
        else:
            draw_empty_slot(surface, fx, fy)

    drag_src = game.drag_src
    for col in range(10):
        tc = game.tableau[col]
        cx = game.tableau_col_x(col)
        if not tc: draw_empty_slot(surface, cx, 60); continue
        
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
        for i, c in enumerate(game.drag_cards): 
            draw_card(surface, bx, by + i * OPEN_OFFSET_Y, c.rank, c.suit, True)

    for f in game.flip_anims: f.draw(surface)
    
    sorted_anims = sorted(game.animations, key=lambda a: a.z_index)
    for a in sorted_anims: a.draw(surface)

    if game.won: draw_win_screen(surface)

    return undo_rect, save_rect, load_rect, new_rect

# ─────────────────────────────────────────────
# OYUN DÖNGÜSÜ
# ─────────────────────────────────────────────
def main():
    game = SpiderSolitaire()
    undo_rect = save_rect = load_rect = new_rect = pygame.Rect(0, 0, 0, 0)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if new_rect.collidepoint(mx, my):
                    game = SpiderSolitaire()
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
                if sx <= mx < sx + CARD_W + 20 and sy <= my < sy + CARD_H:
                    game.click_stock()
                    continue

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
