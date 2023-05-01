import cv2 as cv
import numpy as np
import asyncio
from client import main
import pytesseract
import argparse
import logging

class Game:
    def __init__(self):
        self.cap = cv.VideoCapture(1)
        if not self.cap.isOpened():
            print('Cannot open elgato')
            exit()
        self.game_state = ''
        self.frame = None
        self.trade_state = 'Looking for trade'
        self.names = []
        self.move_inv = False
        

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
        
    async def trade_loop(self):
        try:
            while True:
                ret, self.frame = self.cap.read()
                self.frame = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
                if not ret:
                    print("Can't receive frame")
                    exit()
                # text_frame = self.frame[820:940, 530:1300]
            
                # text = pytesseract.image_to_string(text_frame).replace('\n', '')
                # print(self.trade_state, text)
                # cv.imshow('Frame', self.frame)
                await self.check_disconnect()

                if self.trade_state == 'Look for trade':
                    await self.start_trade()
                if self.trade_state == 'Looking for trade':
                    await self.check_trade_found()
                if self.trade_state == 'Trade found':
                    await self.check_name()
                if self.trade_state == 'Waiting for other':
                    await self.finish_trade()
                if self.trade_state == 'Waiting for trade to finish':
                    await self.check_trade_done()
                
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
            exit()
    
    async def check_name(self):
        name_frame = self.frame[10:70, 400:750]
        name = pytesseract.image_to_string(name_frame).replace('\n', '')
        trade_partner_frame = self.frame[10:70, 100:300]
        trade_partner_text = pytesseract.image_to_string(trade_partner_frame).replace('\n', '')
        if not trade_partner_text == 'Trade Partner':
            return
        await asyncio.sleep(1.5)
        if name in self.names:
            self.trade_partner = name
            await self.innitiate_trade()
        else:
            print([*name])
            print('Partner not in name list')
            await self.exit_trade()
    
    async def check_trade_found(self):
        text_frame = self.frame[820:940, 530:1300]
        
        text = pytesseract.image_to_string(text_frame).replace('\n', '')
        if text == 'A trade partner has been found!':
            self.trade_state = 'Trade found'
            print('Trade found')
            return
        if 'No one could be found!' in text:
            await tap('b')
            self.trade_state = 'Look for trade'
            print('Look for a trade')

    async def innitiate_trade(self):
        if self.move_inv:
            await l_stick_flick(RIGHT)
            await asyncio.sleep(0.5)
            self.move_inv = False
        await tap('a')
        await asyncio.sleep(0.5)
        await tap('a')
        self.trade_state = 'Waiting for other'
        print('Waiting for other')

    async def finish_trade(self):
        text_frame = self.frame[820:940, 530:1300]
        text = pytesseract.image_to_string(text_frame).replace('\n', '')
        if "Do you want to trade" in text:
            await tap('a')
            await asyncio.sleep(1.0)
            await tap('a')
            self.trade_state = 'Waiting for other'
        if "Take good care of" in text:
            print("Saw take care of")
            self.trades_done  += 1
            self.names.remove(self.trade_partner)
            print(self.names)
            await asyncio.sleep(3)
            await self.exit_trade()
        
        
    
    async def exit_trade(self):
        # quit trade inputs
        await tap('b')
        await asyncio.sleep(0.5)
        await tap('a')
        self.trade_state = 'Look for trade'

    async def start_trade(self, names = []):
        if not names and not self.names:
            print('Please enter at least one name')
            exit()
        if self.frame is None:
            ret, self.frame = self.cap.read()
            self.frame = cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY)
            if not ret:
                print("Can't receive frame")
                exit()
        self.names += names
        self.trade_partner = ''
        text_frame = self.frame[10:70, 100:300]
        text = pytesseract.image_to_string(text_frame).replace('\n', '')
        if not text == 'POKE PORT':
            return
        await asyncio.sleep(3)
        await tap('a')
        await asyncio.sleep(1.5)
        await tap('a')
        await asyncio.sleep(1.5)
        await tap('a')
        await asyncio.sleep(1)
        self.trade_state = 'Looking for trade'
        print('Looking for trade')
        await self.trade_loop()

    async def check_disconnect(self):
        text_frame = self.frame[820:940, 530:1300]
        text = pytesseract.image_to_string(text_frame).replace('\n', '')

        if "Your trading partner chose to quit trading" in text:
            await tap('b')
            await asyncio.sleep(0.5)
            await tap('b')
            self.trade_state = 'Look for trade'
            print('Look for trade')

    async def check_trade_done(self):
        text_frame = self.frame[820:940, 530:1300]
        text = pytesseract.image_to_string(text_frame).replace('\n', '')
        if 'Take good care of' in text:
            await tap('b')
            await asyncio.sleep(0.5)
            await self.exit_trade()
    
    def pixel_count(self):
        while True:
            # Capture frame-by-frame
            ret, frame = self.cap.read()
            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            # Our operations on the frame come here
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            # Display the resulting frame
            gray = cv.rectangle(gray, (100,10), (300,70), (255, 0, 0), 2) # name bounding box
            trade_partner_text = gray[10:70, 100:300]
            print([*pytesseract.image_to_string(trade_partner_text).replace('\n', '')])
            cv.imshow('frame', gray)
            if cv.waitKey(1) == ord('q'):
                break
    

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
    print('Tapping', button)
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
    

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', help='The mode to run in', choices=['trade',  'hatch', 'pixels'], required=True)
    parser.add_argument('-n', '--names', help='Names of users', nargs='+', required=False)
    args = parser.parse_args()
    game = Game()
    loop = asyncio.get_event_loop()
    print(args.names)
    if args.mode == 'trade':
        loop.run_until_complete(
            game.start_trade(args.names)
        )
    if args.mode == 'pixels':
        game.pixel_count()

    