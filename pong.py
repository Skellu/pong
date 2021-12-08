# Samuli Öysti
# 30.11.2021

import pygame as pg
from pygame import freetype
from pygame.constants import KEYDOWN, KEYUP, MOUSEBUTTONDOWN, QUIT
import random               # Used to randomize ball starting positions and speeds
import os.path
from os.path import exists  # Used to check if config file exists
import json                 # We Use JSON for securely saving and loading the settings


# initializing the constructor
pg.init()
pg.display.set_caption('Pong!')
# screen resolution
res = (800,600)

# Assign FPS a value
FPS = 60
FramePerSec = pg.time.Clock()

# opens up a window
screen = pg.display.set_mode(res)

# basic colors
WHITE = [255,255,255]
BLACK = [0,0,0]
BROWN = [139,69,19]
GRAY = [128,128,128]
RED = [255,0,0]
PINK = [255,102,178]
GREEN = [0,255,0]
BLUE = [0,0,255]
colors = [WHITE,RED,PINK,GREEN,BLUE]

# Current filepath
directory = os.path.abspath(os.path.dirname(__file__))

def save():                 # Saves settings to config.json
    j = json.dumps(settings)
    with open(directory + '/gamedata/config.json', 'w') as f:
        f.write(j)

def load():                 # Loads settings from config.json
    with open(directory + '/gamedata/config.json', 'r') as f:
        global settings
        settings = json.loads(f.read())


elements = []           # Init list for drawable objects.
buttons = []
p1Score = 0
p2Score = 0     # Init player scores
currentView = 'game'    # Current window
################################ SETTINGS ##################################
pg.event.set_allowed([KEYUP, KEYDOWN, QUIT])                        # Set the allowed events in the pygame event Queue. Dramatically improves performance.
pixelFont_LARGE = pg.freetype.Font(directory + '/gamedata/Pixeboy.ttf', 96)   # Create the pixelated font we want for the numbering system. Licensed as Non-Commercial Freeware https://www.fontspace.com/pixeboy-font-f43730
pixelFont = pg.freetype.Font(directory + '/gamedata/Pixeboy.ttf', 30)
if exists(directory + '/gamedata/config.json'):
    load()
else:
    global settings
    settings = {
    'FPS': 60,                  # MAX FPS Setting. Affects the speed the game runs at.
    'ballVel': 10,               # Horizontal speed of the Ball object in pixels per second. Negative values = LEFT
    'pVel': 6,                  # Vertical speed of player objects in pixels per second. Negative values = UP
    'p1Color': WHITE,            # Player 1 Object color
    'p2Color': WHITE,           # Player 2 Object color
    'ballColor': BROWN,
    }


class Button():
    def __init__(self, label, color, x,y, width, height, onclick='', text='', textColor=WHITE, img=None):
        self.label = label
        self.color = color
        self.x=x
        self.y=y
        self.width=width
        self.height=height
        self.onclick=onclick
        self.rect = pg.Rect(x,y,width,height)
        self.text=text
        self.textColor = textColor
        if img:
            self.img = pg.image.load(directory +'\gamedata\sprites/' + img)
        else:
            self.img = None


    def draw(self,outline=None):
        #Call this method to draw the button on the screen
        if outline:
            pg.draw.rect(screen, outline, (self.x-2,self.y-2,self.width+4,self.height+4),0)

        pg.draw.rect(screen, self.color, (self.x,self.y,self.width,self.height),0)

        if self.text != '':
            
            x, y = pixelFont.get_rect(self.text)[2:4]
            
            pixelFont.render_to(screen, (self.x + (self.width/2 - x/2), self.y + (self.height/2 - y/2)), self.text, self.textColor)

        if self.img:
            self.img = pg.transform.scale(self.img, (self.width,self.height))
            screen.blit(self.img, (self.x, self.y))

    def onClick(self):
        if self.label == 'settings' or self.label == 'game':    # Buttons for switching to the settings menu and back
            global currentView
            currentView = self.label
            setup()

        elif self.label == 'reset':
            restart()

        elif self.label == 'ballVel':
            x = settings['ballVel']
            if x > 15:
                settings['ballVel'] = 3
            else:
                settings['ballVel'] += 1

        elif self.label == 'pVel':
            x = settings['pVel']
            if x > 12:
                settings['pVel'] = 3
            else:
                settings['pVel'] += 1

        elif self.label == 'p1Color':       # Button for changing Player 1 color
            x = colors.index(settings['p1Color'])   # find the current color in the 'colors' list and assign it's index to 'x'
            if x < len(colors)-1:                   # if not last index in the list
                settings['p1Color'] = colors[x+1]   # change color to the next in the list
            else:
                settings['p1Color'] = colors[0]     # else change color to the first in the list

        elif self.label == 'p2Color':       # Button for changing Player 2 color
            x = colors.index(settings['p2Color'])   # same as the previous button
            if x < len(colors)-1:
                settings['p2Color'] = colors[x+1]
            else:
                settings['p2Color'] = colors[0]

        elif self.label == 'ballColor':     # Button for changing ball color
            x = colors.index(settings['ballColor']) # same as the previous button
            if x < len(colors)-1:
                settings['ballColor'] = colors[x+1]
            else:
                settings['ballColor'] = colors[0]

    def isHovered(self):
        pos = pg.get_mouse_pos()
        #Pos is the mouse position or a tuple of (x,y) coordinates
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                return True
        return False


class Element():
    def __init__(self, color, width, height, posX, posY, vel=0, velX=0, text=''):
        self.color = color      # object color
        self.width = width      # object width in pixels
        self.height = height    # object height in pixels
        self.x = posX           # position on the X-axis (horizontal)
        self.y = posY           # position on the Y-axis (vertical)
        self.v = vel            # vertical velocity in pixels per frame. negative values = up.
        self.vX = velX          # horizontal velocity in pixels per frame. negative values = left.
        self.rect = pg.Rect(self.x, self.y, self.width, self.height)
        self.text = text

    def updateBall(self):                                                   # Check if the ball has hit anything and update velocity accordingly
        if self.y < 60-self.v or self.y > res[1]-self.height:                   # If colliding with floor or ceiling 
            self.v *= -1                                                            # Invert Y-velocity
        if self.rect.colliderect(p1.rect) or self.rect.colliderect(p2.rect):    # If colliding with either player object
            if self.x < p1.x+p1.width+self.vX or self.x > p2.x-ball.width+self.vX:          # if closer to a wall than either player, you must have been hit by the top or bottom of a player rectangle.
                pass                                                                    # then pass and let the ball continue towards the wall.
            else:
                self.vX *= -1                                                       # else Invert X-velocity

        
    def update(self):   # Called once per frame, Updates the position of the Element.
        # Allows movement if the object is within the play area.
        if self.y < 60 and self.v < 0:
            pass
        elif self.y > res[1]-self.height and self.v > 0:
            pass
        else:
            self.y += self.v
            self.x += self.vX
        self.draw()

    def textRender(self):
        width, height,x,y = pixelFont.get_rect(str(self.text))
        pixelFont.render_to(screen, (self.x-width/2, self.y-height/2), str(self.text), WHITE)
        

    def draw(self): # Updates the rectangle of the element and draws it on screen.
        # Called automatically from update(), can also be called separately
        self.rect = pg.Rect(self.x, self.y, self.width, self.height)
        pg.draw.rect(screen, self.color, self.rect)
        if self.text:
            self.textRender()
           



def score(player):  # Adds to the score of the player who scored, then runs setup()
    global p1Score, p2Score
    if player == 1:
        p1Score += 1
    elif player == 2:
        p2Score += 1
    setup()


def restart():  # Resets player scores and runs setup()
    global p1Score, p2Score
    p1Score = 0
    p2Score = 0
    setup()

def pause():  # Enters a paused loop, waiting for user input
    while True:
        for ev in pg.event.get():
            if ev.type == QUIT:
                save()
                pg.quit()
            if ev.type == KEYDOWN: # Stop the pause on keypress
                for i in range(3):
                    elements.pop()
                return
            if ev.type == MOUSEBUTTONDOWN:  # On click, if hovering a button, activate it. else stop the pause
                pos = pg.mouse.get_pos()
                for b in buttons:
                    if b.rect.collidepoint(pos):
                        b.onClick()
                        return
                for i in range(3):
                    elements.pop()
                return
         # Call Update and draw on everything
        if currentView == 'game':
            drawGame()
        elif currentView == 'settings': # Break out of the pause loop if in settings menu
            return

        # updates the frames of the game and refreshes the display
        pg.display.flip()
        FramePerSec.tick(FPS)


def setup():   # change view to main game and pause
    elements.clear()
    buttons.clear()
    global p1, p2, ball
    p1 = Element(settings['p1Color'], 20, 100, 40, 240)
    elements.append(p1)
    p2 = Element(settings['p2Color'], 20, 100, 740, 240)
    elements.append(p2)

    # Create the ball and randomize the starting side
    ballVel = settings['ballVel']
    x = random.randrange(80,701,620)
    if x > 100: # If on the right side, invert ball velocity
        ballVel *= -1
    ball = Element(settings['ballColor'], 20, 20, x, random.randrange(80,560), velX=ballVel, vel=5)
    elements.append(ball)
    # Create the brown bar at the top
    taskbar = Element(BROWN, res[0], 60, 0, 0)
    elements.append(taskbar)
    # Create the buttons on the taskbar
    buttons.append(Button('settings',GRAY, 500, 5, 50, 50, img='cog.png'))
    buttons.append(Button('reset', GRAY, 430, 5, 50, 50, img='reset.jpg'))
    # Create the informative text during pauses
    elements.append(Element(BLACK,100,50,120,350,text='P1 Controls: W and S'))
    elements.append(Element(BLACK,100,50,400,350,text='P2 Controls: UP and DOWN'))
    elements.append(Element(BLACK,100,50,320,150,text='Press ANY Key'))
    drawGame()
    pg.display.flip()
    pause()
    

def drawSettings(): # Create the settings menu objects.
    buttons.clear()
    elements.clear()
    screen.fill(BLACK)
    taskbar = Element(BROWN, res[0], 60, 0, 0)
    elements.append(taskbar)
    buttons.append(Button('game', GRAY, 500, 5, 50,50, img='cog.png'))
    buttons.append(Button('reset', GRAY, 430, 5, 50, 50, img='reset.jpg'))
    buttons.append(Button('p1Color', GRAY, 100, 200, 200, 50, text='Player 1 Color', textColor=settings['p1Color']))
    buttons.append(Button('p2Color', GRAY, 100, 270, 200, 50, text='Player 2 Color', textColor=settings['p2Color']))
    buttons.append(Button('ballColor', GRAY, 100, 340, 200, 50, text='Ball Color', textColor=settings['ballColor']))
    buttons.append(Button('ballVel', GRAY, 350, 200, 200,50, text='Ball Speed: {}'.format(settings['ballVel'])))
    buttons.append(Button('pVel', GRAY, 350, 270, 200 , 50, text='Player Speed: {}'.format(settings['pVel'])))
    drawGame()
    

def gameTick(): # Call this if you want to update the ball AND call drawGame()
    ball.updateBall()
    if ball.x < 0+ball.vX:
        score(2)
    elif ball.x > 800-ball.width-ball.vX:
        score(1)
    for el in elements:
        el.update()
    drawGame(True)

def drawGame(update=False): # Call this if you only want to draw, not update object positions.
    screen.fill(BLACK)
    for el in elements:
        el.draw()
    for b in buttons:
        b.draw()

    pixelFont_LARGE.render_to(screen, (5,5), str(p1Score), settings['p1Color']) # Render Player 1's Score 5 pixels from the top and left of the screen
    # Calculates the width of the text and prints P2's score 5 pixels off the top and right of the screen
    pixelFont_LARGE.render_to(screen, (795-pixelFont_LARGE.get_rect(str(p2Score))[2], 5), str(p2Score), settings['p2Color'])
        


def main():

    while True:
        for ev in pg.event.get(): # Read the events in the event queue
            if ev.type == pg.QUIT:
                save()
                pg.quit()
            if ev.type == pg.MOUSEBUTTONDOWN:
                pos = pg.mouse.get_pos()
                for b in buttons:
                    if b.rect.collidepoint(pos):
                        b.onClick()
                        break
            
            if ev.type == pg.KEYDOWN:   # Update player velocities accordingly on keypress
                if ev.key == pg.K_w:
                    p1.v = -settings['pVel']
                if ev.key == pg.K_s:
                    p1.v = settings['pVel']
                if ev.key == pg.K_UP:
                    p2.v = -settings['pVel']
                if ev.key == pg.K_DOWN:
                    p2.v = settings['pVel']
            if ev.type == pg.KEYUP:
                if ev.key == pg.K_w and p1.v != settings['pVel']:
                    p1.v = 0
                if ev.key == pg.K_s and p1.v != -settings['pVel']:
                    p1.v = 0
                if ev.key == pg.K_UP and p2.v != settings['pVel']:
                    p2.v = 0
                if ev.key == pg.K_DOWN and p2.v != -settings['pVel']:
                    p2.v = 0
            

        # Update/Draw
        if currentView == 'game':
            gameTick()
        elif currentView == 'settings':
            drawSettings()

        # updates the frames of the game and refreshes the display
        pg.display.flip()
        FramePerSec.tick(FPS)


if __name__ == '__main__':
    setup()
    main()