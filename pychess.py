# import pygame_gui as pgui
import numpy as np
import pandas as pd
import os
import sys
import pygame as pg
from stockfish import Stockfish
from copy import deepcopy
from itertools import chain
from draw_chess_board import *
# from gui import Gui


class Game:

    onoff = button_onoff()
    def __init__(self):
        self.alternator = alternate_turn()
        # board representation in Forsyth-Edwards-Notation (FEN)
        self.FEN = initial_FEN_position
        # stockfish.set_fen_position(initial_FEN_position)
        self.position_dict = {1: initial_FEN_position}

        self.players = list(initial_setup_pieces())
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
        self.SAN_list = []

        self.check = False
        self.stale_mate = False
        self.captured_list = []
        self.engine = False

        self.machine = False
        self.f_pos = None
        self.l_pos = None
        self.the_move = None
        self.promote_pawn = False
        self.promotion_choice = ''
        self.clicked = None

    def load_game(self, moves, surface):
        for move in moves:
            self.capture = False
            self.f_pos = int(move[:2][1]), move[:2][0]
            self.l_pos = int(move[2:4][1]), move[2:4][0]

            try:
                ch = move[4]
                self.promotion_choice = {
                        'q': Queen, 'r': Rook, 'n': Knight, 'b': Bishop}[ch](
                        [ch, ch.upper()][self.turn == WHITE], self.l_pos)
            except IndexError: pass

            if board.loc[self.f_pos] and self.is_valid():
                self.move(surface)
            else:
                print(self.fullmove, move, 'invalid move')

        self.mode = 'game'

    def main(self, surface):

        global choices
        draw_frame(surface)
        draw_squares(surface)

        if self.mode == 'game' or self.mode == 'quit':
            draw_move_screen(surface, self.captured_list)        
        elif self.mode == 'moves':
            draw_move_screen(surface, self.datcaptured_list)        

        move_rect_screen(surface, self.clicked, dicts.move_rects, self.SAN_list)

        if self.engine:
            self.engine_main_loop(surface)
            self.engine = False

        self.game_event_loop(surface)

        if self.mode == 'moves':
            for player in self.datplayers:
                player.update(surface)
        else: #if self.mode == 'game' or 'load' or 'quit':
            for player in self.players:
                player.update(surface)
            

        pg.display.update()
        clock.tick(60)

        if self.mode == 'load':
            self.load_game(moves, surface)

    def game_event_loop(self, surface):
        global choices
        self.capture = False
        pg.mouse.set_visible(True)
        for event in pg.event.get():

            if event.type == pg.MOUSEBUTTONDOWN and not in_real_grid(event.pos):
                for rect in dicts.move_rects:
                    if dicts.move_rects[rect].collidepoint(event.pos):
                        self.ind_ = rect
                        self.clicked = dicts.move_rects[rect]
                        self.move_rect_loop(surface, self.ind_)
                        if (rect != len(dicts.move_rects) - 1):
                            self.mode = 'moves'
                        else:
                            self.mode = 'game'
                            self.clicked = None
            
            elif event.type == pg.KEYDOWN and event.key == pg.K_b:
                print("b is pressed")
                if not self.clicked and len(dicts.move_rects) > 1:
                    self.ind_ = len(dicts.move_rects) - 2
                    self.clicked = dicts.move_rects[self.ind_]
                    self.move_rect_loop(surface, self.ind_)
                    self.mode = 'moves'

                elif self.clicked and self.ind_ > 0:
                    self.ind_ -= 1
                    self.clicked = dicts.move_rects[self.ind_]
                
                    self.move_rect_loop(surface, self.ind_)
                    print(self.ind_)

            elif event.type == pg.KEYDOWN and event.key == pg.K_f:
                print("f is pressed")
                if self.clicked and (self.ind_ < len(dicts.move_rects) - 1):
                    self.ind_ += 1

                    self.clicked = dicts.move_rects[self.ind_]
                
                    self.move_rect_loop(surface, self.ind_)
                    print(self.ind_)
                    if self.ind_ == len(dicts.move_rects) - 1:
                        self.clicked = None
                        self.mode = 'game'

            elif event.type == pg.MOUSEBUTTONDOWN and self.mode == 'game':
                for player in self.players:
                    if player.rect.collidepoint(event.pos):
                        try:
                            self.f_pos = SCREEN_TO_BOARD[position(event.pos)]
                            print(event.pos, position(event.pos))
                            player.click = True
                        except (KeyError, AttributeError): pass

            elif event.type == pg.MOUSEBUTTONUP and self.mode == 'game':
                for player in self.players:
                    if (player.rect.collidepoint(event.pos) and
                                                player.pos == self.f_pos):
                        try:
                            self.l_pos = SCREEN_TO_BOARD[position(event.pos)]

                            if board.loc[self.f_pos] and self.is_valid():
                                self.move(surface)
                            else:
                                player.rect.center = BOARD_TO_SCREEN[self.f_pos]

                        except (KeyError, AttributeError):
                            player.rect.center = BOARD_TO_SCREEN[self.f_pos]

                    player.click = False

            
            elif (event.type == pg.KEYDOWN and event.key == pg.K_p and
                    self.mode == 'game'):
                if self.machine == True:
                    self.machine = False
                else:
                    self.machine = True
                    self.engine = True




            elif (event.type == pg.QUIT or 
                    (event.type == pg.KEYDOWN and event.key == pg.K_q)):
                pg.quit(); sys.exit()

            # Spawn shadow 
            elif (event.type == pg.KEYDOWN and event.key == pg.K_SPACE and 
                    self.mode == 'game'):
                self.shadow_loop(surface)

            # Spawn quit/save menu
            elif (event.type == pg.KEYDOWN and event.key == pg.K_g):
                print('g is pressed') 

            # Spawn welcome menu
            elif (event.type == pg.KEYDOWN and event.key == pg.K_w):
                print('w is pressed spawn welcome ')


            # Enable move with text input
            elif (event.type == pg.KEYDOWN and event.key == pg.K_RETURN and
                    self.mode == 'game'):
                move = self.text_input_loop(surface)
                print(move)
                if move:
                    self.move_with_text(surface, move)
            

    def move_with_text(self, surface, move):
        f_pos = int(move[1]), move[0]
        l_pos = int(move[3]), move[2]
        try:
            if board.loc[f_pos].color == self.turn:
                self.f_pos = f_pos
                print(self.f_pos)
            self.l_pos = l_pos
            if board.loc[self.f_pos] and self.is_valid():
                self.move(surface)
        except (KeyError, AttributeError):
            print('invalid move')

    def text_input_loop(self, surface):
        yellow = (250, 189, 47)
        frame_color = (40, 40, 40)
        font = pg.font.SysFont('dejavuserif', 32)
        rect = pg.Rect(440, 841, 100, 38)
        text = ''
        text_rect = font.render(text, True, yellow)
        crashed = False
        nums = '12345678'
        chrs = 'abcdefgh'

        while not crashed:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN and len(text) == 4:
                        return text
                    elif event.key == pg.K_BACKSPACE:
                        text = text[:-1]
                    elif event.key == pg.K_ESCAPE or event.key ==  pg.K_q:
                        crashed = True
                    else:
                        if ((len(text) == 0 or len(text) == 2) and 
                                event.unicode in chrs):
                            text += event.unicode
                        elif ((len(text) == 1 or len(text) == 3) and 
                                event.unicode in nums):
                            text += event.unicode

                    text_rect = font.render(text, True, yellow)

            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.captured_list)
            move_rect_screen(surface, self.clicked, dicts.move_rects, self.SAN_list)

            surface.blit(text_rect, (rect.x+15, rect.y))
            pg.draw.rect(surface, yellow, rect, 1)

            for player in self.players:
                player.update(surface)

            pg.display.update()
            clock.tick()

    def shadow_loop(self, surface):
        crashed = False
        red = (157, 0, 5)
        blue = (7, 102, 120)

        x, y = BOARD_TO_SCREEN[self.king_pos(self.turn)]
        x, y = x - 50, y - 50
        x_change = 0
        y_change = 0
        color = red

        while not crashed:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_h or event.key == pg.K_LEFT:
                        x_change = -100
                    elif event.key == pg.K_j or event.key == pg.K_DOWN:
                        y_change = 100
                    elif event.key == pg.K_k or event.key == pg.K_UP:
                        y_change = -100
                    elif event.key == pg.K_l or event.key == pg.K_RIGHT:
                        x_change = 100
                    elif event.key == pg.K_q or event.key == pg.K_ESCAPE:
                        crashed = True
                if event.type == pg.KEYUP:
                    if (event.key == pg.K_h or event.key == pg.K_LEFT or
                        event.key == pg.K_j or event.key == pg.K_DOWN or
                        event.key == pg.K_k or event.key == pg.K_UP or
                        event.key == pg.K_l or event.key == pg.K_RIGHT):
                        x_change = 0
                        y_change = 0
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and color == red:
                    pos = x + 50, y + 50
                    try:
                        f_pos = SCREEN_TO_BOARD[pos]
                        if board.loc[f_pos].color == self.turn:
                            self.f_pos = f_pos
                            color = blue
                    except: pass
                elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE and color == blue:
                    pos = x + 50, y + 50
                    try:
                        print(self.f_pos)
                        self.l_pos = SCREEN_TO_BOARD[pos]
                        if self.is_valid():
                            self.move(surface)
                            # color = red
                            crashed = True
                        else:
                            color = red
                    except (KeyError, AttributeError):pass

                draw_frame(surface)
                draw_squares(surface)
                draw_move_screen(surface, self.captured_list)
                move_rect_screen(surface, self.clicked, dicts.move_rects, self.SAN_list)

                if 40 <= x+x_change <= 740:
                    x += x_change
                if 40 <= y+y_change <= 740:
                    y += y_change

                if color == blue:
                    print(color, self.f_pos)
                    x2, y2 = BOARD_TO_SCREEN[self.f_pos]
                    x2, y2 = x2 - 50, y2 - 50
                    rect2 = pg.Rect((x2, y2), (100, 100))
                    pg.draw.rect(surface, red, rect2)

                rect = pg.Rect((x,y), (100, 100))
                pg.draw.rect(surface, color, rect)

                for player in self.players:
                    player.update(surface)

                pg.display.update()
                clock.tick()

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
                board.loc[self.f_pos[0], self.l_pos[1]].color != self.turn and \
                (piece.rank + piece.direction == self.ep_square[0]) and \
                (abs(ord(piece.file) - ord(self.ep_square[1])) == 1):
                self.en_passant = True
                return True
        else:
            if self.l_pos in piece.available_moves() and self.is_king_safe():
                return True
        print('Move is not valid')
        return False

    def is_king_safe(self):
        temp = board.loc[self.l_pos]
        if temp:
            temp.on_board = False
        piece = board.loc[self.f_pos]
        board.loc[self.f_pos] = 0
        board.loc[self.l_pos] = piece
        piece.rank, piece.file = piece.pos = self.l_pos
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

    def move(self, surface):#, surface):
        """
        
        """
        piece = board.loc[self.f_pos]
        defender = board.loc[self.l_pos]

        # add current board to board dict
        dicts.save_board(self.fullmove, self.turn, deepcopy(board))

        # check if it's en passant 
        if self.en_passant:
            ep_pos = (self.f_pos[0], self.l_pos[1])
            self.captured_list.append(board.loc[ep_pos])
            board.loc[ep_pos].on_board = False
            self.capture = True
            move_captured_piece(-1, self.captured_list)
            self.en_passant = False
            board.loc[ep_pos] = 0

        # check if there is capture and if there is move captured piece to
        # the captured piece lounge
        if defender:
            self.captured_list.append(defender)
            self.capture = True
            move_captured_piece(-1, self.captured_list)
            defender.on_board = False

        self.get_algebraic_notation()

        piece.rank, piece.file = piece.pos = self.l_pos
        board.loc[self.l_pos] = piece
        board.loc[self.f_pos] = 0

        self.update_castling_rights(piece.symbol)
        self.update_en_passant_target_square(piece.symbol, piece.file)
        self.update_halfmove_clock(piece.symbol)

        self.the_move = (self.f_pos[1] + str(self.f_pos[0]) +
                         self.l_pos[1] + str(self.l_pos[0]))

        piece.rect.center = BOARD_TO_SCREEN[piece.rank, piece.file]

        # if self.promote_pawn:
        if piece.symbol.upper() == 'P' and piece.rank == (
                                                [1, 8][self.turn == WHITE]):
            self.promote_pawn = True
            piece.click = False
            if self.mode != 'load':
                self.promotion_loop(surface)
            self.pawn_promotion()
            if not self.check and self.is_check():
                self.check = True
                self.SAN_list[-1] += '+'

        dicts.save_move(self.fullmove, self.turn, self.the_move)
        dicts.save_captured(self.fullmove, self.turn, self.captured_list[:])

        self.turn, self.opponent = next(self.alternator)

        if self.check:
            if self.is_mate():
                self.SAN_list[-1] = self.SAN_list[-1].replace('+', '#')
                print('MATE')
                # display menu

        self.check = False
        self.FEN = self.get_FEN_position()
        stockfish.set_position(dicts.move_list)
        if self.turn == WHITE:
            self.fullmove += 1
        if self.machine:
            self.engine = True

    def square_safe(self, turn, pos):
        for player in self.players:
            if player.on_board and player.color == turn:
                if (player.symbol.upper() == 'P' and pos in player.can_capture()):
                    return False
                elif (player.symbol.upper() != 'P' and
                        pos in player.available_moves()):
                    return False
        return True

    def can_castle(self):
        '''
        Checks if the king is trying to castle, castling rights and if it's
        legal.
        '''
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

        piece = board.loc[self.f_pos]
        if self.l_pos[1] == 'c' and ( 
                'qQ'[piece.symbol.isupper()] not in self.castling_rights):
            print('queen side sikinti')
            return False
        elif self.l_pos[1] == 'g' and ( 
                'kK'[piece.symbol.isupper()] not in self.castling_rights):
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
            castled_rook.rect.center = BOARD_TO_SCREEN[castled_rook.pos]
            board.loc[self.l_pos[0], 'a'] = 0
            self.castled_qs = True
        if self.l_pos[1] == 'g':
            board.loc[self.l_pos[0], 'f'] = board.loc[self.l_pos[0], 'h']
            castled_rook = board.loc[self.l_pos[0], 'f'] 
            castled_rook.pos = (self.l_pos[0], 'f')
            castled_rook.rank, castled_rook.file = castled_rook.pos
            castled_rook.rect.center = BOARD_TO_SCREEN[castled_rook.pos]
            board.loc[self.l_pos[0], 'h'] = 0
            self.castled_ks = True

    def pawn_promotion(self):
        # make new piece and give necessary attributes
        pc = self.promotion_choice
        pc.image = pg.image.load(self.promotion_choice.image_path)
        pc.pos = self.l_pos
        pc.rank, pc.file = self.l_pos
        pc.rect.center = (file_dict[pc.file], rank_dict[pc.rank])
        # delete the pawn that is promoted
        _ind = self.players.index(board.loc[self.l_pos])
        del self.players[_ind]
        # add new piece to the list 
        self.players.append(pc)
        # put the new piece on board
        board.loc[self.l_pos] = pc
        self.the_move += self.promotion_choice.symbol.lower()

        self.promotion_choice = ''

    def promotion_loop(self, surface):
        while self.promote_pawn:
            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.captured_list)
            move_rect_screen(surface, self.clicked, dicts.move_rects, self.SAN_list)
            for player in self.players:
                player.update(surface)
            choices = draw_promote_choices(surface, self.l_pos, self.turn)
            print(choices, self.promotion_choice)
            for choice in choices:
                choice.update(surface)
            for event in pg.event.get():
                if event.type == pg.MOUSEBUTTONDOWN:
                    for choice in choices:
                        if choice.rect.collidepoint(event.pos):
                            self.promotion_choice = choice
                elif event.type == pg.MOUSEBUTTONUP:
                    if self.promotion_choice.rect.collidepoint(event.pos):
                        self.promote_pawn = False

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_q:
                        self.promotion_choice = choices[0]
                    elif event.key == pg.K_r:
                        self.promotion_choice = choices[1]
                    elif event.key == pg.K_n:
                        self.promotion_choice = choices[2]
                    elif event.key == pg.K_b:
                        self.promotion_choice = choices[3]
                    if self.promotion_choice:
                        self.promote_pawn = False
            pg.display.update()
            clock.tick(60)
        
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

                    player.rank, player.file = player.pos = i

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
        # run gui - ask if wanna quit, save or play again
        
        print('mate')
        return True

    def king_pos(self, turn):
        '''
        Little helper function to find king's position.
        '''
        for player in self.players:
            if player.symbol == 'kK'[turn == WHITE]:
                return player.pos

    def move_rect_loop(self, surface, i):
        if '.' in self.SAN_list[i]:
            mv_str = self.SAN_list[i]
            turn = WHITE
        else:
            mv_str= self.SAN_list[i-1]
            turn = BLACK

        move_no = int(mv_str[:mv_str.index('.')])

        datboard = dicts.board[move_no][turn] # Get board state.
        datmove = dicts.moves[move_no][turn] # Get start and end position.
        self.datcaptured_list = dicts.captured[move_no][turn] # Get captured pieces

        # Start and end positions for the animation
        start = int(datmove[:2][1]), datmove[:2][0]
        end = int(datmove[2:][1]), datmove[2:][0]
        (x1, y1), (x, y) = BOARD_TO_SCREEN[end], BOARD_TO_SCREEN[start]

        piece = datboard.loc[start]
        defender = datboard.loc[end]
        self.datplayers = list(get_players(datboard)) + self.datcaptured_list
        print(self.datcaptured_list)
        # Move animation loop
        speed = (x1 - x) // 10, (y1 - y) // 10

        while piece.rect.center != (x1, y1):


            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.captured_list)
            move_rect_screen(surface, self.clicked, dicts.move_rects, self.SAN_list)

            place_other_pieces(surface, self.datplayers, start)
            
            piece.rect = piece.rect.move(speed)
            piece.update(surface)

            pg.display.update()
            clock.tick(50)

        if defender:
            move_captured_piece(-1, self.datcaptured_list)

        # check if en passant and remove the piece
        if piece.symbol.upper() == 'P' and end[1] != start[1] and not defender:
            ep = datboard.loc[start[0], end[1]]
            move_captured_piece(-1, self.datcaptured_list)

        for i, cap in enumerate(self.datcaptured_list):
            move_captured_piece(i, self.datcaptured_list)

        # if it's not the last move, draw next board on dict
        try:
            nxt_mv_no = [move_no + 1, move_no][turn == WHITE]
            nxt_turn = [WHITE, BLACK][turn == WHITE]
            nxt_board = dicts.board[nxt_mv_no][nxt_turn]
            print(piece.symbol.upper == 'P', end[1], start[1], defender)
            self.datplayers = list(get_players(nxt_board)) + self.datcaptured_list

        except KeyError:
            pass

    def move_screen(self, surface,  captured_list):
        font = pg.font.SysFont('gentiumbookbasic', 25)
        font2 = pg.font.SysFont('gentiumbookbasic', 15)
        x, y = 886, 8
        move_rect_color = (235, 219, 178)
        if len(self.SAN_list) > 0:
            for i, san in enumerate(self.SAN_list):
                text = font.render(san, True, move_rect_color)
                text_rect = text.get_rect()

                if x + text_rect.width > 1104:
                    x = 886
                    y += 22
                dicts.move_rects[i] = text_rect
                dicts.move_rects[i].topleft = (x, y)
                x += text_rect.width + 4
                surface.blit(text, dicts.move_rects[i])

        captured_b_pawns = str([i.symbol for i in captured_list].count('p'))
        captured_w_pawns = str([i.symbol for i in captured_list].count('P'))
        # print(captured_list)

        if int(captured_b_pawns) > 1:
            b_pawn_no = font2.render(captured_b_pawns, True, (250, 189, 47))
            b_pawn_no_rect = b_pawn_no.get_rect(center=(904, 767))
            surface.blit(b_pawn_no, b_pawn_no_rect)
        if int(captured_w_pawns) > 1:
            w_pawn_no = font2.render(captured_w_pawns, True, (250, 189, 47))
            w_pawn_no_rect = w_pawn_no.get_rect(center=(904, 825))
            surface.blit(w_pawn_no, w_pawn_no_rect)

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

    def animate_move(self, surface, piece, f_pos, l_pos, players, captured_list):
        (x1, y1), (x, y) = (BOARD_TO_SCREEN[l_pos], BOARD_TO_SCREEN[f_pos])
        speed = (x1 - x) // 10, (y1 - y) // 10
        while piece.rect.center != (x1, y1):
            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.clicked)

            self.move_screen(surface, captured_list)
            place_other_pieces(surface, players, f_pos)

            piece.rect = piece.rect.move(speed)
            piece.update(surface)
            pg.display.update()
            clock.tick(60)

    def engine_main_loop(self, surface):
        global choices
        dicts.save_board(self.fullmove, self.turn, deepcopy(board))
        self.the_move = stockfish.get_best_move()
        print(f'Engine - Move: {self.fullmove} - {self.turn}:  {self.the_move}')
        start, end = self.the_move[:2], self.the_move[2:4]
        self.f_pos = int(start[1]), start[0]
        self.l_pos = int(end[1]), end[0]
        piece = board.loc[self.f_pos]
        defender = board.loc[self.l_pos]

        (x1, y1), (x, y) = BOARD_TO_SCREEN[self.l_pos], BOARD_TO_SCREEN[self.f_pos]
        speed = (x1 - x) // 10, (y1 - y) // 10
        while piece.rect.center != (x1, y1):
            draw_frame(surface)
            draw_squares(surface)
            draw_move_screen(surface, self.captured_list)
            move_rect_screen(surface, self.clicked, dicts.move_rects, self.SAN_list)

            place_other_pieces(surface, self.players, self.f_pos)

            piece.rect = piece.rect.move(speed)
            piece.update(surface)
            pg.display.update()
            clock.tick(40)

        # check if it is en passant
        if piece.symbol.upper() == 'P' and self.f_pos[1] != self.l_pos[1] and \
                not defender:
            ep_pos = (self.f_pos[0], self.l_pos[1])
            ep_defender = board.loc[ep_pos]
            self.captured_list.append(ep_defender)
            self.capture = True
            move_captured_piece(-1, self.captured_list)
            # self.en_passant = False
            board.loc[ep_pos] = 0

        if defender:
            self.captured_list.append(defender)
            self.capture = True
            move_captured_piece(-1, self.captured_list)
            defender.on_board = False

        if (piece.symbol.upper() == 'K' and
                abs(ord(start[0]) - ord(end[0])) == 2):
            self.castle()

        self.get_algebraic_notation()
        board.loc[self.l_pos] = piece
        board.loc[self.f_pos] = 0

        if (piece.symbol.upper() == 'P' and
                piece.rank == [2, 7][self.turn == WHITE]):
            
            choices = draw_promote_choices(surface, self.l_pos, self.turn)
            # for choice in choices:
            #     choice.update(surface)
            print(choices)
            choice_dict = {'q': choices[0], 'r': choices[1],
                           'n': choices[2], 'b': choices[1]}
            self.promotion_choice = choice_dict[self.the_move[-1]]
            self.pawn_promotion()
            self.the_move = self.the_move[:-1]

            
        self.update_castling_rights(piece.symbol)
        self.update_en_passant_target_square(piece.symbol, piece.file)
        self.update_halfmove_clock(piece.symbol)

        dicts.save_move(self.fullmove, self.turn, self.the_move)
        dicts.save_captured(self.fullmove, self.turn, self.captured_list[:])
        
        piece.rank, piece.file = piece.pos = self.l_pos

        if self.is_check():
            self.check = True
        self.turn, self.opponent = next(self.alternator)
        if self.check:
            self.SAN_list[-1] += '+'
            if self.is_mate():
                self.SAN_list[-1] = self.SAN_list[-1].replace('+', '#')
                print('MATE')
                # display menu
        self.check = False
        



        self.FEN = self.get_FEN_position()
        stockfish.set_position(dicts.move_list)

        if self.turn == WHITE:
            self.fullmove += 1



# Directions for generating the available moves for major pieces.
diagonal_dir = [(1, 1), (1, -1), (-1, -1), (-1, 1)]
cardinal_dir = [(1, 0), (-1, 0), (0, 1), (0, -1)]
queen_dir = diagonal_dir + cardinal_dir
knight_dir = [(2, 1), (2, -1), (-2, 1), (-2, -1), \
                (1, 2), (-1, 2), (1, -2), (-1, -2)]

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
        self.image = pg.image.load(self.image_path)
        self.pos = pos
        self.rank, self.file = self.pos
        self.on_board = True
        self.promotion = False

    def update(self, surface):

        if self.click:
            pg.mouse.set_visible(False)
            self.rect.topleft = pg.mouse.get_pos()[0] - 50, pg.mouse.get_pos()[1] - 60
        surface.blit(self.image, self.rect)

    def __repr__(self):
        return self.symbol


    #find all available locations for rook, bishop and queen
    def available_pos_list(self, directions):
        for dir_r, dir_f in iter(directions):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            while 1:
                try:
                    if not board.loc[temp_r, temp_f]:
                        yield (temp_r, temp_f)
                    elif board.loc[temp_r, temp_f].color != self.color:
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
        #pos_list = []
        for dir_r, dir_f in iter(knight_dir):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            try:
                if not board.loc[temp_r, temp_f] or \
                    board.loc[temp_r, temp_f].color != self.color:
                    yield (temp_r, temp_f)
                    #pos_list.append((temp_r, temp_f))
            except (KeyError, AttributeError):
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
        for dir_r, dir_f in iter(queen_dir):
            temp_r, temp_f = self.rank + dir_r, chr(ord(self.file) + dir_f)
            try:
                if not board.loc[temp_r, temp_f] or \
                    board.loc[temp_r, temp_f].color != self.color:
                    yield (temp_r, temp_f)
            except (KeyError, AttributeError):
                continue

class Pawn(Piece):
    def available_moves(self):
        self.direction = [-1, 1][self.symbol.isupper()]
        if (self.rank == 2 and self.color == WHITE) or \
            (self.rank == 7 and self.color == BLACK):
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




def initial_setup_pieces():
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


def get_players(board):
    for rank in ranks:
        for file_ in files:
            if board.loc[rank, file_]:
                board.loc[rank, file_].on_board = True
                player = board.loc[rank, file_]

                player.image = pg.image.load(
                        f'pieces90px/{player.symbol}.png')
                player.rect.center = (file_dict[file_], rank_dict[rank])
                yield player

class Storage:
    def __init__(self):
        self.moves = {}
        self.captured = {}
        self.move_rects = {}
        self.board = {}
        self.move_list = []

    def save_move(self, fullmove, turn, the_move):
        self.move_list.append(the_move)
        if turn == WHITE:
            self.moves[fullmove] = {}
            self.moves[fullmove][turn] = the_move
        else:
            self.moves[fullmove][turn] = the_move

    def save_captured(self, fullmove, turn, captured):
        if turn == WHITE:
            self.captured[fullmove] = {}
            self.captured[fullmove][turn] = captured
        else:
            self.captured[fullmove][turn] = captured

    def save_board(self, fullmove, turn, board):
        if turn == WHITE:
            self.board[fullmove] = {}
            self.board[fullmove][turn] = board
        else:
            self.board[fullmove][turn] = board



if __name__ == "__main__":
    # os.environ['SDL_VIDEO_WINDOW_POS'] = '800,25' # Set window position
    pg.init() # Initialize pygame
    pg.display.set_caption('Chess') # Set pygame window caption
    clock = pg.time.Clock() # Set clock
    screen = pg.display.set_mode((1113, 881)) # Set screen size


    # Define colors of sides, it's used while naming turns and pieces
    BLACK = 'black'
    WHITE = 'white'

    # Default initial board position in Forsyth-Edwards Notation (FEN) 
    initial_FEN_position = \
            'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


    # Board representation. Pandas dataFrame used for easy square naming 
    board = pd.DataFrame(np.zeros((8, 8), dtype=int),
                         index=[8, 7, 6, 5, 4, 3, 2, 1],
                         columns=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])

    ranks = board.index
    files = board.columns

   
    real_positions = [90, 190, 290, 390, 490, 590, 690, 790]
    file_dict = dict(zip(files, real_positions))
    rank_dict = dict(zip(ranks, real_positions))

    BOARD_TO_SCREEN = {}
    SCREEN_TO_BOARD = {}
    for rank in ranks:
        for file_ in files:
            SCREEN_TO_BOARD[(file_dict[file_], rank_dict[rank])] = (rank, file_)
            BOARD_TO_SCREEN[(rank, file_)] = (file_dict[file_], rank_dict[rank])
    #engine
    stockfish = Stockfish('stockfish')
    stockfish.set_skill_level(10)

    pieces = {'a': Rook, 'b': Knight, 'c': Bishop, 'd': Queen,
              'e': King, 'f': Bishop, 'g': Knight, 'h': Rook}
    symbols = {Rook: 'r', Knight: 'n', Bishop: 'b',
               Queen: 'q', King: 'k', Pawn: 'p'}



    moves = ['h2h4', 'f7f5', 'h4h5', 'f5f4', 'h5h6', 'f4f3', 'h6g7', 'f3g2', 'g7h8q', 'g2h1n', 'h8g8', 'd7d6', 'g8h7', 'h1f2', 'e1f2', 'c8e6', 'h7e4', 'd8c8', 'f1g2', 'd6d5', 'e4e5', 'b8c6', 'e5g5', 'd5d4', 'g1f3', 'c8d8', 'g5f4', 'd8d7', 'd1h1', 'e8c8', 'f3e5', 'd7d6', 'g2c6', 'b7c6', 'b1a3', 'f8g7', 'h1e4', 'd8f8', 'e5f7', 'f8f7', 'f4f7', 'g7e5', 'f7h5', 'e5g7', 'h5g5', 'g7f6', 'g5h5', 'c8b8', 'f2g2', 'e6d5', 'h5h7', 'd5e4', 'h7e4', 'd6d5', 'e4f3', 'd5f3', 'g2f3', 'c6c5', 'a3c4', 'e7e5', 'b2b3', 'f6g7', 'c1a3', 'b8b7', 'f3g3', 'e5e4', 'a1e1', 'g7f8', 'e1f1', 'f8d6', 'g3f2', 'b7b8', 'f2g2', 'b8b7', 'f1f5', 'd4d3', 'c2d3', 'a7a6', 'c4a5', 'b7b8', 'd3e4', 'c5c4', 'a3d6', 'c7d6', 'f5f8', 'b8c7', 'f8f7', 'c7b6', 'b3b4', 'b6b5', 'f7f5', 'b5b4']

    dicts = Storage()


    a = Game()
    while 1:
        a.main(screen)
