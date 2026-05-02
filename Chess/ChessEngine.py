# This class is responisble for storing all the information about 
# the current state of a chess game. 
# It will also be responsible for determining the valid moves at the current state
# It will also keep a move log

class GameState():
    def __init__(self):
        # The board is an 8x8 list, each element in the list has 2 characters
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"], 
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],]
            # We used 'b' and 'w' to represent the color black and white respectively, then the capital letters are the pieces, 
            # note 'N' is for knight and 'K' for king
            # The "--" represents an empty space with no piece
        self.whiteToMove = True
        self.movelog = []

    
    # Takes a move as a parameter and executes it (This will not work for castling and en-passant)
    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.movelog.append(move) # log the move so we can undo it later
        self.whiteToMove = not self.whiteToMove # To help with swapping turns

    
    # This will undo the last move made
    def undoMove(self):
        if len(self.movelog) != 0:  #Make sure there is a move to undo
            move = self.movelog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove # Switch turns back






    # All moves considering checks

    def getValidMoves(self):
        return self.getAllPossibleMoves() # for now we won't worry about checks

    # All moves without considering checks

    def getAllPossibleMoves(self):
        moves = [Move((6,4), (4,4), self.board)]
        for r in range(len(self.board)): # Number of rows
            for c in range(len(self.board[r])): # Number of columns in given row
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) and (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    if piece == 'p':
                        self.getPawnMoves(r, c, moves)
                    elif piece == 'R':
                        self.getRookMoves(r, c, moves)

        return moves
    # Get all the pawn moves for the pawn located at row, col and add these moves to the list

    def getPawnMoves(self, r, c, moves):
        pass

    def getRookMoves(self, r, moves): # Get all rook moves
        pass





class Move():
    # maps keys to values
    # key: value
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}  ## HAD TO USE CLAUDE FOR THIS 😂
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}


    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol] # We are trying to keep track of information right here
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        print(self.moveID)
    # Overriding the equals method
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False


    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]