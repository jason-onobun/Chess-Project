# This is the main driver file. It will be responsible for handling user input 
# and displaying the current GameState object

import pygame as p
import ChessEngine2, chessAI

WIDTH = HEIGHT = 512 #400 could work
DIMENSION = 8 #dimensions of the chess board are 8x8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15 #for animations later on
IMAGES = {}


# Initialize a global dictionary of images. This will be called exactly once
# in the main

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("Chess/images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    #We can now access an image by saying 'IMAGES['wp']'


# The main driver for our code. This will handle user input and updating the graphics

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = ChessEngine2.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False #flgag variable for when a move is made
    animate = False # Flag variable for when we should animate a move

    loadImages() #only do this once, before the while loop
    running = True
    sqSelected = () # Where no square is selected initially. Keep track of the last click of the user
    playerClicks = [] # Keep track of player clicks


    gameOver = False
    playerOne = False # If a human is playing white, then this will be true. if an AI is playing, then false
    playerTwo = True # Same as above but for black
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
                    if sqSelected == (row, col): # This would check if the user clicked the same square twice
                        sqSelected = () #deselect
                        playerClicks = [] # clear player clicks
                    else:
                        sqSelected = (row, col)
                        playerClicks.append(sqSelected) #Appened for both 1st and 2nd clicks
                    if len(playerClicks) == 2: #after second click
                        move = ChessEngine2.Move(playerClicks[0], playerClicks[1], gs.board)
                        #print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move == validMoves[i]:
                                gs.makeMove(validMoves[i])
                                moveMade = True
                                animate = True
                                sqSelected = () # To help the user reset the clicks
                                playerClicks = []
                        if not moveMade:
                            playerClicks = [sqSelected]  #if lets say you mistakenly clicked a piece you do not want to move

            # Key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: #Undo when 'z' is pressed
                    gs.undoMove()
                    moveMade = True
                    animate = False
                    gameOver = False
                if e.key == p.K_r:
                    gs = ChessEngine2.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False
                    gameOver = False


        # AI move finder
        if not gameOver and not humanTurn:
            AIMove = chessAI.findBestMove(gs, validMoves)
            if AIMove is None:
                AIMove = chessAI.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = True


        if moveMade:
            if animate:
                animateMove(gs.movelog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        drawGameState(screen, gs, validMoves, sqSelected)
        if gs.checkmate:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, "Black wins by Checkmate")
            else:
                drawText(screen, "White wins by Checkmate")
        elif gs.stalemate:
            gameOver = True
            drawText(screen, "Stalemate")
        clock.tick(MAX_FPS)
        p.display.flip()


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




#Responsible for all the graphic with a current game state
def drawGameState(screen, gs, validMoves, sqSelected):
    drawBoard(screen) # Draw the swaureson the board
    drawPieces(screen, gs.board) # draw pieces on top of the squares
    highlightSquares(screen, gs, validMoves, sqSelected)


def drawBoard(screen): # Draw the squares on the board
    global colors
    colors = [p.Color(240, 217, 181), p.Color(181, 136, 99)] # WE ARE GONNA CHANGE THIS LATER
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c) % 2)] #We want to determine if the board would be black
            # or white. where if it is '0' it will be white and if it is '1' it would be black
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def drawPieces(screen, board): # Draw pieces on the board
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": # not an empty sqaure
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
                

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
            fade = max(0, int(255 * (1 - t)))  # fully visible at start, gone at end
            captured_img = IMAGES[move.pieceCaptured].copy()
            captured_img.set_alpha(fade)
            screen.blit(captured_img, endSquare)

        # Draw the moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawText(screen, text):
    # Semi-transparent dark overlay over the whole board
    overlay = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # black with ~60% opacity
    screen.blit(overlay, (0, 0))

    font = p.font.SysFont("Helvetica", 36, True, False)  # fixed typo too
    textObject = font.render(text, True, p.Color(255, 255, 255))  # white text

    # Center the text
    textX = WIDTH // 2 - textObject.get_width() // 2
    textY = HEIGHT // 2 - textObject.get_height() // 2

    # Draw a dark rounded-ish box behind the text for readability
    padding = 16
    box_rect = p.Rect(textX - padding, textY - padding,
                      textObject.get_width() + padding * 2,
                      textObject.get_height() + padding * 2)
    p.draw.rect(screen, p.Color(30, 30, 30), box_rect, border_radius=8)
    p.draw.rect(screen, p.Color(200, 160, 80), box_rect, width=2, border_radius=8)  # gold border

    screen.blit(textObject, (textX, textY))

if __name__ == "__main__":
    main()



