# This is the main driver file. It will be responsible for handling user input 
# and displaying the current GameState object

import pygame as p
import ChessEngine

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
    gs = ChessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False #flgag variable for when a move is made


    loadImages() #only do this once, before the while loop
    running = True
    sqSelected = () # Where no square is selected initially. Keep track of the last click of the user
    playerClicks = [] # Keep track of player clicks



    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            # Mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
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
                    move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                    print(move.getChessNotation())
                    if move in validMoves:
                        gs.makeMove(move)
                        moveMade = True
                    # Personal move: removed "gs.makeMove(True) which was outside the if move"
                    sqSelected = () # To help the user reset the clicks
                    playerClicks = []

            # Key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z: #Undo when 'z' is pressed
                    gs.undoMove()
                    moveMade = True
        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False

        drawGameState(screen, gs)
        clock.tick(MAX_FPS)
        p.display.flip()


#Responsible for all the graphic with a current game state
def drawGameState(screen, gs):
    drawBoard(screen) # Draw the swaureson the board
    drawPieces(screen, gs.board) # draw pieces on top of the squares


def drawBoard(screen): # Draw the squares on the board
    colors = [p.Color("white"), p.Color("gray")] # WE ARE GONNA CHANGE THIS LATER
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
                






if __name__ == "__main__":
    main()



























