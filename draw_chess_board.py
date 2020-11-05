"""
Draws a chess board and a frame around it with letters and numbers.
Draws the background of the move screen and the captured pieces screen.
"""

import pygame as pg

BLACK = 'black'
WHITE = 'white'
light_square = (205, 207, 204)#(232, 235, 239)
dark_square = (110, 120, 122)#(125, 135, 150)
captured_section = (50, 48, 47) 
frame_color = (40, 40, 40)

def draw_frame(surface):
    """
    Draws the frame around the board and the letters and numbers on the frame. 
    (Not implemented!!) Depending on whose turn, turns the board around.
    The frame is 40px thick.
    """
    # draw the frame 
    pg.draw.polygon(surface, frame_color,\
            [(0,0), (40,40), (840,40), (840,840), (880,880),(880,0)])
    pg.draw.polygon(surface, frame_color,\
            [(0,0), (40,40), (40,840), (840,840), (880,880),(0,880)])
    # put numbers and letters on the frame
    font = pg.font.SysFont('gentiumbookbasic', 30)
    letters = iter('abcdefgh')
    numbers = iter('12345678')
    # if it's black's turn, type the letters and colors in revers order
    # if turn == 1:
    #     letters = list(reversed(letters))
    #     numbers = list(reversed(numbers))
    for i, number in enumerate(numbers):
        x, y = 790, 18
        text = font.render(number, True, (255, 255, 255))
        text_rect = text.get_rect(center=(y,x-(i)*100))
        surface.blit(text, text_rect)

    for i,letter in enumerate(letters):
        x, y = 90, 20
        text = font.render(letter, True, (255, 255, 255))
        text_rect = text.get_rect(center=(x+i*100,y))
        surface.blit(text, text_rect)

def draw_squares(surface):
    """
    Draws the squares of the board. Length of the side is 100px.
    """
    x, y = 40, 40
    szbtwn = 100
    dark = False
    for i in iter((0, 2, 4, 6, 1, 3, 5, 7)):
        if i == 1:
            dark = True
        for j in range(8):
            rect = pg.Rect(x+j*szbtwn, y+i*szbtwn, szbtwn, szbtwn)
            if dark == True:
                pg.draw.rect(surface, dark_square, rect)
                dark = False
            else:
                pg.draw.rect(surface, light_square, rect)
                dark = True

def move_rect_screen(surface, clicked_move_rect, moves, SAN_list):
    if clicked_move_rect:
        pg.draw.rect(surface, dark_square, clicked_move_rect)
    font = pg.font.SysFont('gentiumbookbasic', 25)
    x, y = 886, 8
    move_rect_color = (235, 219, 178)
    if SAN_list:
        for i, san in enumerate(SAN_list):
            text = font.render(san, True, move_rect_color)
            text_rect = text.get_rect()

            if x + text_rect.width > 1104:
                x = 886
                y += 22
            moves[i] = text_rect
            moves[i].topleft = (x, y)
            x += text_rect.width + 4
            surface.blit(text,moves[i])
    # highlight the clicked move in moves mode

def draw_move_screen(surface, captured_list):
    """
    Draws the background and the frame of the moves and the captured pieces 
    section.
    It takes 'move rect' as argument, so when it is clicked, it highlights the 
    move rect area.
    """
    font2 = pg.font.SysFont('gentiumbookbasic', 15)
    # top right section (moves screen)
    rect = pg.Rect(881, 0, 232, 749)
    pg.draw.rect(surface, (29, 32, 33), rect) 
    # bottom right section (captured pieces lounge)
    rect = pg.Rect(881, 749, 232, 132)
    pg.draw.rect(surface, captured_section, rect) 
    # the frame around and between the sections
    pg.draw.lines(surface, (146, 131, 116), True,
            ((880, 0), (880, 880), (1112, 880), (1112, 0)), 1)
    pg.draw.lines(surface, (146, 131, 116), True,
            ((882, 2), (882, 748), (1110, 748), (1110, 2)), 1)
    pg.draw.lines(surface, (146, 131, 116), True,
            ((882, 878), (882, 750), (1110, 750), (1110, 878)), 1)


    # numbers on the captured pawns 
    captured_b_pawns = str([i.symbol for i in captured_list].count('p'))
    captured_w_pawns = str([i.symbol for i in captured_list].count('P'))

    if int(captured_b_pawns) > 1:
        b_pawn_no = font2.render(captured_b_pawns, True, (250, 189, 47))
        b_pawn_no_rect = b_pawn_no.get_rect(center=(904, 767))
        surface.blit(b_pawn_no, b_pawn_no_rect)
    if int(captured_w_pawns) > 1:
        w_pawn_no = font2.render(captured_w_pawns, True, (250, 189, 47))
        w_pawn_no_rect = w_pawn_no.get_rect(center=(904, 825))
        surface.blit(w_pawn_no, w_pawn_no_rect)
    

def place_other_pieces(surface, players, start):
    for player in players:
        if player.pos != start:
            player.update(surface)


def position(pos):
    """
    When the player put a piece on the board, this function takes mouse position 
    as an argument and returns the proper point on the square.
    """
    pos = list(pos)
    for i, ind in enumerate(pos):
        if ind <= 100 * (ind // 100) + 40:
            pos[i] = 100 * (pos[i] // 100) - 10
        else:
            pos[i] = 100 * (pos[i] // 100) + 90

    return tuple(pos)

def in_real_grid(pos):
    """
    Checks if the given position is on the game field.
    """
    if 40 <= pos[0] <= 840 and 40 <= pos[1] <= 840:
        return True
    return False


def alternate_turn():
    while 1:
        yield BLACK, WHITE
        yield WHITE, BLACK

def button_onoff():
    while 1:
        yield 880
        yield 1113


def move_captured_piece(ind_, captured_list):
        if captured_list:
            captured = captured_list[ind_]
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
            if (captured.symbol in [x.symbol for x in captured_list[:-1]] and
                    captured.symbol.upper() != 'P'):
                x += 10
            captured.image = pg.image.load(f'pieces50px/{captured.symbol}.png')
            captured.rect.center = x, y
            captured.pos = captured.rank = captured.file = None
            captured.on_board = False




