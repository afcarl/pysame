#!/usr/bin/env python
import sys
import pygame
import random


##  Board
##
class Board(object):

    BG_COLOR = (0,0,80)
    HI_COLOR = (255,255,255)
    BORDER_COLOR = (0,0,0)
    BLOCK_COLORS = [ (255,0,0), (0,255,0), (220,220,0),
                     (0,0,220), (0,200,255) ]
    
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

    def __init__(self, (bwidth, bheight), blocksize=32):
        self.bheight = bheight
        self.blocksize = blocksize
        self._block = []
        self._selected = None
        n = len(self.BLOCK_COLORS)
        for x in xrange(bwidth):
            self._block.append([ random.randrange(n) for y in xrange(bheight) ])
        self._update_groups()
        return

    def get_bwidth(self):
        return len(self._block)

    def get_size(self):
        return (self.get_bwidth()*self.blocksize,
                self.bheight*self.blocksize)

    def get_selection(self):
        return len(self._selected)

    def get_selection_rect(self):
        return self._get_blockrect(self._selected)
        
    def get_blockpos(self, (x,y)):
        bwidth = self.get_bwidth()
        x = x/self.blocksize
        y = y/self.blocksize
        if x < 0 or bwidth <= x or y < 0 or self.bheight <= y:
            raise ValueError((x,y))
        return (x, y)
        
    def render(self):
        surface = pygame.Surface(self.get_size())
        surface.fill(self.BG_COLOR)
        self._paint_blocks(surface)
        self._paint_selection(surface)
        return surface

    def update_selection(self, p):
        selected = self._get_selected(p)
        if 2 <= len(selected):
            self._selected = selected
        else:
            self._selected = set()
        return
        
    def remove_selection(self):
        self._remove_blocks(self._selected)
        return

    def _update_groups(self):
        self._selected = set()
        # clustering
        josh = {}
        i = 0
        bwidth = self.get_bwidth()
        for x in xrange(bwidth):
            for y in xrange(self.bheight):
                pos0 = (x,y)
                block0 = self._block[x][y]
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
                    neighbours.append( ((x+1,y), self._block[x+1][y]) )
                if y+1 < self.bheight:
                    neighbours.append( ((x,y+1), self._block[x][y+1]) )
                for (pos1,block1) in neighbours:
                    if block1 is None: continue
                    if block1 != block0: continue
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
        return

    def _remove_blocks(self, blocks):
        rows = set()
        for (x,y) in blocks:
            self._block[x][y] = None
            rows.add(x)
        for x in rows:
            row = self._block[x]
            y1 = 0
            while y1 < len(row):
                if row[y1] is not None:
                    y1 += 1
                    continue
                for y0 in xrange(y1+1, len(row)):
                    if row[y0] is not None:
                        row[y1] = row[y0]
                        row[y0] = None
                        break
                else:
                    row[y1] = None
                    y1 += 1
        self._block = [ row for row in self._block if row[0] is not None ]
        self._update_groups()
        return

    def _paint_blocks(self, surface):
        bwidth = self.get_bwidth()
        lines = []
        for x in xrange(bwidth):
            row = self._block[x]
            for y in xrange(len(row)):
                block = row[y]
                if block is None: continue
                rect = self._get_blockrect([(x,y)])
                group = self._groups.get((x,y))
                color = self.BLOCK_COLORS[block]
                surface.fill(color, rect)
                if group is not self._groups.get((x+1,y)):
                    lines.append((rect.topright, rect.bottomright))
                if group is not self._groups.get((x,y+1)):
                    lines.append((rect.topleft, rect.topright))
        for (p1,p2) in lines:
            pygame.draw.line(surface, self.BORDER_COLOR, p1, p2)
        return

    def _paint_selection(self, surface):
        lines = []
        for (x,y) in self._selected:
            rect = self._get_blockrect([(x,y)])
            group = self._groups.get((x,y))
            if group is not self._groups.get((x-1,y)):
                lines.append((rect.topleft, rect.bottomleft))
            if group is not self._groups.get((x+1,y)):
                lines.append((rect.topright, rect.bottomright))
            if group is not self._groups.get((x,y-1)):
                lines.append((rect.bottomleft, rect.bottomright))
            if group is not self._groups.get((x,y+1)):
                lines.append((rect.topleft, rect.topright))
        for (p1,p2) in lines:
            pygame.draw.line(surface, self.HI_COLOR, p1, p2, 2)
        return
        
    def _get_blockrect(self, blocks):
        rect = None
        for (x,y) in blocks:
            r = pygame.Rect(x*self.blocksize, (self.bheight-1-y)*self.blocksize,
                            self.blocksize, self.blocksize)
            if rect is None:
                rect = r
            else:
                rect.union_ip(r)
        return rect

    def _get_selected(self, focus):
        selected = set()
        if focus in self._groups:
            group = self._groups[focus]
            selected.update(group.blocks)
        return selected


##  PySame
##
class PySame(object):

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
            
    BG_COLOR = (0,0,80)
    TEXT_COLOR = (255,255,255)

    def __init__(self, blocksize=32):
        self.blocksize = blocksize
        self.surface = pygame.display.get_surface()
        self.font = pygame.font.Font('prstartk.ttf', blocksize)
        self.sound_remove = pygame.mixer.Sound('remove2.wav')
        return

    def start(self, boardsize=(20,15)):
        self._board = Board(boardsize, blocksize=self.blocksize)
        self._score = 0
        self._particles = []
        return

    def repaint(self):
        self.surface.fill(self.BG_COLOR)
        (width,height) = self.surface.get_size()
        board = self._board.render()
        (w,h) = board.get_size()
        self.surface.blit(board, ((width-w)/2,height-h))
        for part in self._particles:
            self.surface.blit(part.surface, part.rect)
        text = (u'SCORE: %d' % self._score)
        self._render_text(text, self.TEXT_COLOR, (0,0))
        pygame.display.flip()
        return

    def update(self):
        for part in self._particles:
            part.update()
        self._particles = [ part for part in self._particles if 0 < part.count ]
        self.repaint()
        return

    def _add_particle(self, surface, (x,y)):
        (w,h) = surface.get_size()
        part = self.Particle(surface, pygame.Rect(x-w/2, y-h/2, w, h), 10)
        self._particles.append(part)
        return

    def _render_text(self, text, color, pos):
        glyph = self.font.render(text, 1, color)
        self.surface.blit(glyph, pos)
        return

    def _get_blockpos(self, (x,y)):
        (width,height) = self.surface.get_size()
        (w,h) = self._board.get_size()
        x -= (width-w)/2
        y = height-y
        return self._board.get_blockpos((x,y))

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
                try:
                    p = self._get_blockpos(ev.pos)
                    self._board.update_selection(p)
                except ValueError:
                    pass
            elif ev.type == pygame.MOUSEBUTTONUP:
                n = self._board.get_selection()
                if n:
                    self._score += n*n
                    self.sound_remove.play()
                    rect = self._board.get_selection_rect()
                    surface = self.font.render(str(n), 1, self.TEXT_COLOR)
                    self._add_particle(surface, rect.center)
                    self._board.remove_selection()
                try:
                    p = self._get_blockpos(ev.pos)
                    self._board.update_selection(p)
                except ValueError:
                    pass
        pygame.time.set_timer(pygame.USEREVENT, 0)
        return

# main
def main(argv):
    pygame.mixer.pre_init(22050)
    pygame.init()
    pygame.display.set_mode((640,480))
    game = PySame()
    game.start()
    return game.run()

if __name__ == '__main__': sys.exit(main(sys.argv))
