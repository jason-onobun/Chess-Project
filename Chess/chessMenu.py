import pygame as p
import sys
import chessAI
import ChessMain
import random
import math

SCREEN_W, SCREEN_H = 762, 600
BG_DARK = (18, 12, 32)
BG_PANEL = (28, 30, 48)
ACCENT_GOLD = (245, 215, 170)
ACCENT_GOLD_DIM = (180, 130, 80)
ACCENT_PURPLE = (160, 110, 230)
ACCENT_PURPLE_DIM = (100, 60, 180)
WHITE = (235, 225, 255)
GREY = (180, 170, 200)


# bUTTON Colour
BTN_BG = (35, 25, 55)
BTN_HOVER = (55, 40, 85)
BTN_BORDER = ACCENT_PURPLE

DIFFICULTIES = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3,
    "Expert": 4,
}

DIFF_LABELS = list(DIFFICULTIES.keys())

def drawArcaneOverlay(screen):
    overlay = p.Surface((SCREEN_W, SCREEN_H), p.SRCALPHA)

    # Static stars / magical dust — positions are fixed, no more flickering
    for x, y, alpha in _STAR_POSITIONS:
        p.draw.circle(overlay, (220, 220, 255, alpha), (x, y), 1)
    
    # Very faint vertical mystical beams
    for x in range(0, SCREEN_W, 85):
        p.draw.line(overlay, (140, 100, 255, 8), (x, 0), (x, SCREEN_H), 2)
    
    screen.blit(overlay, (0, 0))


_STAR_POSITIONS = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H), 
                   random.randint(25, 75)) for _ in range(70)]






def drawButton(surface, rect, text, font,
               bg=BTN_BG, border=BTN_BORDER, textColor=WHITE,
               hovered=False, glow=False):
    color = tuple(min(c + 35, 255) for c in bg) if hovered else bg
    p.draw.rect(surface, color, rect, border_radius=12)

    if hovered or glow:
        glow_rect = rect.inflate(8, 8)
        s = p.Surface(glow_rect.size, p.SRCALPHA)
        p.draw.rect(s, (*ACCENT_PURPLE, 60), glow_rect, border_radius=16)
        surface.blit(s, glow_rect.topleft)

    p.draw.rect(surface, border, rect, width=3, border_radius=12)

    label = font.render(text, True, textColor)
    lx = rect.centerx - label.get_width() // 2
    ly = rect.centery - label.get_height() // 2
    surface.blit(label, (lx, ly))



def screenHome(surface, fonts, mouse, events):
    surface.fill(BG_DARK)
    drawArcaneOverlay(surface)

    title = fonts["title"].render("WIZARD'S CHESS", True, ACCENT_GOLD)
    title_shadow = fonts["title"].render("WIZARD'S CHESS", True, (80, 40, 120))
    surface.blit(title_shadow, (SCREEN_W // 2 - title_shadow.get_width() // 2 + 3, 168))
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 165))

    btnHuman = p.Rect(SCREEN_W // 2 - 170, 270, 340, 65) # button for human
    btnAI = p.Rect(SCREEN_W // 2 - 170, 355, 340, 65) # button for AI
    btnQuit = p.Rect(SCREEN_W // 2 - 70, 460, 140, 50)

    mx, my = mouse
    hH = btnHuman.collidepoint(mx, my)
    hA = btnAI.collidepoint(mx, my)
    hQ = btnQuit.collidepoint(mx, my)

    drawButton(surface, btnHuman, "Play vs Human", fonts["btn"], hovered=hH)
    drawButton(surface, btnAI, "Play vs AI",   fonts["btn"], hovered=hA)
    drawButton(surface, btnQuit, "Quit", fonts["btn"], 
               bg=(60, 20, 30), border=(190, 70, 70), hovered=hQ)

    for e in events:
        if e.type == p.MOUSEBUTTONDOWN and e.button == 1:
            if hH: return "human"
            if hA: return "ai"
            if hQ: p.quit(); sys.exit()
    return None

def screenAIOptions(surface, fonts, mouse, events, state):
    surface.fill(BG_DARK)
    drawArcaneOverlay(surface)

    # For the title

    title = fonts["heading"].render("GAME SETTINGS", True, ACCENT_GOLD)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 40))

    mx, my = mouse

    # To help the player choose their colour when playing against the AI
    secLabel = fonts["label"].render("CHOOSE YOUR COLOR", True, WHITE)
    surface.blit(secLabel, (SCREEN_W // 2 - secLabel.get_width() // 2, 115))

    colourOptions = [("White", "white"), ("Black", "black"), ("Random", "random")]
    colBtnW, colBtnH = 135, 52

    colStartX = SCREEN_W // 2 - (colBtnW * 3 + 24) // 2
    colBtnY = 155
    colRects = []
    for i, (label, val) in enumerate(colourOptions):
        r = p.Rect(colStartX + i * (colBtnW + 12), colBtnY, colBtnW, colBtnH)
        colRects.append((r, val))
        selected = (state["colour"] == val)
        bg = (70, 140, 100) if selected else BTN_BG
        border = (100, 220, 140) if selected else BTN_BG
        drawButton(surface, r, label, fonts["btn"], bg=bg, border=border, hovered=r.collidepoint(mx, my) and not selected)

    # Handling difficulty
    diffLabel = fonts["label"].render("DIFFICULTY", True, WHITE)
    surface.blit(diffLabel, (SCREEN_W // 2 - diffLabel.get_width() // 2, 235))

    diffBtnW, diffBtnH = 125, 52
    diffstartX = SCREEN_W // 2 - (diffBtnW * 4 + 30) // 2
    diffBtnY = 270
    diffRects = []
    for i, name in enumerate(DIFF_LABELS):
        r = p.Rect(diffstartX + i * (diffBtnW + 8), diffBtnY, diffBtnW, diffBtnH)
        diffRects.append(r)
        selected = (state["difficulty"] == i)
        bg = (70, 140, 100) if selected else BTN_BG
        border = (100, 220, 140) if selected else BTN_BORDER

        drawButton(surface, r, name, fonts["btn"], bg=bg, border=border, 
                   hovered=r.collidepoint(mx, my) and not selected)


            # Difficulty description

    depthVal = DIFFICULTIES[DIFF_LABELS[state["difficulty"]]]
    descriptions = {
        0: "Looks 1 Move ahead - great for beginners.",
        1: "Plays reasonably well; makes solid moves.",
        2: "Thinks 3 moves deep - a real challenge.",
        3: "Maximum depth - TOUGH fight. Much slower though.",}

    desc = fonts["small"].render(descriptions.get(state["difficulty"], ""), True, GREY)
    surface.blit(desc, (SCREEN_W // 2 - desc.get_width() // 2, 340))
    depthInfo = fonts["small"].render(f"(Search depth: {depthVal})", True, ACCENT_GOLD_DIM)
    surface.blit(depthInfo, (SCREEN_W // 2 - depthInfo.get_width() // 2, 365))

    btnStart = p.Rect(SCREEN_W // 2 + 30, 440, 190, 58)
    btnBack = p.Rect(SCREEN_W // 2 - 220, 445, 170, 58)


    hS = btnStart.collidepoint(mx, my)
    hB = btnBack.collidepoint(mx, my)

    drawButton(surface, btnStart, "BEGIN JOURNEY", fonts["btn"], bg=(80, 160, 100), border=(120, 200, 140), hovered=hS)
    drawButton(surface, btnBack, "<- Back", fonts["btn"], hovered=hB)


    for e in events:
        if e.type == p.MOUSEBUTTONDOWN and e.button == 1:
            for r, val in colRects:
                if r.collidepoint(mx, my):
                    state["colour"] = val
            for i, r in enumerate(diffRects):
                if r.collidepoint(mx, my):
                    state["difficulty"] = i
                    
            if hS: return "start"
            if hB: return "back"
    return None

def runMenu():
    p.init()
    screen = p.display.set_mode((SCREEN_W, SCREEN_H))
    p.display.set_caption("Wizard's Chess")
    clock = p.time.Clock()

    fonts = {
        "title": p.font.SysFont("Georgia", 68, bold=True),
        "heading": p.font.SysFont("Georgia", 42, bold=True),
        "btn": p.font.SysFont("Georgia", 20, bold=True),
        "label": p.font.SysFont("Georgia", 22, bold=True),
        "small": p.font.SysFont("Georgia", 18),
    }


    currentScreen = "home"

    aiSettings = {
        "colour": "white",
        "difficulty": 1,
    }


    while True:
        events = p.event.get()
        for e in events:
            if e.type == p.QUIT:
                p.quit()
                sys.exit()

        mouse = p.mouse.get_pos()

        screen.fill(BG_DARK)

        if currentScreen == "home":
            result = screenHome(screen, fonts, mouse, events)
            if result == "human":
                p.quit()
                ChessMain.main(playerOne=True, playerTwo=True)
                return
            elif result == "ai":
                currentScreen = "ai_options"

        elif currentScreen == "ai_options":
            result = screenAIOptions(screen, fonts, mouse, events, aiSettings)
            if result == "back":
                currentScreen ="home"
            elif result == "start":
                chessAI.DEPTH = DIFFICULTIES[DIFF_LABELS[aiSettings["difficulty"]]]

                colour = aiSettings["colour"]
                if colour == "random":
                    colour = random.choice(["white", "black"])

                if colour == "white":
                    playerOne, playerTwo = True, False

                else:
                    playerOne, playerTwo = False, True

                p.quit()
                ChessMain.main(playerOne=playerOne, playerTwo=playerTwo)
                return
        p.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    runMenu()