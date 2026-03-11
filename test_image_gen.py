import asyncio
from image_generator import generate_carousel_images

content = {
    "cover": "CELL'S SECRET ENGINE UNLOCKED: CANCER'S NEW ENEMY?",
    "slide_1": "Imagine finding a whole new factory running inside something you thought you knew inside out. Scientists just did that, deep within our cells. They uncovered hundreds of tiny workers, called metabolic enzymes, mysteriously attached to our DNA right inside the cell's command center, the nucleus. This completely rewrites what we thought we knew about how our cells function and manage their energy.",
    "slide_2": "These newly found enzymes aren't just lounging around. They form unique patterns, like fingerprints, in different body tissues and even in cancers. When DNA gets damaged, these specialized enzymes quickly gather around the affected areas, acting like a rapid repair crew. This critical process helps fix errors and keep our genetic code intact, preventing potential health issues. Over 300 unique enzyme types were observed.",
    "slide_3": "This breakthrough reveals an unexpected direct connection between a cell's energy system and how our genes are controlled. It offers powerful new clues on how cancers grow and resist current treatments. Understanding these 'nuclear metabolic fingerprints' could lead to entirely new ways to stop cancer cells in their tracks, potentially leading to treatment breakthroughs with an estimated 25% improvement in targeted therapy development."
}

async def run():
    print(await generate_carousel_images(content))

asyncio.run(run())
