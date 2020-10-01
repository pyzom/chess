"""
Draws a chess board and a frame around it with letters and numbers.
Draws the background of the move screen and the captured pieces screen.
"""

import pygame as pg
BLACK = 'black'
WHITE = 'white'
light_square = (232, 235, 239)
dark_square = (125, 135, 150)
captured_section = (47, 79, 79) 
frame_color = (35, 43, 43)

def draw_frame(Surface):
    """
    Draws the frame around the board and the letters and numbers on the frame. 
    (Not implemented!!) Depending on whose turn, turns the board around.
    The frame is 40px thick.
    """
    # draw the frame 
    pg.draw.polygon(Surface, frame_color,\
            [(0,0), (40,40), (840,40), (840,840), (880,880),(880,0)])
    pg.draw.polygon(Surface, frame_color,\
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
        Surface.blit(text, text_rect)

    for i,letter in enumerate(letters):
        x, y = 90, 20
        text = font.render(letter, True, (255, 255, 255))
        text_rect = text.get_rect(center=(x+i*100,y))
        Surface.blit(text, text_rect)

def draw_squares(Surface):
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
                pg.draw.rect(Surface, dark_square, rect)
                dark = False
            else:
                pg.draw.rect(Surface, light_square, rect)
                dark = True

def draw_move_screen(Surface, clicked_move_rect):
    """
    Draws the background and the frame of the moves and the captured pieces 
    section.
    When a 'move rect' is clicked, it highlights the move rect area.
    """
    # top right section (moves screen)
    rect = pg.Rect(881, 0, 232, 749)
    pg.draw.rect(Surface, (0), rect) 
    # bottom right section (captured pieces lounge)
    rect = pg.Rect(881, 749, 232, 132)
    pg.draw.rect(Surface, captured_section, rect) 
    # the frame around and between the sections
    pg.draw.lines(Surface, light_square, True, \
            ((880, 0), (880, 880), (1112, 880), (1112, 0)), 1)
    pg.draw.lines(Surface, light_square, True, \
            ((882, 2), (882, 748), (1110, 748), (1110, 2)), 1)
    pg.draw.lines(Surface, light_square, True, \
            ((882, 878), (882, 750), (1110, 750), (1110, 878)), 1)
    # highlight the move in moves mode
    if clicked_move_rect:
        rect = pg.Rect(clicked_move_rect)
        pg.draw.rect(Surface, captured_section, rect)


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

