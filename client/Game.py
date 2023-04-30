import cv2 as cv
import numpy as np
import asyncio
from client import main
import pytesseract

class Game:
    def __init__(self):
        self.cap = cv.VideoCapture(1)
        if not self.cap.isOpened():
            print('Cannot open elgato')
            exit()
        self.game_state = ''
        self.frame = None
        self.trade_state = 'Looking for trade'
        

    def update_game_state(self):
        # game state - defining UI element
        # open_world - map in bottom right
        # menu       - black box on right
        # bag        - top UI is ~ const
        # box        - many squares
        pass

    async def hatch_eggs(self, num_eggs):
        self.game_state='Running'
        
        await self.start_running()

    def check_for_dialogue_box(self):
        pass

    async def start_running(self):
        # set joystick to corner and press b
        await l_stick_hold(UPLEFT)
        await press('b')

    def hatch_loop(self):
        while True:
            ret, self.frame = self.cap.read()

            if not ret:
                print("Can't receive frame")
                exit()
            if self.check_for_dialogue_box():
                return 
            if cv.waitKey() == ord('q'):
                exit()
        
    def trade_loop(self):
        while True:
            ret, self.frame = self.cap.read()
            self.frame = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
            if not ret:
                print("Can't receive frame")
                exit()
            
            # cv.imshow('Frame', self.frame)
            if self.trade_state == 'Look for trade':
                self.start_trade()
            if self.trade_state == 'Looking for trade':
                self.check_trade_found()
            if self.trade_state == 'Trade found':
                self.check_name()
            if self.trade_state == 'Waiting for accept':
                pass
            if cv.waitKey() == ord('q'):
                exit()
    
    def check_name(self):
        name_frame = self.frame[10:70, 400:750]
        name = pytesseract.image_to_string(name_frame).replace('\n', '')
        if name in self.names:
            self.complete_trade()
        else:
            self.exit_trade()
    
    def check_trade_found(self):
        text_frame = self.frame[820:940, 530:1300]
        
        text = pytesseract.image_to_string(text_frame).replace('\n', '')
        if text == 'A trade partner has been found!':
            self.trade_state = 'Trade found'

    def complete_trade(self):
        # inputs to complete trade, need to wait for them to accept
        # update an internal counter of how many trades have been completed
        pass
    
    def exit_trade(self):
        # quit trade inputs
        self.trade_state = 'Look for trade'

# self.frame = cv.rectangle(self.frame, (400,10), (750,70), (255, 0, 0), 2) # name bounding box
# self.frame = cv.rectangle(self.frame, (478,780), (1440,980), (255, 0, 0), 2) # bottom bounding box
# self.frame = cv.rectangle(self.frame, (530,820), (1300,940), (255, 0, 0), 2) # Text bounding box
async def press(button):
    await main('press', button)
    print('Pressed', button)
async def release(button):
    await main('release', button)
async def tap(button):
    await main('tap', button)
async def l_stick_hold(position):
    await main('stick_hold', 'left', position)
async def r_stick_hold(position):
    await main('stick_hold', 'right', position)
async def l_stick_flick(position):
    await main('stick_flick', 'left', position)
async def r_stick_flick(position):
    await main('stick_flick', 'right', position)
async def l_stick_reset():
    await main('stick_reset', 'left')
async def r_stick_reset():
    await main('stick_reset', 'right')

#Stick consts
UP=(2048,4095)
DOWN=(2048,0)
LEFT=(0, 2048)
RIGHT=(4095,2048)

UPLEFT=(0, 4095)
UPRIGHT=(4095, 4095)
DOWNLEFT=(0, 0)
DOWNRIGHT=(4095, 0)

# EGG HATCHING
# Run in circles, check if notificaiton box has showed up
# When it does, 1 pokemon has hatched, so increment counter by 1, release b
# Press a or b to get through menu
# if counter < 6, loop back to top
# if counter = 6, get next egg group from inv
# reset counter

if __name__ == "__main__":
    game = Game()
    game.trade_loop()