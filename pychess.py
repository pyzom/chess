import numpy as np
import pandas as pd
import os
import sys
import pygame as pg
from stockfish import Stockfish
from copy import deepcopy
from itertools import chain
from draw_chess_board import *

def alternate_turn():
    while 1:
        yield BLACK, WHITE
        yield WHITE, BLACK

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
        self.engine_level = stockfish.set_skill_level(5)
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
        return True

    def square_safe(self, turn, pos):
        for player in self.players:
            if player.color == turn and player.on_board:
                if (player.symbol.upper() == 'P' and
                    pos in player.can_capture()):
                    return False
                elif (player.symbol.upper() != 'P' and
                      pos in player.available_moves()):
                    return False
        return True

    def draw_current_board(self, surface, players, start):
        for player in players:
            if player.pos != start and player.on_board:
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
        MyClock.tick(60)

    def game_event_loop(self, surface):
        global choices
        self.capture = False
        pg.mouse.set_visible(True)
        for event in pg.event.get():

            if event.type == pg.MOUSEBUTTONDOWN and not in_real_grid(event.pos):
                for i in self.move_rect_dict:
                    if self.move_rect_dict[i].collidepoint(event.pos):
                        self.mode = 'moves'
                        self.clicked = self.move_rect_dict[i]
                        print(self.SAN_list[i])
                        print(board_dict[(i+2)/2][[WHITE, BLACK][i%2 == 0]])
                        self.move_rect_loop(surface, i)
                        if self.clicked is self.move_rect_dict[len(self.move_rect_dict)-1]:
                            self.mode = 'game'
                        else:
                            self.mode = 'moves'

            elif event.type == pg.MOUSEBUTTONDOWN:
                if self.promote_pawn:
                    for choice in choices:
                        if choice.rect.collidepoint(event.pos):
                            print(event.pos)
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
                    if self.promotion_choice != None:
                        self.pawn_promotion()
                    self.promote_pawn = False
                else:
                    for player in self.players:
                        if (player.rect.collidepoint(event.pos) and
                            player.pos == self.f_pos):
                            try:
                                self.l_pos = SCREEN_TO_BOARD[position(event.pos)]
                                print('l_pos = ', self.l_pos)
                                if self.move():
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
            elif event.type == pg.QUIT:
                pg.quit()
                sys.exit()


    def pawn_promotion(self): 
        choice = self.promotion_choice
        choice.pos = self.l_pos
        choice.rank, choice.file = choice.pos
        choice.image = pg.image.load(f'pieces90px/{choice}.png')
        for player in self.players:
            if player.pos == self.l_pos:
                index_ = self.players.index(player)
                choice.rect.center = player.rect.center
        del self.players[index_]
        self.players.insert(index_, choice)
        board.loc[self.l_pos] = choice

    def move_rect_loop(self,surface, i):
        try:
            move_no = int(self.SAN_list[i][0])
            turn = WHITE
        except ValueError:
            move_no = int(self.SAN_list[i-1][0])
            turn = BLACK

        ex_board = board_dict[move_no][turn]
        ex_move = self.move_dict[move_no][turn]
        ex_captured_list = self.captured_dict[move_no][turn]
        start = int(ex_move[:2][1]), ex_move[:2][0]
        end = int(ex_move[2:][1]), ex_move[2:][0]
        (x1, y1), (x, y) = BOARD_TO_SCREEN[end], BOARD_TO_SCREEN[start]
        piece = ex_board.loc[start]
        defender = ex_board.loc[end]
        self.move_captured_pieces(ex_captured_list)
        #print(ex_captured_list)
        #print(start, end, piece, defender)
        ex_players = []
        #print(ex_board)
        for rank in ranks:
            for file_ in files:
                if ex_board.loc[rank, file_] and not defender:
                    ex_board.loc[rank, file_].on_board = True

                    ex_board.loc[rank, file_].image = \
                        pg.image.load(f'pieces90px/{ex_board.loc[rank, file_].symbol}.png')
                    ex_board.loc[rank, file_].rect.center = (file_dict[file_], rank_dict[rank])
                    ex_players.append(ex_board.loc[rank, file_])

        speed = (x1 - x) // 10, (y1 - y) // 10
        while piece.rect.center != (x1, y1):
            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.clicked)
            self.draw_current_board(surface, ex_players, start)

            piece.rect = piece.rect.move(speed)
            piece.update(surface)
            pg.display.update()
            MyClock.tick(100)

        if defender:
            defender.rect.center = 900, 800
            defender = 0

    def move_captured_pieces(self, captured_pieces):
        if captured_pieces:
            for captured in captured_pieces:
                y = 815
                if captured.color == WHITE:
                    y = 870
                if captured == 'P':
                    x = 925
                if captured == 'N':
                    x = 970
                if captured == 'B':
                    x = 1015
                if captured == 'R':
                    x = 1055
                if captured == 'Q':
                    x = 1100

                captured.image = pg.image.load(f'pieces50px/{captured.symbol}.png')
                captured.rect.center = x, y
                captured.on_board = False
                #captured.pos = captured.rank = captured.file = None

    def move(self):
        piece = board.loc[self.f_pos]
        defender = board.loc[self.l_pos]

        if piece and self.is_valid() and self.mode == 'game':
            if self.turn == WHITE:
                board_dict[self.fullmove] = {}
                board_dict[self.fullmove][self.turn] = deepcopy(board)
            else:
                board_dict[self.fullmove][self.turn] = deepcopy(board)

            if piece.symbol.upper() == 'P' and piece.rank == [2, 7][self.turn == WHITE]:
                self.promote_pawn = True

            if self.en_passant:
                ep_pos = (self.f_pos[0], self.l_pos[1])
                self.captured_list.append(board.loc[ep_pos])
                board.loc[ep_pos].on_board = False
                self.capture = True
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
            if self.l_pos in piece.available_moves() and \
                self.is_king_safe():
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
        if self.f_pos[1] != 'e' and (self.l_pos[1] != 'c' or self.l_pos[1] != 'g'):
            return False

        if self.l_pos[1] == 'c' and \
            ((piece.symbol.isupper() and 'Q' not in self.castling_rights) or \
             (piece.symbol.islower() and 'q' not in self.castling_rights)):
                print('queen side sikinti')
                return False
        if self.l_pos[1] == 'g' and \
            ((piece.symbol.isupper() and 'K' not in self.castling_rights) or \
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
        global BOARD_TO_SCREEN, SCREEN_TO_BOARD
        if self.l_pos[1] == 'c':
            board.loc[self.l_pos[0], 'd'] = board.loc[self.l_pos[0], 'a']
            board.loc[self.l_pos[0], 'd'].pos = (self.l_pos[0], 'd')
            pos = board.loc[self.l_pos[0], 'd'].pos
            board.loc[self.l_pos[0], 'd'].rect.center = BOARD_TO_SCREEN[pos]
            board.loc[self.l_pos[0], 'a'] = 0
            self.castled_qs = True
        if self.l_pos[1] == 'g':
            board.loc[self.l_pos[0], 'f'] = board.loc[self.l_pos[0], 'h']
            board.loc[self.l_pos[0], 'f'].pos = (self.l_pos[0], 'f')
            pos = board.loc[self.l_pos[0], 'f'].pos
            board.loc[self.l_pos[0], 'f'].rect.center = BOARD_TO_SCREEN[pos]
            board.loc[self.l_pos[0], 'h'] = 0
            self.castled_ks = True

    def update_castling_rights(self, symbol):
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
        font = pg.font.SysFont('gentiumbookbasic', 20)
        font2 = pg.font.SysFont('gentiumbookbasic', 15)
        x, y = 886, 8
        self.move_rect_color = (200, 220, 220)
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
            MyClock.tick(40)

        if self.en_passant:
            ep_pos = (self.f_pos[0], self.l_pos[1])
            self.captured_list.append(board.loc[ep_pos])
            self.capture = True
            self.move_captured_piece(-1)
            self.en_passant = False

        if defender:
            self.captured_list.append(defender)
            self.capture = True
            self.move_captured_piece(-1)

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

    #    self.image = pg.image.load(f'pieces90px/{choice}.png')
    #    self.symbol = choice.symbol


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

class Rook(Piece):
    def available_moves(self):
        return self.available_pos_list(cardinal_dir)

class Knight(Piece):
    def available_moves(self):
        for dir_r, dir_f in iter(knight_dir):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            try:
                if not board.loc[temp_r, temp_f] or \
                    board.loc[temp_r, temp_f].color != self.color:
                    yield (temp_r, temp_f)
            except KeyError or AttributeError:
                continue

class Bishop(Piece):
    def available_moves(self):
        return self.available_pos_list(diagonal_dir)

class Queen(Piece):
    def available_moves(self):
        return self.available_pos_list(queen_dir)

class King(Piece):
    def available_moves(self):
        for dir_r, dir_f in iter(queen_dir):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            try:
                if not board.loc[temp_r, temp_f] \
                or board.loc[temp_r, temp_f].color != self.color:
                    #pos_list.append((temp_r, temp_f))
                    yield (temp_r, temp_f)
            except KeyError or AttributeError:
                continue

class Pawn(Piece):
    def available_moves(self):
        self.direction = [-1, 1][self.symbol.isupper()]
        # if self.symbol.isupper():
        #     self.direction = 1
        # else:
        #     self.direction = -1
        if self.rank == 2 and self.color == WHITE or \
            self.rank == 7 and self.color == BLACK:
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
        if 2 <= self.rank <= 7 and self.on_board:
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
    pg.draw.lines(surface, (20, 20, 20), True, ((x, y), (x + 4*szbtwn, y), \
                                                (x + 4*szbtwn, y + szbtwn), \
                                                    (x, y + szbtwn)), 4 )
    return choices[4:]


def position(pos):
    pos = list(pos)
    for i,ind in enumerate(pos):
        if ind <= 100 * (ind // 100) + 40:
            pos[i] = 100 * (pos[i] // 100) - 10
        else:
            pos[i] = 100 * (pos[i] // 100) + 90

    return tuple(pos)

def in_real_grid(pos):
        if 40 <= pos[0] <= 840 and 40 <= pos[1] <= 840:
            return True
        return False

light_square = (232, 235, 239)
dark_square = (125, 135, 150)
BLACK = 'black'
WHITE = 'white'

def draw_frame(Surface):
    pg.draw.polygon(Surface, (31,31,31), [(0,0), (40,40), (840,40), (840,840), (880,880),(880,0)])
    pg.draw.polygon(Surface, (31,31,31), [(0,0), (40,40), (40,840), (840,840), (880,880),(0,880)])
    font = pg.font.SysFont('gentiumbookbasic', 30)
    letters = iter('ABCDEFGH')
    numbers = iter('12345678')
    # if turn == 1:
    #     letters = list(reversed(letters))
    #     numbers = list(reversed(numbers))
    for i, number in enumerate(numbers):
        x, y = 790, 18
        text = font.render(number, True, light_square)
        text_rect = text.get_rect(center=(y,x-(i)*100))
        Surface.blit(text, text_rect)

    for i,letter in enumerate(letters):
        x, y = 90, 20
        text = font.render(letter, True, light_square)
        text_rect = text.get_rect(center=(x+i*100,y))
        Surface.blit(text, text_rect)

def draw_squares(Surface):
    x, y = 40, 40
    szbtwn = 100
    dark = False
    for i in iter((0, 2, 4, 6, 1, 3, 5, 7)):
        if i == 1:
            dark = True
        for j in range(8):
            rect = pg.Rect(x+j*szbtwn, y+i*szbtwn, szbtwn, szbtwn)
            if dark == True:
                pg.draw.rect(Surface, dark_square, rect)
                dark = False
            else:
                pg.draw.rect(Surface, light_square, rect)
                dark = True

def draw_move_screen(Surface, clicked_move_rect):
    rect = pg.Rect(881, 0, 232, 749)
    pg.draw.rect(Surface, (31, 37, 37), rect)
    rect = pg.Rect(881, 749, 232, 132)
    pg.draw.rect(Surface, (70, 70, 70), rect)
    pg.draw.lines(Surface, light_square, True, ((880, 0), (880, 880), (1112, 880), (1112, 0)), 1)
    pg.draw.lines(Surface, light_square, True, ((882, 2), (882, 748), (1110, 748), (1110, 2)), 1)
    pg.draw.lines(Surface, light_square, True, ((882, 878), (882, 750), (1110, 750), (1110, 878)), 1)
    if clicked_move_rect:
        rect = pg.Rect(clicked_move_rect)
        pg.draw.rect(Surface, (70, 70, 70), rect)

 


if __name__ == "__main__":
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pg.init()
    MyClock = pg.time.Clock()
    pg.display.set_caption('Chess')
    light_square = (232, 235, 239)
    dark_square = (125, 135, 150)
    Screen = pg.display.set_mode((1113, 881), pg.RESIZABLE)
    BLACK = 'black'
    WHITE = 'white'
    MyClock = pg.time.Clock()
    initial_FEN_position = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    # Directions for generating the available positions for bishops, rooks, queens,
        #knights and kings (same as the queens' directions)
    diagonal_dir = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
    cardinal_dir = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    queen_dir = diagonal_dir + cardinal_dir
    knight_dir = [(2, 1), (2, -1), (-2, 1), (-2, -1), \
                  (1, 2), (-1, 2), (1, -2), (-1, -2)]

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
    stockfish = Stockfish('/usr/bin/stockfish')


    a = Game()
    while 1:
        a.main(Screen)
