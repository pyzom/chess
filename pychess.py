import numpy as np
import pandas as pd
import os
import sys
import pygame as pg
from stockfish import Stockfish
from copy import deepcopy
from itertools import chain
from draw_chess_board import *

class Game:
    alternator = alternate_turn()
    def __init__(self):
        # board representation in Forsyth-Edwards-Notation (FEN)
        self.FEN = initial_FEN_position
        stockfish.set_fen_position(initial_FEN_position)
        self.position_dict = {1: initial_FEN_position}

        self.players = list(place_pieces())
        self.turn, self.opponent = WHITE, BLACK

        self.mode = 'game'
        self.capture = False
        self.ep_square = '-'
        self.en_passant = False
        self.castling_rights = 'KQkq'
        self.castled_qs = False
        self.castled_ks = False
        self.fullmove = int(self.FEN[-1])
        self.halfmove = int(self.FEN[-3])
        self.move_dict = {}
        self.move_rect_dict = {}
        self.SAN_list = []
        self.check = False
        self.stale_mate = False
        self.captured_list = []
        self.captured_dict = {}
        self.engine = False
        self.machine = False
        self.engine_level = stockfish.set_skill_level(20)
        self.f_pos = None
        #self.l_pos = None
        self.the_move = None
        self.promote_pawn = False
        self.promotion_choice = None
        self.clicked = None


    def is_check(self):
        king_position = self.king_pos(self.opponent)
        if self.square_safe(self.turn, king_position):
            return False
        print('CHECK')
        return True

    def is_mate(self):
        for player in self.players:

            if player.color == self.turn and player.on_board:
                if player.symbol.upper() == 'P':
                    scanned_list = chain(player.available_captures(),
                            player.available_moves())
                else:
                    scanned_list = player.available_moves()

                for i in scanned_list:
                    temp = board.loc[i]
                    if temp:
                        temp.on_board = False
                    original_pos = player.pos[:]
                    board.loc[player.pos] = 0
                    board.loc[i] = player

                    player.pos = i
                    player.rank, player.file = i

                    king_position = self.king_pos(self.turn)
                    if self.square_safe(self.opponent, king_position):

                        player.pos = original_pos
                        player.rank, player.file = original_pos
                        board.loc[original_pos] = player
                        board.loc[i] = temp
                        if temp:
                            temp.on_board = True

                        print(board, 'NOT MATE\n ', player, 'can move to', i)
                        return False
                    player.pos = original_pos
                    player.rank, player.file = original_pos
                    board.loc[original_pos] = player
                    board.loc[i] = temp
                    if temp:
                        temp.on_board = True
        print('mate')
        return True

    def square_safe(self, turn, pos):
        for player in self.players:
            if player.on_board and player.color == turn:
                if (player.symbol.upper() == 'P' and pos in player.can_capture()):
                    return False
                elif (player.symbol.upper() != 'P' and
                        pos in player.available_moves()):
                    return False
        return True

    def draw_current_board(self, surface, players, start):
        for player in players:
            if player.on_board and player.pos != start:
                player.update(surface)

    def main(self, surface):
        global choices
        surface.fill((125, 135, 150))
        draw_frame(surface)
        draw_squares(surface)
        draw_move_screen(surface, self.clicked)        
        self.game_event_loop(surface)
        self.move_screen(surface)

        if self.engine:
            self.engine_main_loop(surface)
            self.engine = False
        for player in self.players:
            player.update(surface)

        if self.promote_pawn:
            choices = draw_promote_choices(surface, (8, 'e'), self.opponent)
            #print(choices)
            for choice in choices:
                choice.update(surface)
        pg.display.update()
        clock.tick(60)

    def game_event_loop(self, surface):
        global choices
        self.capture = False
        pg.mouse.set_visible(True)
        for event in pg.event.get():

            if event.type == pg.MOUSEBUTTONDOWN and not in_real_grid(event.pos):
                for i in self.move_rect_dict:
                    if self.move_rect_dict[i].collidepoint(event.pos):
                        self.clicked = self.move_rect_dict[i]
                        print(self.SAN_list[i])
                        print(board_dict[1][WHITE])
                        self.move_rect_loop(surface, i)
                        if self.clicked is not self.move_rect_dict[len(self.move_rect_dict)-1]:
                            self.mode = 'moves'
                        else:
                            self.mode = 'game'
                print(self.mode, self.clicked)

            elif event.type == pg.MOUSEBUTTONDOWN:
                if self.promote_pawn:
                    for choice in choices:
                        print(choice)
                        if choice.rect.collidepoint(event.pos):
                            self.promotion_choice = choice
                            print(self.promotion_choice, 'SPC')
                else:
                    for player in self.players:
                        if player.rect.collidepoint(event.pos):
                            try:
                                self.f_pos = SCREEN_TO_BOARD[position(event.pos)]
                                print('f_pos =', self.f_pos)
                                player.click = True
                            except KeyError or AttributeError:
                                print('nana')
            elif event.type == pg.MOUSEBUTTONUP:
                if self.promote_pawn:
                    try:
                        self.pawn_promotion()
                        self.promote_pawn = False
                    except AttributeError:
                        print('None is clicked - Pawn promotion')
                        self.promote_pawn = True
                else:
                    for player in self.players:
                        if (player.rect.collidepoint(event.pos) and
                                player.pos == self.f_pos):
                            try:
                                self.l_pos = SCREEN_TO_BOARD[position(event.pos)]
                                print('l_pos = ', self.l_pos)
                                if self.move() and self.mode == 'game':
                                    self.clicked = None

                                    player.rect.center = BOARD_TO_SCREEN[player.rank, player.file]
                                    self.turn, self.opponent = next(self.alternator)
                                    if self.check:
                                        if self.is_mate():
                                            self.SAN_list[-1] = self.SAN_list[-1].replace('+', '#')
                                            print('MATE')
                                    self.check = False
                                    self.FEN = self.get_FEN_position()
                                    stockfish.set_fen_position(self.FEN)
                                    if self.turn == WHITE:
                                        self.fullmove += 1
                                    if self.machine:
                                        self.engine = True
                                else:
                                    player.rect.center = BOARD_TO_SCREEN[self.f_pos]
                            except KeyError or AttributeError:
                                player.rect.center = BOARD_TO_SCREEN[self.f_pos]
                        player.click = False
            elif event.type == pg.QUIT or (
                    event.type == pg.KEYDOWN and event.key == pg.K_q):
                pg.quit()
                sys.exit()

    def move_rect_loop(self,surface, i):
        # Get move number and turn.
        try:
            move_no = int(self.SAN_list[i][0])
            turn = WHITE
        except ValueError:
            move_no = int(self.SAN_list[i-1][0])
            turn = BLACK

        # Get board state.
        ex_board = board_dict[move_no][turn]
        # Get start and end position.
        ex_move = self.move_dict[move_no][turn]
        # Get current captured pieces
        ex_captured_list = self.captured_dict[move_no][turn]
        # Start and end positions for the animation
        start = int(ex_move[:2][1]), ex_move[:2][0]
        end = int(ex_move[2:][1]), ex_move[2:][0]
        (x1, y1), (x, y) = BOARD_TO_SCREEN[end], BOARD_TO_SCREEN[start]
        # name the piece at the start position
        piece = ex_board.loc[start]
        # name the piece (if there is any) at the end position
        defender = ex_board.loc[end]
        # move the already captured pieces to the captured piece lounge
        self.move_captured_pieces(ex_captured_list)
        #print(ex_captured_list)
        #print(start, end, piece, defender)
        ex_players = []
        #print(ex_board)
        for rank in ranks:
            for file_ in files:
                if ex_board.loc[rank, file_]:
                    ex_board.loc[rank, file_].on_board = True
                    ex_player = ex_board.loc[rank, file_]

                    ex_player.image = pg.image.load(
                            f'pieces90px/{ex_player.symbol}.png')
                    ex_player.rect.center = (file_dict[file_], rank_dict[rank])
                    ex_players.append(ex_player)

        speed = (x1 - x) // 10, (y1 - y) // 10
        while piece.rect.center != (x1, y1):
            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.clicked)
            self.draw_current_board(surface, ex_players, start)

            piece.rect = piece.rect.move(speed)
            piece.update(surface)
            pg.display.update()
            clock.tick(100)

        if defender:
            self.move_captured_pieces([defender])


    def move_captured_pieces(self, captured_pieces):
        if captured_pieces:
            for captured in captured_pieces:
                y = 815
                if captured.color == WHITE:
                    y = 870
                if captured.symbol.upper() == 'P':
                    x = 925
                if captured.symbol.upper() == 'N':
                    x = 970
                if captured.symbol.upper() == 'B':
                    x = 1015
                if captured.symbol.upper() == 'R':
                    x = 1055
                if captured.symbol.upper() == 'Q':
                    x = 1100

                captured.image = pg.image.load(f'pieces50px/{captured.symbol}.png')
                captured.rect.center = x, y
                captured.on_board = False
                #captured.pos = captured.rank = captured.file = None

    def move(self):
        piece = board.loc[self.f_pos]
        defender = board.loc[self.l_pos]

        if piece and self.is_valid():
            # add current board to board dict
            if self.turn == WHITE:
                board_dict[self.fullmove] = {}
                board_dict[self.fullmove][self.turn] = deepcopy(board)
            else:
                board_dict[self.fullmove][self.turn] = deepcopy(board)

            # check if it's a pawn promotion
            if piece.symbol.upper() == 'P' and piece.rank == [2, 7][self.turn == WHITE]:
                self.promote_pawn = True

            # check if it's en passant 
            if self.en_passant:
                ep_pos = (self.f_pos[0], self.l_pos[1])
                self.captured_list.append(board.loc[ep_pos])
                board.loc[ep_pos].on_board = False
                self.capture = True
                self.move_captured_piece(-1)
                self.en_passant = False

            # check if there is capture and if there is move captured piece to
            # the captured piece lounge
            if defender:
                self.captured_list.append(defender)
                self.capture = True
                self.move_captured_piece(-1)
                defender.on_board = False

            self.get_algebraic_notation()
            board.loc[self.l_pos] = piece
            board.loc[self.f_pos] = 0
            board.loc[self.l_pos].pos = self.l_pos
            board.loc[self.l_pos].rank = self.l_pos[0]
            board.loc[self.l_pos].file = self.l_pos[1]

            self.update_castling_rights(piece.symbol)
            self.update_en_passant_target_square(piece.symbol, piece.file)
            self.update_halfmove_clock(piece.symbol)
            self.the_move = (self.f_pos[1] + str(self.f_pos[0]) +
                    self.l_pos[1] + str(self.l_pos[0]))

            if self.turn == WHITE:
                self.move_dict[self.fullmove] = {}
                self.move_dict[self.fullmove][self.turn] = self.the_move
                self.captured_dict[self.fullmove] = {}
                self.captured_dict[self.fullmove][self.turn] = self.captured_list[:]
            else:
                self.move_dict[self.fullmove][self.turn] = self.the_move
                self.captured_dict[self.fullmove][self.turn] = self.captured_list[:]
            return True
        return False

    def move_captured_piece(self, i):
        if self.captured_list:
            captured = self.captured_list[i]
            y = 815
            if captured.color == WHITE:
                y = 870
            if captured.symbol.upper() == 'P':
                x = 925
            if captured.symbol.upper() == 'N':
                x = 970
            if captured.symbol.upper() == 'B':
                x = 1015
            if captured.symbol.upper() == 'R':
                x = 1055
            if captured.symbol.upper() == 'Q':
                x = 1100
            if captured.symbol in [x.symbol for x in self.captured_list[:-1]] and \
                captured.symbol.upper() != 'P':
                x += 10
            captured.image = pg.image.load(f'pieces50px/{captured.symbol}.png')
            captured.rect.center = x, y
            captured.pos = captured.rank = captured.file = None



    def is_valid(self):
        piece = board.loc[self.f_pos]
        if piece.color != self.turn:
            print('Not ' + piece.color + '\'s turn!')
            return False

        #castle
        if piece.symbol.upper() == 'K' and self.can_castle():
            self.castle()
            return True

        if piece.symbol.upper() == 'P':
            if (self.l_pos in piece.available_moves() or \
                self.l_pos in piece.available_captures()) and \
                self.is_king_safe():
                return True
            #if it's an en passant move
            if self.l_pos == self.ep_square and self.is_king_safe() and \
                board.loc[self.f_pos[0], self.l_pos[1]].color != self.color and \
                (piece.rank + piece.direction == self.ep_square[0]) and \
                (abs(ord(piece.file) - ord(self.ep_square[1])) == 1):
                self.en_passant = True
                return True
        else:
            if self.l_pos in piece.available_moves() and self.is_king_safe():
                return True
        print('Move is not valid')
        return False

    def king_pos(self, turn):
        king_position = [self.players[4].pos, self.players[-4].pos][turn == WHITE]
        return king_position


    def can_castle(self):
        piece = board.loc[self.f_pos]
        f = ord(self.f_pos[1])
        f1 = ord(self.l_pos[1])
        if abs(f1 - f) != 2:
            return False
        try:
            diff = (f1 - f) // abs(f1 - f)
        except ZeroDivisionError:
            return False
        if self.f_pos[1] != 'e' and (
                                self.l_pos[1] != 'c' or self.l_pos[1] != 'g'):
            return False

        if self.l_pos[1] == 'c' and ( 
            (piece.symbol.isupper() and 'Q' not in self.castling_rights) 
            or 
            (piece.symbol.islower() and 'q' not in self.castling_rights)):
            print('queen side sikinti')
            return False
        if self.l_pos[1] == 'g' and ( 
            (piece.symbol.isupper() and 'K' not in self.castling_rights) 
            or 
            (piece.symbol.islower() and 'k' not in self.castling_rights)):
            print('king side sikinti')
            return False

        while 'a' <= chr(f) <= 'h':
            if self.square_safe(self.opponent, (self.f_pos[0], chr(f))):
                f += diff
                continue
            print((self.f_pos[0], chr(f)), 'sq safe sikinti', chr(f))
            return False

        return True

    def castle(self):
        """
        Moves the castled rook's rect and manages position information.
        Provides info for updating the castling rights.
        """
        global BOARD_TO_SCREEN, SCREEN_TO_BOARD
        if self.l_pos[1] == 'c':
            board.loc[self.l_pos[0], 'd'] = board.loc[self.l_pos[0], 'a']
            castled_rook = board.loc[self.l_pos[0], 'd'] 
            castled_rook.pos = (self.l_pos[0], 'd')
            castled_rook.rank, castled_rook.file = castled_rook.pos
            pos = castled_rook.pos
            castled_rook.rect.center = BOARD_TO_SCREEN[pos]
            board.loc[self.l_pos[0], 'a'] = 0
            self.castled_qs = True
        if self.l_pos[1] == 'g':
            board.loc[self.l_pos[0], 'f'] = board.loc[self.l_pos[0], 'h']
            castled_rook = board.loc[self.l_pos[0], 'f'] 
            castled_rook.pos = (self.l_pos[0], 'f')
            castled_rook.rank, castled_rook.file = castled_rook.pos
            pos = castled_rook.pos
            castled_rook.rect.center = BOARD_TO_SCREEN[pos]
            board.loc[self.l_pos[0], 'h'] = 0
            self.castled_ks = True

    def update_castling_rights(self, symbol):
        """
        Updates castling rights, when a castle happens.
        """
        if symbol == 'K' or (symbol == 'R' and self.f_pos[1] == 'a'):
            self.castling_rights = self.castling_rights.replace('Q', '')
        if symbol == 'K' or (symbol == 'R' and self.f_pos[1] == 'h'):
            self.castling_rights = self.castling_rights.replace('K', '')
        if symbol == 'k' or (symbol == 'r' and self.f_pos[1] == 'a'):
            self.castling_rights = self.castling_rights.replace('q', '')
        if symbol == 'k' or (symbol == 'r' and self.f_pos[1] == 'h'):
            self.castling_rights = self.castling_rights.replace('k', '')
        if self.castling_rights == '':
            self.castling_rights = '-'

    def update_en_passant_target_square(self, symbol, file_):
        if symbol.upper() == 'P' and abs(self.f_pos[0] - self.l_pos[0]) == 2:
            self.ep_square = (((self.f_pos[0] + self.l_pos[0]) // 2), file_)
        else:
            self.ep_square = '-'

    def update_halfmove_clock(self, symbol):
        if symbol.upper() == 'P' or self.capture:
            self.halfmove = 0
        else:
            self.halfmove += 1

    def is_king_safe(self):
        temp = board.loc[self.l_pos]
        if temp:
            temp.on_board = False
        piece = board.loc[self.f_pos]
        board.loc[self.f_pos] = 0
        board.loc[self.l_pos] = piece
        piece.pos = self.l_pos
        piece.rank, piece.file = self.l_pos
        safe = False
        king_position = self.king_pos(self.turn)

        if self.square_safe(self.opponent, king_position):
            safe = True
        if self.is_check() and safe:
            print('check')
            self.check = True

        piece.pos = self.f_pos
        piece.rank, piece.file = self.f_pos
        board.loc[self.f_pos] = piece
        board.loc[self.l_pos] = temp
        if temp:
            temp.on_board = True
        return safe

    def get_algebraic_notation(self):

        piece = board.loc[self.f_pos]#l_pos
        no = ''
        piece_type = piece.symbol.upper()
        f = '' # file
        r = '' # rank
        c = '' # capture
        end_pos = self.l_pos[1] + str(self.l_pos[0])
        check_mate = ''

        if self.turn == WHITE:
            no = str(self.fullmove) + '.'

        if piece.symbol.upper() == 'P':
            piece_type = ''
            if self.capture:
                f = piece.file
                c = 'x'
        else:
            #other piece(s) that can also see the same square
            other_players = []
            for player in self.players:
                if player.symbol == piece.symbol and player.pos != piece.pos \
                    and player.on_board and self.l_pos in player.available_moves():
                    other_players.append(player)
            if other_players:
                for player in other_players:
                    if piece.file != player.file:
                        f = piece.file
                    elif piece.file == player.file and piece.rank != player.rank:
                        r = str(piece.rank)
            if self.capture:
                c = 'x'

        if self.check:
            check_mate = '+'

        move_SAN = no + piece_type + f + r + c + end_pos + check_mate

        if self.castled_qs:
            move_SAN = no + '0-0-0'
            self.castled_qs = False
        if self.castled_ks:
            move_SAN = no + ' 0-0'
            self.castled_ks = False
        self.SAN_list.append(move_SAN)


    def get_FEN_position(self):
        fen = ''
        counter = 0
        #place pieces
        for rank in ranks:
            for file_ in files:
                piece = board.loc[rank, file_]
                if piece:
                    if counter:
                        fen += str(counter)
                    fen += piece.symbol
                    counter = 0
                else:
                    counter += 1
            if counter != 0:
                fen += str(counter)
            if rank != 1:
                fen += '/'
            else:
                fen += ' '

            counter = 0
        #side to move
        if self.turn == WHITE:
            fen += 'w '
        else:
            fen += 'b '
        #castling ability
        fen += self.castling_rights + ' '
        #en passant target square
        if self.ep_square == '-':
            fen += '- '
        else:
            fen += self.ep_square[1] + str(self.ep_square[0]) + ' '
        #halfmove clock
        fen += str(self.halfmove) + ' '
        #fullmove counter
        fen += str(self.fullmove)
        return fen



    def move_screen(self, surface):
        font = pg.font.SysFont('gentiumbookbasic', 30)
        font2 = pg.font.SysFont('gentiumbookbasic', 15)
        x, y = 886, 8
        self.move_rect_color = (255, 255, 255)
        self.after_click = (dark_square)
        if len(self.SAN_list) > 0:
            for i, san in enumerate(self.SAN_list):
                text = font.render(san, True, self.move_rect_color)
                text_rect = text.get_rect()

                if x + text_rect.width > 1104:
                    x = 886
                    y += 22
                self.move_rect_dict[i] = text_rect
                self.move_rect_dict[i].topleft = (x, y)
                x += text_rect.width + 4
                surface.blit(text, self.move_rect_dict[i])

        captured_b_pawns = str([i.symbol for i in a.captured_list].count('p'))
        captured_w_pawns = str([i.symbol for i in a.captured_list].count('P'))

        if int(captured_b_pawns) > 1:
            b_pawn_no = font2.render(captured_b_pawns, True, (250, 250, 250))
            b_pawn_no_rect = b_pawn_no.get_rect(center=(902, 767))
            surface.blit(b_pawn_no, b_pawn_no_rect)
        if int(captured_w_pawns) > 1:
            w_pawn_no = font2.render(captured_w_pawns, True, (250, 250, 250))
            w_pawn_no_rect = w_pawn_no.get_rect(center=(902, 825))
            surface.blit(w_pawn_no, w_pawn_no_rect)

    def engine_main_loop(self, surface):
        engine_move = stockfish.get_best_move()
        start, end = engine_move[:2], engine_move[2:]
        self.f_pos = int(start[1]), start[0]
        self.l_pos = int(end[1]), end[0]
        (x1, y1), (x, y) = BOARD_TO_SCREEN[self.l_pos], BOARD_TO_SCREEN[self.f_pos]
        piece = board.loc[self.f_pos]
        defender = board.loc[self.l_pos]
        speed = (x1 - x) // 10, (y1 - y) // 10
        while piece.rect.center != (x1, y1):
            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.clicked)
            self.draw_current_board(surface, self.players, self.f_pos)

            piece.rect = piece.rect.move(speed)
            piece.update(surface)
            pg.display.update()
            clock.tick(40)

        if self.en_passant:
            ep_pos = (self.f_pos[0], self.l_pos[1])
            ep_defender = board.loc[ep_pos]
            self.captured_list.append(ep_defender)
            self.capture = True
            ep_defender.on_board = False
            self.move_captured_piece(-1)
            self.en_passant = False

        if defender:
            self.captured_list.append(defender)
            self.capture = True
            self.move_captured_piece(-1)
            defender.on_board = False

        self.get_algebraic_notation()
        board.loc[self.l_pos] = piece
        board.loc[self.f_pos] = 0
        self.update_castling_rights(piece.symbol)
        self.update_en_passant_target_square(piece.symbol, piece.file)
        self.update_halfmove_clock(piece.symbol)

        self.the_move = self.f_pos[1] + str(self.f_pos[0]) + \
                        self.l_pos[1] + str(self.l_pos[0])

        self.move_dict[self.fullmove][self.turn] = self.the_move

        piece.rank, piece.file = piece.pos = self.l_pos

        self.turn, self.opponent = next(self.alternator)
        self.FEN = self.get_FEN_position()
        stockfish.set_fen_position(self.FEN)
        if self.turn == WHITE:
            self.fullmove += 1

    def pawn_promotion(self):
        for player in self.players:
            if player.pos == self.l_pos:
                _ind = self.players.index(player)
                del self.players[_ind]
        pc = self.promotion_choice
        pc.image = pg.image.load(self.promotion_choice.image_path)
        pc.pos = self.l_pos
        pc.rank, pc.file = self.l_pos
        pc.rect.center = (file_dict[pc.file], rank_dict[pc.rank])
        self.players.append(pc)
        board.loc[self.l_pos] = pc

class Piece:
    def __init__(self, symbol, pos):
        self.symbol = symbol
        if self.symbol.isupper():
            self.color = WHITE
        else:
            self.color = BLACK
        self.rect = pg.Rect((0, 0, 90, 90))
        self.click = False

        self.image_path = 'pieces90px/' + self.symbol + '.png'
        self.image = pg.image.load(self.image_path)#.convert_alpha()
        #self.image = pg.transform.rotozoom(i, 0, 0.9)
        self.pos = pos
        self.rank, self.file = self.pos
        self.on_board = True

    def update(self, surface):

        if self.click:
            pg.mouse.set_visible(False)
            self.rect.topleft = pg.mouse.get_pos()[0] - 50, pg.mouse.get_pos()[1] - 60
        surface.blit(self.image, self.rect)

    def __repr__(self):
        return self.symbol

    #def pawn_promotion(self, choice):
    #    print(choice, 'HCOICE')
    #    #self.pos = self.rank, self.file = pos
    #    self.image = pg.image.load('pieces90px/{choice.__repr__}.png')



    #find all available locations for rook, bishop and queen
    def available_pos_list(self, directions):
        #pos_list = []
        for dir_r, dir_f in iter(directions):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            while 1:
                try:
                    if not board.loc[temp_r, temp_f]:
                        #pos_list.append((temp_r, temp_f))
                        yield (temp_r, temp_f)
                    elif board.loc[temp_r, temp_f].color != self.color:
                        #pos_list.append((temp_r, temp_f))
                        yield (temp_r, temp_f)
                        break
                    else:
                        break
                    temp_f = chr(ord(temp_f) + dir_f)
                    temp_r += dir_r
                except KeyError:
                    break
        #return pos_list

class Rook(Piece):
    def available_moves(self):
        return self.available_pos_list(cardinal_dir)

class Knight(Piece):
    def available_moves(self):
        #pos_list = []
        for dir_r, dir_f in iter(knight_dir):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            try:
                if not board.loc[temp_r, temp_f] or \
                    board.loc[temp_r, temp_f].color != self.color:
                    yield (temp_r, temp_f)
                    #pos_list.append((temp_r, temp_f))
            except KeyError or AttributeError:
                continue
        #return pos_list

class Bishop(Piece):
    def available_moves(self):
        return self.available_pos_list(diagonal_dir)

class Queen(Piece):
    def available_moves(self):
        return self.available_pos_list(queen_dir)

class King(Piece):
    def available_moves(self):
        #pos_list = []
        for dir_r, dir_f in iter(queen_dir):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            try:
                if not board.loc[temp_r, temp_f] or \
                    board.loc[temp_r, temp_f].color != self.color:
                    yield (temp_r, temp_f)
            except KeyError or AttributeError:
                continue

class Pawn(Piece):
    def available_moves(self):
        self.direction = [-1, 1][self.symbol.isupper()]
        if self.rank == 2 and self.color == WHITE or \
            self.rank == 6 or self.color == BLACK:
            temp_f = self.file
            temp_r = self.rank + 2 * self.direction
            if board.loc[temp_r, temp_f] == 0:
                yield (temp_r, temp_f)

        if 2 <= self.rank <= 7:
            temp_r, temp_f = self.rank + self.direction, self.file
            if board.loc[temp_r, temp_f] == 0:
                yield (temp_r, temp_f)

    def available_captures(self):
        if self.symbol.isupper():
            self.direction = 1
        else:
            self.direction = -1

        if 2 <= self.rank <= 7:
            for i in [-1, 1]:
                temp_r, temp_f = self.rank + self.direction, chr(ord(self.file) + i)
                try:
                    defender = board.loc[temp_r, temp_f]
                    if defender and defender.color != self.color:
                        yield (temp_r, temp_f)
                except KeyError:
                    continue

    def can_capture(self):
        if self.symbol.isupper():
            self.direction = 1
        else:
            self.direction = -1
        if self.on_board and 2 <= self.rank <= 7:
            for i in [-1, 1]:
                temp_r, temp_f = self.rank + self.direction, chr(ord(self.file) + i)
                if 1 <= temp_r <= 8 and 'a' <= temp_f <= 'h':
                    yield (temp_r, temp_f)

def place_pieces():
    pieces = {'a': Rook, 'b': Knight, 'c': Bishop, 'd': Queen, \
            'e': King, 'f': Bishop, 'g': Knight, 'h': Rook}
    for rank in iter(ranks):
        for file_ in iter(files):
            if rank == 1:
                symbol = symbols[pieces[file_]].upper()
                board.loc[rank, file_] = pieces[file_](symbol, (rank, file_))
            if rank == 8:
                symbol = symbols[pieces[file_]]
                board.loc[rank, file_] = pieces[file_](symbol, (rank, file_))
            if rank == 2:
                symbol = symbols[Pawn].upper()
                board.loc[rank, file_] = Pawn(symbol, (rank, file_))
            if rank == 7:
                symbol = symbols[Pawn]
                board.loc[rank, file_] = Pawn(symbol, (rank, file_))

            if board.loc[rank, file_]:
                board.loc[rank, file_].rect.center = (file_dict[file_], rank_dict[rank])
                yield board.loc[rank, file_]

def draw_promote_choices(surface, pos, turn):
    choices = ['qQ', 'rR', 'nN', 'bB', Queen, Rook, Knight, Bishop]
    x = BOARD_TO_SCREEN[pos][0]
    if x > 550:
        x = 550

    y = [800, 0][turn == WHITE]
    szbtwn = 80
    rect = pg.Rect(x, y, 4*szbtwn, szbtwn)
    pg.draw.rect(surface, dark_square, rect)
    for i in range(4):
        choices[i+4] = choices[i+4](choices[i][turn == WHITE], (x, y))
        choices[i+4].image = pg.transform.rotozoom(choices[i+4].image, 0, 0.70)
        choices[i+4].rect.topleft = (x+5, y+8)
        x += 80
    x-=320
    pg.draw.lines(surface, (20, 20, 20), True, ((x, y), (x + 4*szbtwn, y), 
                                                (x + 4*szbtwn, y + szbtwn), 
                                                    (x, y + szbtwn)), 4 )
    return choices[4:]









if __name__ == "__main__":
    # Set window position
    os.environ['SDL_VIDEO_WINDOW_POS'] = '800,25'
    # Initialize pygame
    pg.init()

    # Set pygame window caption
    pg.display.set_caption('Chess')
    # Set clock
    clock = pg.time.Clock()
    # Set display mode
    screen = pg.display.set_mode((1113, 881))

    # Define colors of sides, it's used while naming turns and pieces
    BLACK = 'black'
    WHITE = 'white'

    # Default initial board position in Forsyth-Edwards Notation (FEN) 
    initial_FEN_position = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    # Directions for generating the available moves for major pieces.
    diagonal_dir = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
    cardinal_dir = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    queen_dir = diagonal_dir + cardinal_dir
    knight_dir = [(2, 1), (2, -1), (-2, 1), (-2, -1), \
            (1, 2), (-1, 2), (1, -2), (-1, -2)]

    # Board representation. Pandas dataFrame used for easy square naming 
    board = pd.DataFrame(np.zeros((8, 8), dtype=int),
            index=[8, 7, 6, 5, 4, 3, 2, 1],
            columns=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
    ranks = board.index
    files = board.columns
    symbols = {Rook: 'r', Knight: 'n', Bishop: 'b',
            Queen: 'q', King: 'k', Pawn: 'p'}

    real_positions = [90, 190, 290, 390, 490, 590, 690, 790]
    file_dict = dict(zip(files, real_positions))
    rank_dict = dict(zip(ranks, real_positions))

    BOARD_TO_SCREEN = {}
    SCREEN_TO_BOARD = {}
    for rank in ranks:
        for file_ in files:
            SCREEN_TO_BOARD[(file_dict[file_], rank_dict[rank])] = (rank, file_)
            BOARD_TO_SCREEN[(rank, file_)] = (file_dict[file_], rank_dict[rank])
    board_dict = {}
    #engine
    stockfish = Stockfish('stockfish')


    a = Game()
    while 1:
        a.main(screen)
