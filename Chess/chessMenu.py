import pygame as p
import sys
import chessAI
import ChessMain

SCREEN_W, SCREEN_H = 762, 600
BG_DARK = (18, 18, 18)
BG_PANEL = (30, 30, 30)
GOLD = (200, 160, 80)
GOLD_DIM = (140, 110, 50)
WHITE = (240, 240, 240)
GREY = (160, 160, 160)
LIGHT_SQ = (240, 217, 181)
DARK_SQ = (181, 136, 99)
GREEN_SEL = (80, 170, 100)
GREEN_DIM = (50, 110, 65)
RED_SEL = (190, 70, 70)

DIFFICULTIES = {
    "Easy": 1,
    "Medium": 2,
    "Hard": 3,
    "Expert": 4,
}

DIFF_LABELS = list(DIFFICULTIES.keys())


def drawButton(surface, rect, text, font,
               bg, border, textColor=WHITE,
               hovered=False, radius=10):
    col = tuple(min(c + 25, 255) for c in bg) if hovered else bg
    p.draw.rect(surface, col, rect, border_radius=radius)
    p.draw.rect(surface, border, rect, width=2, border_radius=radius)
    label = font.render(text, True, textColor)
    lx = rect.centerx - label.get_width() // 2
    ly = rect.centery - label.get_height() // 2
    surface.blit(label, (lx, ly))


def drawCheckerboardBg(surface): # would help with a sbutle chessboard-tile background
    sq = 40
    cols = SCREEN_W // sq + 1
    rows = SCREEN_H // sq + 1
    for r in range(rows):
        for c in range(cols):
            colour = (28, 28, 28) if (r+c) % 2 == 0 else (22, 22, 22)
            p.draw.rect(surface, colour, p.Rect(c * sq, r* sq, sq, sq))


def screenHome(surface, fonts, mouse, events):

    drawCheckerboardBg(surface)

    title = fonts["title"].render("CHESS", True, GOLD)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 165))

    btnHuman = p.Rect(SCREEN_W // 2 - 160, 270, 320, 60) # button for human
    btnAI = p.Rect(SCREEN_W // 2 - 160, 360, 320, 60) # button for AI
    btnQuit = p.Rect(SCREEN_W // 2 - 80, 460, 160, 48)

    mx, my = mouse
    hH = btnHuman.collidepoint(mx, my)
    hA = btnAI.collidepoint(mx, my)
    hQ = btnQuit.collidepoint(mx, my)

    drawButton(surface, btnHuman, "Play vs Human", fonts["btn"], BG_PANEL, GOLD, hovered=hH)
    drawButton(surface, btnAI,  "Play vs AI",   fonts["btn"], BG_PANEL, GOLD, hovered=hA)
    drawButton(surface, btnQuit,  "Quit",       fonts["btn"], BG_PANEL, RED_SEL, hovered=hQ, radius=8)

    for e in events:
        if e.type == p.MOUSEBUTTONDOWN and e.button == 1:
            if hH: return "human"
            if hA: return "ai"
            if hQ: p.quit(); sys.exit()
    return None

def screenAIOptions(surface, fonts, mouse, events, state):
    drawCheckerboardBg(surface)

    # For the title

    title = fonts["heading"].render("Game Settings", True, GOLD)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 40))

    mx, my = mouse

    # To help the player choose their colour when playing against the AI
    secLabel = fonts["label"].render("Play as", True, WHITE)
    surface.blit(secLabel, (SCREEN_W // 2 - 200, 115))

    colourOptions = [("White", "white"), ("Black", "black"), ("Random", "random")]
    colBtnW, colBtnH = 130, 48

    colStartX = SCREEN_W // 2 - (colBtnW * 3 + 16) // 2
    colBtnY = 150
    colRects = []
    for i, (label, val) in enumerate(colourOptions):
        r = p.Rect(colStartX + i * (colBtnW + 8), colBtnY, colBtnW, colBtnH)
        colRects.append((r, val))
        selected = (state["colour"] == val)
        bg = GREEN_SEL if selected else BG_PANEL
        border = GREEN_DIM if selected else GOLD_DIM
        hov = r.collidepoint(mx, my) and not selected
        drawButton(surface, r, label, fonts["btn"], bg, border, hovered=hov, radius=8)

    # Handling difficulty
    diffLabel = fonts["label"].render("Difficulty", True, WHITE)
    surface.blit(diffLabel, (SCREEN_W // 2 - 200, 240))

    diffBtnW, diffBtnH = 130, 48
    diffstartX = SCREEN_W // 2 - (diffBtnW * 4 + 24) // 2
    diffBtnY = 275
    diffRects = []
    for i, name in enumerate(DIFF_LABELS):
        r = p.Rect(diffstartX + i * (diffBtnW + 8), diffBtnY, diffBtnW, diffBtnH)
        diffRects.append(r)
        selected = (state["difficulty"] == i)
        bg      = GREEN_SEL if selected else BG_PANEL
        border = GREEN_DIM if selected else GOLD_DIM
        hov = r.collidepoint(mx, my) and not selected
        drawButton(surface, r, name, fonts["btn"], bg, border, hovered=hov, radius=8)


            # Difficulty description

    depthVal = DIFFICULTIES[DIFF_LABELS[state["difficulty"]]]
    descriptions = {
        0: "looks 1 Move ahead - great for beginners.",
        1: "Plays reasonably well; makes solid moves.",
        2: "Thinks 3 moves deep - a real challenge.",
        3: "Maximum depth - TOUGH fight. Much slower though.",}

    desc = fonts["small"].render(descriptions[state["difficulty"]], True, GREY)
    surface.blit(desc, (SCREEN_W // 2 - desc.get_width() // 2, 338))
    depthInfo = fonts["small"].render(f"(Search depth: {depthVal})", True, GOLD_DIM)
    surface.blit(depthInfo, (SCREEN_W // 2 - depthInfo.get_width() // 2, 362))

    btnStart = p.Rect(SCREEN_W // 2 + 20, 460, 200, 56)
    btnBack = p.Rect(SCREEN_W // 2 - 220, 460, 180, 56)


    hS = btnStart.collidepoint(mx, my)
    hB = btnBack.collidepoint(mx, my)

    drawButton(surface, btnStart, "Start Game", fonts["btn"], GREEN_SEL, GREEN_DIM, hovered=hS, radius=10)
    drawButton(surface, btnBack,  "<- Back",        fonts["btn"], BG_DARK, GOLD_DIM, hovered=hB, radius=10)


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
    p.display.set_caption("Chess")
    clock = p.time.Clock()

    fonts = {
        "title": p.font.SysFont("Georgia", 64, bold=True),
        "heading": p.font.SysFont("Georgia", 42, bold=True),
        "sub": p.font.SysFont("Georgia", 20, bold=False, italic=True),
        "btn": p.font.SysFont("Arial", 22, bold=True),
        "label": p.font.SysFont("Arial", 20, bold=True),
        "small": p.font.SysFont("Arial", 26),
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
                    import random
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