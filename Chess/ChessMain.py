# This is the main driver file. It will be responsible for handling user input 
# and displaying the current GameState object

import pygame as p
import ChessEngine2, chessAI

from multiprocessing import Process, Queue



BOARD_WIDTH = BOARD_HEIGHT = 512 #400 could work
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8 #dimensions of the chess board are 8x8
SQ_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15 #for animations later on
IMAGES = {}


# Initialize a global dictionary of images. This will be called exactly once
# in the main

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("Chess/images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    #We can now access an image by saying 'IMAGES['wp']'


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
    running = True
    sqSelected = () # Where no square is selected initially. Keep track of the last click of the user
    playerClicks = [] # Keep track of player clicks


    gameOver = False

    AIThinking = False
    moveFinderProcess = None
    moveUndone = False
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
                moveMade = True
                animate = True
                AIThinking = False


        if moveMade:
            if animate:
                animateMove(gs.movelog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
            moveUndone = False

        drawGameState(screen, gs, validMoves, sqSelected, moveLogFont)
        if gs.checkmate or gs.stalemate:
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
    drawPieces(screen, gs.board) # draw pieces on top of the squares
    highlightSquares(screen, gs, validMoves, sqSelected)
    drawMoveLog(screen, gs, moveLogFont)



def drawBoard(screen): # Draw the squares on the board
    global colors
    colors = [p.Color(240, 217, 181), p.Color(181, 136, 99)] # WE ARE GONNA CHANGE THIS LATER
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)] #We want to determine if the board would be black
            # or white. where if it is '0' it will be white and if it is '1' it would be black
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))



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
def animateMove(move, screen, board, clock):
    global colors
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    framesPerSquare = 10
    frameCount = (abs(dR) + abs(dC)) * framesPerSquare

    for frame in range(frameCount + 1):
        # Smoothstep easing: slow start, fast middle, slow end
        t = frame / frameCount
        t = t * t * (3 - 2 * t)  # the smoothstep formula

        r = move.startRow + dR * t
        c = move.startCol + dC * t

        drawBoard(screen)
        drawPieces(screen, board)

        # Erase piece from ending square
        color = colors[(move.endRow + move.endCol) % 2]
        endSquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endSquare)

        # Fade out captured piece during animation
        if move.pieceCaptured != "--":
            if move.isEnpassantMove:
                enPassantRow = move.endRow + 1 if move.pieceCaptured[0] == 'b' else move.endRow - 1
                endSquare = p.Rect(move.endCol * SQ_SIZE, enPassantRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            fade = max(0, int(255 * (1 - t)))  # fully visible at start, gone at end
            captured_img = IMAGES[move.pieceCaptured].copy()
            captured_img.set_alpha(fade)
            screen.blit(captured_img, endSquare)

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



