#!/usr/bin/env python
import sys
import pygame
import random


##  PySame
##
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

    class Particle(object):

        def __init__(self, surface, rect, count):
            self.surface = surface
            self.rect = rect
            self.count = count
            return

        def __repr__(self):
            return '<Particle: %r %r>' % (self.surface, self.rect)

        def update(self):
            self.count -= 1
            self.rect.y -= 2
            return
            
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

    BGCOLOR = (0,0,80)
    HICOLOR = (255,255,255)
    SCORECOLOR = (255,255,255)
    BORDERCOLOR = (0,0,0)

    def __init__(self, boardsize=(20,15), blocksize=32):
        self.boardsize = boardsize
        self.blocksize = blocksize
        self.surface = pygame.display.get_surface()
        self.font = pygame.font.Font('prstartk.ttf', 24)
        self.sounds_remove = [
            pygame.mixer.Sound('remove1.wav'),
            pygame.mixer.Sound('remove2.wav'),
            pygame.mixer.Sound('remove3.wav'),
            pygame.mixer.Sound('remove4.wav'),
            ]
        return

    def init_game(self):
        self._score = 0
        self._init_blocks()
        self._particles = []
        return

    def repaint(self):
        self.surface.fill(self.BGCOLOR)
        self._paint_blocks()
        self._paint_highlights()
        for part in self._particles:
            self.surface.blit(part.surface, part.rect)
        self._render_text((u'SCORE: %d' % self._score), self.SCORECOLOR, (0,0))
        pygame.display.flip()
        return

    def update(self):
        for part in self._particles:
            part.update()
        self._particles = [ part for part in self._particles if 0 < part.count ]
        self.repaint()
        return

    def remove_highlights(self):
        assert self._highlighted
        n = len(self._highlighted)
        score = n*n
        (x,y) = self._get_blocks_center(self._highlighted)
        self._score += score
        if 16 <= n:
            i = 3
        elif 8 <= n:
            i = 2
        elif 4 <= n:
            i = 1
        else:
            i = 0
        self.sounds_remove[i].play()
        self._remove_blocks(self._highlighted)
        self._update_groups()
        pos = (x*self.blocksize+self.blocksize/2, y*self.blocksize+self.blocksize/2)
        self._add_text_particle(str(score), self.SCORECOLOR, pos)
        return

    def _remove_blocks(self, blocks):
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

    def _init_blocks(self):
        self._matrix = []
        (bwidth,bheight) = self.boardsize
        for y in xrange(bheight):
            self._matrix.append([ self.Block() for x in xrange(bwidth) ])
        self._update_groups()
        return

    def _update_groups(self):
        self._focus = None
        self._highlighted = set()
        # clustering
        (bwidth,bheight) = self.boardsize
        josh = {}
        i = 0
        for y in xrange(bheight):
            for x in xrange(bwidth):
                pos0 = (x,y)
                block0 = self._matrix[y][x]
                if block0 is None: continue
                if pos0 in josh:
                    group0 = josh[pos0]
                    while group0.parent is not None:
                        group0 = group0.parent
                else:
                    group0 = josh[pos0] = self.Group(i)
                    i += 1
                neighbours = []
                if x+1 < bwidth:
                    neighbours.append( ((x+1,y), self._matrix[y][x+1]) )
                if y+1 < bheight:
                    neighbours.append( ((x,y+1), self._matrix[y+1][x]) )
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
        self._groups = {}
        for (pos,group) in josh.iteritems():
            while group.parent is not None:
                group = group.parent
            group.add(pos)
            self._groups[pos] = group
        # ending detection.
        self._movable = False
        for group in self._groups.itervalues():
            if 2 <= len(group.blocks):
                self._movable = True
        return

    def _add_text_particle(self, text, color, (x,y)):
        glyph = self.font.render(text, 1, color)
        (w,h) = glyph.get_size()
        part = self.Particle(glyph, pygame.Rect(x-w/2, y-h/2, w, h), 10)
        self._particles.append(part)
        return

    def _render_text(self, text, color, pos):
        glyph = self.font.render(text, 1, color)
        self.surface.blit(glyph, pos)
        return

    def _paint_blocks(self):
        (bwidth,bheight) = self.boardsize
        lines = []
        for y in xrange(bheight):
            row = self._matrix[y]
            for x in xrange(bwidth):
                block = row[x]
                if block is None: continue
                rect = self._get_blockrect((x,y))
                group = self._groups.get((x,y))
                self.surface.fill(self.surface.map_rgb(block.color), rect)
                if group is not self._groups.get((x+1,y)):
                    lines.append((rect.topright, rect.bottomright))
                if group is not self._groups.get((x,y+1)):
                    lines.append((rect.bottomleft, rect.bottomright))
        for (p1,p2) in lines:
            pygame.draw.line(self.surface, self.BORDERCOLOR, p1, p2)
        return

    def _paint_highlights(self):
        lines = []
        for (x,y) in self._highlighted:
            rect = self._get_blockrect((x,y))
            group = self._groups.get((x,y))
            if group is not self._groups.get((x-1,y)):
                lines.append((rect.topleft, rect.bottomleft))
            if group is not self._groups.get((x+1,y)):
                lines.append((rect.topright, rect.bottomright))
            if group is not self._groups.get((x,y-1)):
                lines.append((rect.topleft, rect.topright))
            if group is not self._groups.get((x,y+1)):
                lines.append((rect.bottomleft, rect.bottomright))
        for (p1,p2) in lines:
            pygame.draw.line(self.surface, self.HICOLOR, p1, p2, 2)
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

    def _get_blocks_center(self, blocks):
        (x,y,n) = (0,0,0)
        for (x1,y1) in blocks:
            x += x1
            y += y1
            n += 1
        return (x/n,y/n)

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
                self.update()
            elif ev.type == pygame.MOUSEMOTION:
                self._focus = self._get_blockpos(ev.pos)
                highlighted = self._get_highlighted(self._focus)
                if 2 <= len(highlighted):
                    self._highlighted = highlighted
                else:
                    self._highlighted = set()
            elif ev.type == pygame.MOUSEBUTTONUP:
                if self._highlighted:
                    self.remove_highlights()
        pygame.time.set_timer(pygame.USEREVENT, 0)
        return

# main
def main(argv):
    pygame.mixer.pre_init(22050)
    pygame.init()
    pygame.display.set_mode((640,480))
    game = PySame()
    game.init_game()
    return game.run()

if __name__ == '__main__': sys.exit(main(sys.argv))
