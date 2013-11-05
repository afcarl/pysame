#!/usr/bin/env python
import sys
import pygame
import random

class Group(object):

    def __init__(self, i):
        self.i = i
        self.parent = None
        self.blocks = []
        return

    def __repr__(self):
        return '<%r: %r>' % (self.i, self.blocks)

    def add(self, block):
        self.blocks.append(block)
        return

def get_groups(matrix, boardsize):
    (bwidth,bheight) = boardsize
    josh = {}
    i = 0
    for y in xrange(bheight):
        for x in xrange(bwidth):
            pos0 = (x,y)
            block0 = matrix[y][x]
            if block0 is None: continue
            if pos0 in josh:
                group0 = josh[pos0]
                while group0.parent is not None:
                    group0 = group0.parent
            else:
                group0 = josh[pos0] = Group(i)
                i += 1
            neighbours = []
            if x+1 < bwidth:
                neighbours.append( ((x+1,y), matrix[y][x+1]) )
            if y+1 < bheight:
                neighbours.append( ((x,y+1), matrix[y+1][x]) )
            for (pos1,block1) in neighbours:
                if block1 is None: continue
                if block1.color != block0.color: continue
                if pos0 not in josh:
                    assert 0
                elif pos1 not in josh:
                    josh[pos1] = josh[pos0]
                else:
                    group1 = josh[pos1]
                    while group1.parent is not None:
                        group1 = group1.parent
                    assert group1 is not None
                    if group1 is not group0:
                        group1.parent = group0
    groups = {}
    for (pos,group) in josh.iteritems():
        while group.parent is not None:
            group = group.parent
        group.add(pos)
        groups[pos] = group
    return groups

class PySame(object):

    class Block(object):
        
        COLORS = [ (255,0,0), (0,255,0), (220,220,0),
                   (0,0,220), (0,200,255) ]
        
        def __init__(self):
            self.i = random.randrange(len(self.COLORS))
            self.color = self.COLORS[self.i]
            return

        def __repr__(self):
            return '<[%d]>' % (self.i)

    def __init__(self, surface, boardsize=(20,15), blocksize=32):
        self.surface = surface
        self.boardsize = boardsize
        self.blocksize = blocksize
        return

    BGCOLOR = (0,0,80)
    HICOLOR = (255,255,255)
    BORDERCOLOR = (0,0,0)

    def repaint(self):
        self.surface.fill(self.BGCOLOR)
        (bwidth,bheight) = self.boardsize
        lines = []
        for y in xrange(bheight):
            row = self._matrix[y]
            for x in xrange(bwidth):
                block = row[x]
                if block is None: continue
                rect = self._get_blockrect((x,y))
                if (x,y) in self._highlighted:
                    self.surface.fill(self.HICOLOR, rect)
                else:
                    self.surface.fill(self.surface.map_rgb(block.color), rect)
                group = self._groups.get((x,y))
                if group is not self._groups.get((x+1,y)):
                    lines.append((rect.topright, rect.bottomright))
                if group is not self._groups.get((x,y+1)):
                    lines.append((rect.bottomleft, rect.bottomright))
        for (p1,p2) in lines:
            pygame.draw.line(self.surface, self.BORDERCOLOR, p1, p2)
        pygame.display.flip()
        return

    def init_blocks(self):
        self._matrix = []
        (bwidth,bheight) = self.boardsize
        for y in xrange(bheight):
            self._matrix.append([ self.Block() for x in xrange(bwidth) ])
        self._update_groups()
        return

    def remove_blocks(self, blocks):
        (bwidth,bheight) = self.boardsize
        cols = set()
        for (x,y) in blocks:
            self._matrix[y][x] = None
            cols.add(x)
        for x in cols:
            y = bheight-1
            for y0 in xrange(y, 0, -1):
                if self._matrix[y0][x] is not None:
                    self._matrix[y][x] = self._matrix[y0][x]
                    y -= 1
            while 0 <= y:
                self._matrix[y][x] = None
                y -= 1
        x = 0
        for x0 in xrange(bwidth):
            if self._matrix[bheight-1][x0] is not None:
                for y in xrange(bheight):
                    self._matrix[y][x] = self._matrix[y][x0]
                x += 1
        while x < bwidth:
            for y in xrange(bheight):
                self._matrix[y][x] = None
            x += 1
        return

    def _update_groups(self):
        self._groups = get_groups(self._matrix, self.boardsize)
        self._focus = None
        self._highlighted = set()
        return

    def _get_blockpos(self, (x,y)):
        (bwidth,bheight) = self.boardsize
        x = x/self.blocksize
        y = y/self.blocksize
        if x < 0 or bwidth <= x or y < 0 or bheight <= y: return None
        return (x, y)
        
    def _get_blockrect(self, (x,y)):
        return pygame.Rect(x*self.blocksize, y*self.blocksize,
                           self.blocksize, self.blocksize)

    def _get_highlighted(self, focus):
        highlighted = set()
        if focus in self._groups:
            group = self._groups[focus]
            highlighted.update(group.blocks)
        return highlighted

    def run(self, msec=50):
        loop = True
        pygame.time.set_timer(pygame.USEREVENT, msec)
        while loop:
            ev = pygame.event.wait()
            if ev.type == pygame.QUIT:
                loop = False
            elif ev.type == pygame.KEYDOWN:
                loop = False
            elif ev.type == pygame.VIDEOEXPOSE:
                self.repaint()
            elif ev.type == pygame.USEREVENT:
                self.repaint()
            elif ev.type == pygame.MOUSEMOTION:
                self._focus = self._get_blockpos(ev.pos)
                highlighted = self._get_highlighted(self._focus)
                if 2 <= len(highlighted):
                    self._highlighted = highlighted
                else:
                    self._highlighted = set()
            elif ev.type == pygame.MOUSEBUTTONUP:
                self.remove_blocks(self._highlighted)
                self._update_groups()
        pygame.time.set_timer(pygame.USEREVENT, 0)
        return

def main(argv):
    pygame.init()
    pygame.display.set_mode((640,480))
    surface = pygame.display.get_surface()
    game = PySame(surface)
    game.init_blocks()
    return game.run()

if __name__ == '__main__': sys.exit(main(sys.argv))
