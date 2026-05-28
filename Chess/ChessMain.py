# This is the main driver file. It will be responsible for handling user input 
# and displaying the current GameState object

import pygame as p
import ChessEngine2, chessAI
import math, random

from multiprocessing import Process, Queue



BOARD_WIDTH = BOARD_HEIGHT = 512 #400 could work
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8 #dimensions of the chess board are 8x8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15 #for animations later on
IMAGES = {}
SOUNDS = {}


BOARD_LIGHT_SQ = p.Color(65, 45, 95)
BOARD_DARK_SQ = p.Color(28, 18, 45)

# Capture effect colour for each piece
CAPTURE_COLOURS = {
    'p': (255, 230, 80), # warm gold
    'N': (60, 210, 100), # emerald green
    'B': (180, 80, 255), # electric violet
    'R': (60, 160, 255), # steel blue
    'Q': (255, 200, 50), # royal gold
    'K': (255, 80, 80), # crimson
}



# Initialize a global dictionary of images. This will be called exactly once
# in the main

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("Chess/images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    #We can now access an image by saying 'IMAGES['wp']'

def loadSounds():
    p.mixer.init()
    sound_files = {
        "capture": "Chess/sounds/capturePiece.wav",
        "check": "Chess/sounds/kingInCheck.wav",
        "checkmate": "Chess/sounds/checkMateWin.ogg",
    }
    for name, path in sound_files.items():
        try:
            SOUNDS[name] = p.mixer.Sound(path)
        except FileNotFoundError:
            print(f"[Sound] Warning: '{path}' not found. '{name}' sound will be skipped.")
            SOUNDS[name] = None


def playSound(name):
    sound = SOUNDS.get(name)
    if sound:
        sound.play()

def spawnParticles(cx, cy, color, count=14, speed_lo=2.0, speed_hi=7.0):
    parts = []
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        spd = random.uniform(speed_lo, speed_hi)
        parts.append({
            'x': float(cx),
            'y': float(cy),
            'vx': math.cos(angle) * spd,
            'vy': math.sin(angle) * spd,
            'life': 1.0,
            'decay': random.uniform(0.04, 0.09),
            'color': color[:3],
            'size': random.randint(3, 6),
        })

    return parts


def tickParticles(surface, parts):
    alive = []
    for pt in parts:
        pt['x'] += pt['vx']
        pt['y'] += pt['vy']
        pt['vy'] += 0.22
        pt['life'] -= pt['decay']
        if pt['life'] <= 0:
            continue
        alpha = int(255 * pt['life'])
        sz = max(1, int(pt['size'] * pt['life']))
        s = p.Surface((sz * 2, sz * 2), p.SRCALPHA)
        p.draw.circle(s, (*pt['color'], alpha), (sz, sz), sz)
        surface.blit(s, (int(pt['x']) - sz, int(pt['y']) -sz))
        alive.append(pt)
    return alive


# Pawn punch effect for when pawn captures piece
def pawnPunchEffect(screen, board, cx, cy, color, clock):
    parts = spawnParticles(cx, cy, color, count=18, speed_lo=2, speed_hi=6)
    FRAMES = 24
    for frame in range(FRAMES):
        drawBoard(screen)
        drawPieces(screen, board)


        # To help expand the shockwave ring
        ring_r = int(6 + frame * 4)
        a = int(255 * max(0.0, 1.0 - frame / FRAMES))
        rs = p.Surface((ring_r * 2 + 4, ring_r * 2 + 4), p.SRCALPHA)
        p.draw.circle(rs, (*color, a), (ring_r + 2, ring_r + 2), ring_r, 3)
        screen.blit(rs, (cx - ring_r - 2, cy - ring_r -2))

        # To help with a central flash
        if frame < 8:
            fl_r = int(SQ_SIZE * 0.35 * (1 - frame / 8))
            fl_a = int(220 * (1 - frame / 8))
            fl = p.Surface((fl_r * 2, fl_r * 2), p.SRCALPHA)
            p.draw.circle(fl, (*color, fl_a), (fl_r, fl_r), fl_r)
            screen.blit(fl, (cx - fl_r, cy - fl_r))

        parts = tickParticles(screen, parts)
        p.display.flip()
        clock.tick(60)


def knightSmashEffect(screen, board, cx, cy, color, move, clock):
    captured = move.pieceCaptured
    parts = spawnParticles(cx, cy, color, count=20, speed_lo=2, speed_hi=8)
    FRAMES = 32

    for frame in range(FRAMES):
        t = frame / FRAMES
        drawBoard(screen)
        drawPieces(screen, board)

        if frame < 22 and captured in IMAGES:
            scale = max(0.05, 1.0 -frame / 32)
            angle = frame * 22
            sz = max(1, int(SQ_SIZE * scale))
            scaled = p.transform.scale(IMAGES[captured], (sz, sz))
            rot = p.transform.rotate(scaled, angle)
            rot.set_alpha(int(255 * (1 - t)))
            screen.blit(rot, (cx - rot.get_width() // 2, cy - rot.get_height() // 2))
        
        rng = int(frame * 5) # help expand the emerald ring
        if rng > 0 and frame < 18:
            a = int(255 * max(0, 1 - frame / 18))
            rs = p.Surface((rng * 2 + 6, rng * 2 + 6), p.SRCALPHA)
            p.draw.circle(rs, (*color, a), (rng + 3, rng + 3), rng, 4)
            screen.blit(rs, (cx - rng -3, cy - rng - 3))

        parts = tickParticles(screen, parts)
        p.display.flip()
        clock.tick(60)


def bishopSlashEffect(screen, board, cx, cy, color, clock):
    parts  = spawnParticles(cx, cy, color, count=14, speed_lo=1, speed_hi=5)
    FRAMES = 26
    for frame in range(FRAMES):
        drawBoard(screen)
        drawPieces(screen, board)

        # X-shaped diagonal beams
        if frame < 16:
            progress = min(1.0, frame / 8)
            beam_len = int(SQ_SIZE * 1.6 * progress)
            a = int(255 * max(0, 1 - frame / 16))
            bs = p.Surface((BOARD_WIDTH, BOARD_HEIGHT), p.SRCALPHA)
            for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                ex = cx + int(dx * beam_len / math.sqrt(2))
                ey = cy + int(dy * beam_len / math.sqrt(2))
                p.draw.line(bs, (*color, a),      (cx, cy), (ex, ey), 4)
                p.draw.line(bs, (*color, a // 2), (cx, cy), (ex, ey), 8) # glow halo
            screen.blit(bs, (0, 0))

        # Centre flash
        if frame < 6:
            r = int(SQ_SIZE * 0.3 * (1 - frame / 6))
            a = int(220 * (1 - frame / 6))
            f = p.Surface((r * 2, r * 2), p.SRCALPHA)
            p.draw.circle(f, (*color, a), (r, r), r)
            screen.blit(f, (cx - r, cy - r))

        parts = tickParticles(screen, parts)
        p.display.flip()
        clock.tick(60)

def rookBlastEffect(screen, board, cx, cy, color, clock):
    parts  = spawnParticles(cx, cy, color, count=14, speed_lo=2, speed_hi=6)
    FRAMES = 28
    for frame in range(FRAMES):
        drawBoard(screen)
        drawPieces(screen, board)

        # Straight-line cross blast (rook's movement directions)
        if frame < 14:
            ll = int(frame * 6)
            a  = int(220 * max(0, 1 - frame / 14))
            ls = p.Surface((BOARD_WIDTH, BOARD_HEIGHT), p.SRCALPHA)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                p.draw.line(ls, (*color, a), (cx, cy), (cx + dx * ll, cy + dy * ll), 4)
                p.draw.line(ls, (*color, a // 2), (cx, cy), (cx + dx * ll, cy + dy * ll), 8)
            screen.blit(ls, (0, 0))

        # Two offset expanding rings for depth
        for offset in [0, 8]:
            f = frame - offset
            if 0 <= f < 28:
                rr = int(f * 4)
                if rr > 0:
                    a = int(255 * max(0, 1 - f / 28))
                    rs = p.Surface((rr * 2 + 6, rr * 2 + 6), p.SRCALPHA)
                    p.draw.circle(rs, (*color, a), (rr + 3, rr + 3), rr, 3)
                    screen.blit(rs, (cx - rr - 3, cy - rr - 3))

        parts = tickParticles(screen, parts)
        p.display.flip()
        clock.tick(60)


def queenExplosionEffect(screen, board, cx, cy, color, clock):
    parts = spawnParticles(cx, cy, color, count=28, speed_lo=2, speed_hi=10)
    parts += spawnParticles(cx, cy, (255, 255, 200), count=16, speed_lo=1, speed_hi=5)
    FRAMES = 42
    for frame in range(FRAMES):
        t = frame / FRAMES
        drawBoard(screen)
        drawPieces(screen, board)

        # 8 radial beams for one per queen directios
        if frame < 22:
            bl = int(frame * 8)
            a = int(255 * max(0, 1 - frame / 22))
            bs = p.Surface((BOARD_WIDTH, BOARD_HEIGHT), p.SRCALPHA)
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                ex = cx + int(math.cos(rad) * bl)
                ey = cy + int(math.sin(rad) * bl)
                p.draw.line(bs, (*color, a), (cx, cy), (ex, ey), 3)
                p.draw.line(bs, (*color, a // 2), (cx, cy), (ex, ey), 7)
            screen.blit(bs, (0, 0))

        # Central supernova flash
        if frame < 12:
            r = int(SQ_SIZE * 0.5 * (1 - frame / 12))
            a = int(255 * (1 - frame / 12))
            fl = p.Surface((r * 2, r * 2), p.SRCALPHA)
            p.draw.circle(fl, (*color, a), (r, r), r)
            screen.blit(fl, (cx - r, cy - r))

        # Expanding halo ring
        rng = int(frame * 6)
        if rng > 0 and frame < 28:
            a  = int(200 * max(0, 1 - frame / 28))
            rs = p.Surface((rng * 2 + 8, rng * 2 + 8), p.SRCALPHA)
            p.draw.circle(rs, (*color, a), (rng + 4, rng + 4), rng, 5)
            screen.blit(rs, (cx - rng - 4, cy - rng - 4))

        parts = tickParticles(screen, parts)
        p.display.flip()
        clock.tick(60)


def kingCaptureEffect(screen, board, cx, cy, color, clock):
    parts  = spawnParticles(cx, cy, color, count=24, speed_lo=3, speed_hi=9)
    FRAMES = 30
    for frame in range(FRAMES):
        drawBoard(screen)
        drawPieces(screen, board)
        rng = int(frame * 5)
        if rng > 0:
            a  = int(200 * max(0, 1 - frame / FRAMES))
            rs = p.Surface((rng * 2 + 6, rng * 2 + 6), p.SRCALPHA)
            p.draw.circle(rs, (*color, a), (rng + 3, rng + 3), rng, 5)
            screen.blit(rs, (cx - rng - 3, cy - rng - 3))
        parts = tickParticles(screen, parts)
        p.display.flip()
        clock.tick(60)


def animateCaptureEffect(screen, move, board, clock):
    piece_type = move.pieceMoved[1]
    color = CAPTURE_COLOURS.get(piece_type, (255, 255, 255))
    cx = move.endCol * SQ_SIZE + SQ_SIZE // 2
    cy = move.endRow * SQ_SIZE + SQ_SIZE // 2
    dispatch = {
        'p': lambda: pawnPunchEffect(screen, board, cx, cy, color, clock),
        'N': lambda: knightSmashEffect(screen, board, cx, cy, color, move, clock),
        'B': lambda: bishopSlashEffect(screen, board, cx, cy, color, clock),
        'R': lambda: rookBlastEffect(screen, board, cx, cy, color, clock),
        'Q': lambda: queenExplosionEffect(screen, board, cx, cy, color, clock),
        'K': lambda: kingCaptureEffect(screen, board, cx, cy, color, clock),
    }
    fn = dispatch.get(piece_type)
    if fn:
        fn()

def getCheckingPieces(gs):
    if gs.whiteToMove:
        kingR, kingC = gs.whiteKingLocation
    else:
        kingR, kingC = gs.blackKingLocation

    # to help temporarily flip so it can genratwe opponent moves
    gs.whiteToMove = not gs.whiteToMove
    opp_moves = gs.getAllPossibleMoves()
    gs.whiteToMove = not gs.whiteToMove

    seen, checkers = set(), []
    for mv in opp_moves:
        if mv.endRow == kingR and mv.endCol == kingC:
            pos = (mv.startRow, mv.startCol)
            if pos not in seen:
                seen.add(pos)
                checkers.append(pos)
    return checkers, (kingR, kingC)

def animateCheckEffect(screen, gs, board, clock): # We are going to be using a white beam
    checkers, (kingR, kingC) = getCheckingPieces(gs)
    if not checkers:
        return
    
    kingCX = kingC * SQ_SIZE + SQ_SIZE // 2
    kingCY = kingR * SQ_SIZE + SQ_SIZE // 2
    FRAMES = 54

    for frame in range(FRAMES):
        pulse= abs(math.sin(frame * math.pi / 10))
        drawBoard(screen)
        drawPieces(screen, board)

        ks = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
        p.draw.rect(ks, (255, 40, 40, int(190 * pulse)), ks.get_rect())
        screen.blit(ks, (kingC * SQ_SIZE, kingR * SQ_SIZE))

        ls = p.Surface((BOARD_WIDTH, BOARD_HEIGHT), p.SRCALPHA)
        for (chR, chC) in checkers:
            chCX = chC * SQ_SIZE + SQ_SIZE // 2
            chCY = chR * SQ_SIZE + SQ_SIZE // 2
            a = int(230 * (0.45 + 0.55 * pulse))


            p.draw.line(ls, (255, 100, 100, a // 2), (chCX, chCY), (kingCX, kingCY), 7)
            p.draw.line(ls, (255, 40, 40, a), (chCX, chCY), (kingCX, kingCY), 3)

            cs = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
            p.draw.rect(cs, (255, 140, 60, int(100 * pulse)), cs.get_rect())
            screen.blit(cs, (chC * SQ_SIZE, chR * SQ_SIZE))
        screen.blit(ls, (0, 0))
        p.display.flip()
        clock.tick(60)

def animateResolveCheckEffect(screen, move, board, clock):
    cx = move.endCol * SQ_SIZE + SQ_SIZE // 2
    cy = move.endRow * SQ_SIZE + SQ_SIZE // 2
    color = (80, 210, 255)
    FRAMES = 28
    for frame in range(FRAMES):
        t = frame /FRAMES
        drawBoard(screen)
        drawPieces(screen, board)

        for ring_offset in [0, 7]:
            f = frame - ring_offset
            if f < 0:
                continue
            rr = int(SQ_SIZE * 0.2 + f * 3.5)
            a = int(255 * max(0.0, 1.0 - f / FRAMES))
            rs = p.Surface((rr * 2 + 6, rr * 2 + 6), p.SRCALPHA)
            p.draw.circle(rs, (*color, a), (rr + 3, rr+3), rr, 3)
            screen.blit(rs, (cx - rr - 3, cy - rr -3))

        p.display.flip()
        clock.tick(60)





def drawPromotionUI(screen, gs):
    pieces = ['Q', 'R', 'B', 'N']
    color = 'w' if gs.whiteToMove else 'b'

    panelW = SQ_SIZE * 4
    panelH = SQ_SIZE
    panelX = (BOARD_WIDTH - panelW) // 2
    panelY = (BOARD_HEIGHT - panelH) // 2

    overlay = p.Surface((BOARD_WIDTH, BOARD_HEIGHT), p.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    box = p.Rect(panelX - 10, panelY - 10, panelW + 20, panelH + 20)
    p.draw.rect(screen, p.Color(30, 30, 30), box, border_radius=8)
    p.draw.rect(screen, p.Color(200, 160, 80), box, width=2, border_radius=8)

    for i, piece in enumerate(pieces):
        screen.blit(IMAGES[color + piece],
                    p.Rect(panelX + i * SQ_SIZE, panelY, SQ_SIZE, SQ_SIZE))
        
    p.display.flip()

    clock = p.time.Clock()
    while True:
        for event in p.event.get():
            if event.type == p.QUIT:
                return 'Q'
            if event.type == p.MOUSEBUTTONDOWN:
                mx, my = p.mouse.get_pos()
                if panelY <= my <= panelY + panelH:
                    for i, piece in enumerate(pieces):
                        if panelX + i * SQ_SIZE <= mx <= panelX + (i + 1) * SQ_SIZE:
                            return piece
        clock.tick(30)

# The main driver for our code. This will handle user input and updating the graphics

def main(playerOne=True, playerTwo=False):
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    moveLogFont = p.font.SysFont("Arial", 18, False, False)
    gs = ChessEngine2.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False #flgag variable for when a move is made
    animate = False # Flag variable for when we should animate a move

    loadImages() #only do this once, before the while loop
    loadSounds()
    running = True
    sqSelected = () # Where no square is selected initially. Keep track of the last click of the user
    playerClicks = [] # Keep track of player clicks


    gameOver = False

    AIThinking = False
    moveFinderProcess = None
    moveUndone = False

    moveGivesCheck = False # did the move just make the opponent be in check
    currentPlayerInCheck = False # is the player the one now moves in the check



    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            # Mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos() # (x,y) location of the mouse
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, col) or col >= 8: # This would check if the user clicked the same square twice or clicked the mouse log
                        sqSelected = () #deselect
                        playerClicks = [] # clear player clicks
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected) #Appened for both 1st and 2nd clicks
                    if len(playerClicks) == 2:
                        move = ChessEngine2.Move(playerClicks[0], playerClicks[1], gs.board)
                        print(move.getChessNotation())

                        # If the clicked move is a pawn promotion, ask the human which piece
                        if move.isPawnPromotion:
                            # Only show UI if at least one valid promotion exists for this start→end
                            isValidPromotion = any(
                                vm.isPawnPromotion
                                and vm.startRow == move.startRow and vm.startCol == move.startCol
                                and vm.endRow  == move.endRow  and vm.endCol  == move.endCol
                                for vm in validMoves
                            )
                            if isValidPromotion:
                                choice = drawPromotionUI(screen, gs)
                                move.promotionChoice = choice

                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                validMoves[i].setDisambiguation(validMoves)
                                gs.makeMove(validMoves[i])
                                moveGivesCheck = gs.inCheck()
                                moveMade = True
                                animate = True
                                sqSelected = ()
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]
            # Key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: #Undo when 'z' is pressed
                    gs.undoMove()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = True
                    animate = False
                    gameOver = False
                    moveGivesCheck = False
                    currentPlayerInCheck = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        AIThinking = False
                    moveUndone = True
                if e.key == p.K_r:
                    gs = ChessEngine2.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False
                    moveGivesCheck = False
                    currentPlayerInCheck = False
                    if AIThinking:
                        moveFinderProcess.terminate()
                        moveFinderProcess.join()
                        AIThinking = False
                    moveUndone = True

        # AI move finder
        if not gameOver and not humanTurn and not moveUndone:
            if not AIThinking:
                AIThinking = True
                returnQueue = Queue() # used to pass data between threads
                moveFinderProcess = Process(target=chessAI.findBestMove, args=(gs, validMoves, returnQueue, chessAI.DEPTH))
                moveFinderProcess.start() # Call chessAI findBestMove(gs, validMoves, returnQueue)
 
            if not moveFinderProcess.is_alive():
                AIMove = returnQueue.get()
                if AIMove is None:
                    AIMove = chessAI.findRandomMove(validMoves)
                AIMove.setDisambiguation(validMoves)
                gs.makeMove(AIMove)
                moveGivesCheck = gs.inCheck()
                moveMade = True
                animate = True
                AIThinking = False


        if moveMade:
            prevPlayerWasInCheck = currentPlayerInCheck # was the mover in check?
            move = gs.movelog[-1] if gs.movelog else None

            if animate and move:
                animateMove(move, screen, gs.board, clock, fast=moveGivesCheck)

                if move.isCapture:
                    playSound("capture")
                    animateCaptureEffect(screen, move, gs.board, clock) # Fast animation if this move gives check (dramatic speed burst)

                elif prevPlayerWasInCheck:
                    # player escaped / blocked check without capturing
                    animateResolveCheckEffect(screen, move, gs.board, clock)
 
            validMoves = gs.getValidMoves()
            currentPlayerInCheck = gs.inCheck()
            
            if moveGivesCheck and not gs.checkmate and not gs.stalemate:
                playSound("check")
                animateCheckEffect(screen, gs, gs.board, clock)
            
            moveMade = False
            animate = False
            moveUndone = False
            moveGivesCheck = False

        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)
        if gs.checkmate or gs.stalemate:
            if not gameOver:
                if gs.checkmate:
                    playSound("checkmate")
            gameOver = True
            if gs.stalemate:
                drawEndGameText(screen, "Stalemate", None)
            elif gs.whiteToMove:
                joke = "I guess I might replace you🫵😂🙏" if not playerTwo else None
                drawEndGameText(screen, "Black wins by Checkmate", joke)
                
            else:
                joke = "I guess I might replace you🫵😂🙏" if not playerOne else None
                drawEndGameText(screen, "White wins by Checkmate", joke)
   

        clock.tick(MAX_FPS)
        p.display.flip()

#Responsible for all the graphic with a current game state
def drawGameState(screen, gs, validMoves, sqSelected, moveLogFont):
    drawBoard(screen) # Draw the swaureson the board
    drawArcaneOverlay(screen)
    drawPieces(screen, gs.board) # draw pieces on top of the squares
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawMoveLog(screen, gs, moveLogFont)




def drawBoard(screen):
    GLOW_COLOR = p.Color(180, 120, 255, 40)  # Subtle magical glow

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            is_light = (r + c) % 2 == 0
            base_color = BOARD_LIGHT_SQ if is_light else BOARD_DARK_SQ
            
            rect = p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            p.draw.rect(screen, base_color, rect)
            
            # Add subtle inner glow/border for magical feel
            if is_light:
                glow_rect = rect.inflate(-6, -6)
                s = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
                p.draw.rect(s, GLOW_COLOR, glow_rect, border_radius=4)
                screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))


_STAR_POSITIONS = [(random.randint(0, BOARD_WIDTH), random.randint(0, BOARD_HEIGHT),
                    random.randint(20, 70)) for _ in range(80)]

def drawArcaneOverlay(screen):
    overlay = p.Surface((BOARD_WIDTH, BOARD_HEIGHT), p.SRCALPHA)

    # Static stars / magical dust — positions are fixed, no more flickering
    for x, y, alpha in _STAR_POSITIONS:
        p.draw.circle(overlay, (220, 220, 255, alpha), (x, y), 1)
    
    # Very faint vertical mystical beams
    for x in range(0, BOARD_WIDTH, 90):
        p.draw.line(overlay, (140, 100, 255, 8), (x, 0), (x, BOARD_HEIGHT), 2)
    
    screen.blit(overlay, (0, 0))




# Highlight the square selected and moves for the piece selected
def highlightSquares(screen, gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ("w" if gs.whiteToMove else "b"): #sqselected is a piece that can be movd
            #highlight selected square
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(120) # Transparency value
            s.fill(p.Color(205, 170, 0))
            screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
            # highlight moves from that square
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    dot_surface = p.Surface((SQ_SIZE, SQ_SIZE), p.SRCALPHA)
                    p.draw.circle(
                        dot_surface,
                        (0, 0, 0, 80), # Semi-transparent dark dot
                        (SQ_SIZE // 2, SQ_SIZE // 2),
                        SQ_SIZE //6
                    )
                    screen.blit(dot_surface, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))



def drawPieces(screen, board): # Draw pieces on the board
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": # not an empty sqaure
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                

def drawMoveLog(screen, gs, font): # Draws the move log


    moveLogRect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color("black"), moveLogRect)
    moveLog = gs.movelog
    moveTexts = []
    for i in range(0, len(moveLog), 2):
        moveString = str(i//2 + 1) + ". " + str(moveLog[i]) + " "
        if i+1 < len(moveLog): # make sure black made a move
            moveString += str(moveLog[i+1]) + " "
        moveTexts.append(moveString)
    
    
    movesPerRow = 3
    padding = 5
    lineSpacing = 2
    textY = padding
    for i in range(0, len(moveTexts), movesPerRow):
        text = ""
        for j in range(movesPerRow):
            if i + j < len(moveTexts):
                text += moveTexts[i+j]
        textObject = font.render(text, True, p.Color(255, 255, 255))  # white text
        textLocation = moveLogRect.move(padding, textY)
        screen.blit(textObject, textLocation)
        textY += textObject.get_height() + lineSpacing



# Animating a move
def animateMove(move, screen, board, clock, fast=False):
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 4 if fast else 10
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare

    for frame in range(frameCount + 1):
        # Smoothstep easing: slow start, fast middle, slow end
        t_raw = frame / frameCount
        t = t_raw if fast else t_raw * t_raw * (3 - 2 * t_raw)

        r = move.startRow + dR * t
        c = move.startCol + dC * t

        drawBoard(screen)
        drawPieces(screen, board)

        # Erase piece from ending square
        is_light = (move.endRow + move.endCol) % 2 == 0
        color = BOARD_LIGHT_SQ if is_light else BOARD_DARK_SQ
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)

        # Fade out captured piece during animation
        if move.pieceCaptured != "--":
            if move.isEnpassantMove:
                enPassantRow = move.endRow + 1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                endSquare = p.Rect(move.endCol * SQ_SIZE, enPassantRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            fade = max(0, int(255 * (1 - t_raw)))  # fully visible at start, gone at end
            captured_img = IMAGES[move.pieceCaptured].copy()
            captured_img.set_alpha(fade)
            screen.blit(captured_img, endSquare)

        if fast and frame > 0:
            for trail in range(min(frame, 3), 0, -1):
                trail_t = max(0.0, t - trail * 0.18)
                trail_r = move.startRow + dR * trail_t
                trail_c = move.startCol + dC * trail_t
                t_alpha = max(0, int(80 // trail))
                t_surf = IMAGES[move.pieceMoved].copy()
                t_surf.set_alpha(t_alpha)
                screen.blit(t_surf, p.Rect(trail_c * SQ_SIZE, trail_r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

        # Draw the moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawEndGameText(screen, text, jokeText=None):
    # Semi-transparent dark overlay over the whole board
    overlay = p.Surface((BOARD_WIDTH, BOARD_HEIGHT), p.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # black with ~60% opacity
    screen.blit(overlay, (0, 0))

    mainFont = p.font.SysFont("Helvetica", 36, True, False)  # fixed typo too
    emojiFont = p.font.SysFont("Segoe UI Emoji", 26, False, False)
    mainObj = mainFont.render(text, True, p.Color(255, 255, 255))  # white text
    jokeObj = emojiFont.render(jokeText, True, p.Color(255, 215, 0)) if jokeText else None


    padding = 16
    lineGap = 10
    boxW = max(mainObj.get_width(), jokeObj.get_width() if jokeObj else 0) + padding * 2
    boxH = mainObj.get_height() + (lineGap + jokeObj.get_height() if jokeObj else 0) + padding * 2

    boxX = BOARD_WIDTH // 2 - boxW // 2
    boxY = BOARD_HEIGHT // 2 - boxH // 2

    box_rect = p.Rect(boxX, boxY, boxW, boxH)
    p.draw.rect(screen, p.Color(30, 30, 30), box_rect, border_radius=8)
    p.draw.rect(screen, p.Color(200, 160, 80), box_rect, width=2, border_radius=8)

    screen.blit(mainObj, (BOARD_WIDTH // 2 - mainObj.get_width() // 2, boxY + padding))

    if jokeObj:
        screen.blit(jokeObj, (BOARD_WIDTH // 2 - jokeObj.get_width() // 2, boxY + padding + mainObj.get_height() + lineGap))

if __name__ == "__main__":
    main()



