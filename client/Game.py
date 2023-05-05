import cv2 as cv
import numpy as np
import asyncio
from client import main
import pytesseract
import argparse
import logging
import math 

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
        self.code = None
        

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
        list_names = [val for val in self.names if name in val or val in name]
        if list_names:
            self.trade_partner = list_names[0]
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
            self.names.remove(self.trade_partner) ################################
            self.move_inv = True
            print(self.names)
            await asyncio.sleep(3)
            await self.exit_trade()
        
        
    
    async def exit_trade(self):
        # quit trade inputs
        await tap('b')
        await asyncio.sleep(0.5)
        await tap('a')
        self.trade_state = 'Look for trade'

    async def start_trade(self, names = [], code = ""):
        if not names and not self.names:
            print('Please enter at least one name')
            exit()
        # if not self.code:
        #     self.code = code
        #     await self.set_trade_code(self.code)
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
        await asyncio.sleep(3.5)
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
    
    async def set_trade_code(self, code):
        await tap('a')
        await asyncio.sleep(1)
        await l_stick_flick(DOWN)
        await tap('a')
        await asyncio.sleep(1)
        # code screen should be open
        # now screen grab the number of characters input
        ret, frame = self.cap.read()
        if not ret:
            print("Can't receive frame")
            exit()
        num_digits_frame = frame[375:425, 1375:1395]
        num_digits = int(pytesseract.image_to_string(num_digits_frame, config='--psm 6').replace('\n', ''))
        for _ in range(num_digits):
            await tap('b')
            await asyncio.sleep(0.5)
        # now we must input code, we start at 1 
        curr_num = 1
        for next_num in code:
            print('Moving from', curr_num, 'to', next_num)
            next_num = int(next_num)
            # first move vertically
            if (curr_num - next_num) < 0:
                # we need to move down
                print('Down', math.floor((next_num - curr_num) / 3))
                for _ in range(math.floor((next_num - curr_num) % 3)):
                    await l_stick_flick(DOWN)
                    await asyncio.sleep(0.5)
            else:
                print('Up', math.floor((curr_num - next_num) % 3))
                for _ in range(math.floor((curr_num - next_num) % 3)):
                    await l_stick_flick(UP)
                    await asyncio.sleep(0.5)
            # vert move should be done
            # just mod 3 both numbers, then move left right or stay
            if (curr_num % 3 > next_num % 3):
                print('Left', curr_num % 3 - next_num % 3)
                for _ in range((curr_num % 3) - (next_num % 3)):
                    await l_stick_flick(LEFT)
                    await asyncio.sleep(0.5)
            else:
                print('Right', (next_num % 3) - (curr_num % 3))
                for _ in range(next_num % 3 - curr_num % 3):
                    await l_stick_flick(RIGHT)
                    await asyncio.sleep(0.5)
            # movement is done
            await tap('a')
            curr_num = next_num
        # now code should be entered correctly
        await tap('plus')
        await asyncio.sleep(0.5)
        await l_stick_flick(UP)
        await asyncio.sleep(0.5)
        await tap('b')
        # now move on to main script


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
            gray = cv.rectangle(gray, (1375,375), (1395,425), (255, 0, 0), 2) # name bounding box
            trade_partner_text = frame[375:425, 1375:1395]
            print([*pytesseract.image_to_string(trade_partner_text, config='--psm 6').replace('\n', '')])
            cv.imshow('frame', trade_partner_text)
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
    parser.add_argument('-c', '--code', help='Trading code', required=False)
    args = parser.parse_args()
    game = Game()
    loop = asyncio.get_event_loop()
    print(args.names)
    if args.mode == 'trade':
        loop.run_until_complete(
            game.start_trade(args.names, args.code)
        )
    if args.mode == 'pixels':
        game.pixel_count()

    