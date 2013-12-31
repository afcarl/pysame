#!/usr/bin/env python
import sys
import pygame

def main(argv):
    blocksize = 32
    blockcolors = [
        '#ff0000', '#00ff00', '#dddd00',
        '#0000dd', '#00ccff', '#ff00cc',
    ]
    img = pygame.Surface((blocksize*len(blockcolors), blocksize))
    for (i,color) in enumerate(blockcolors):
        x = blocksize*i
        color = pygame.Color(color)
        img.fill(color, (x, 0, blocksize, blocksize))
    pygame.image.save(img, 'out.png')
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))
