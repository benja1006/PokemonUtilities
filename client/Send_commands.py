from client import main
import asyncio

#Stick consts
DOWN=(2048,4095)
UP=(2048,0)
LEFT=(0, 2048)
RIGHT=(4095,2048)

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


async def open_inventory():
    """Open the inventory from the main walking around screen
    """
    await tap('x')
    await asyncio.sleep(5)
    await l_stick_flick(DOWN)
    await asyncio.sleep(5)
    await tap('a')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        open_inventory()
    )