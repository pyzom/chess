import pygame as pg

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

 
