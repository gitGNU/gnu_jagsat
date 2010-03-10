#
# This file is copyright Tribeflame Oy, 2009.
#
from tf.gfx import ui
from tf.gfx.imagefile import ImageFile
from OpenGL.GL import *
from OpenGL.GLU import *

from tf.gfx import uiactions

from tf.gfx import uihelp
from tf import signalslot
from tf.gfx import uiactions
import math
import time

import numpy

from PySFML import sf


def get_cross_product(pos1, pos2, pos3):
    _a = pos1
    _b = pos2
    _c = pos3
    a = (_a[2] - _c[2], _a[3] - _c[3], _a[4] - _c[4])
    b = (_b[2] - _c[2], _b[3] - _c[3], _b[4] - _c[4])
    cross = numpy.cross(a, b)
    return cross


def normalize(vec):
    v = math.sqrt(vec[0] * vec[0] + \
                      vec[1] * vec[1] + \
                      vec[2] * vec[2])
    try:
        vec[0] /= v
        vec[1] /= v
        vec[2] /= v
    except ZeroDivisionError:
        pass


class Component3D(ui.Component):

    def __init__(self, parent):
        ui.Component.__init__(self, parent)
        # xrot, yrot, zrot
        self.rotations = [0.0, 0.0, 0.0]

    def Render(self, window):
        for c in self.children_back:
            c.draw(window)

        self._draw_3d(window)

        for c in self.children:
            c.draw(window)

    def _draw_3d(self, window):
        pass


class TextureMapped(Component3D):

    def __init__(self, parent):
        Component3D.__init__(self, parent)
        self.textures = []
        # [ texture,  tx, ty,   x, y, z ...] )
        self.coords = []
        self.displaylist = -1
        self.needs_new_displaylist = True

    def set_color(self, color):
        sf.Drawable.SetColor(self, color)

    def add_coord(self, texture, lst):
        print "TEX", texture
        try:
            id = self.textures.index(texture)
        except ValueError:
            id = len(self.textures)
            self.textures.append(texture)
        #lst is-a [ (tx, ty, x, y, z) ...]
        self.coords.append((texture, lst))
        assert len(lst) == 4
        for i in lst:
            assert len(i) == 5

        if self.needs_new_displaylist == False:
            glDeleteLists(self.displaylist, 1)

        self.needs_new_displaylist = True

    def _draw_3d(self, window):
        view = self.get_view()
        assert view

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Without this, the ordinary SFML sprites will occlude
        # anything with z > 0
        glClear(GL_DEPTH_BUFFER_BIT)

        # LIGHT, must be outside display list
        glEnable(GL_LIGHTING)

        pos = self.GetPosition()

        cx, cy = view.view.GetCenter()
        hx, hy = view.view.GetHalfSize()
        #print "CX, CY", cx, cy
        #print "HX, HY", hx, hy
        #print "POS", pos[0], pos[1]

        # The combination of mkx, mky, sk makes the
        # item correctly positioned, at least for the view center/size
        # that I have tested.
        cx -= pos[0]
        cy -= pos[1]
        # The 1024x800 is the dev linux machine
        # These formulas make a component3d and ui.component
        # have the same graphical positions for the same values
        mkx = 500.0 * window.GetWidth() / 1024.0
        mky = 400.0 * window.GetHeight() / 800.0
        glTranslatef(-cx / mkx, cy / mky, 0.0)

        #sk = 40575.0
        sk = 256.0
        sz = 0.5 # Don't change due to clipping
        scale = self.GetScale()
        glScalef(scale[0] * sk / hx, scale[1] * sk / hy, sz)

        glRotatef(self.rotations[0], 1.0, 0.0, 0.0)
        glRotatef(self.rotations[1], 0.0, 1.0, 0.0)
        glRotatef(self.rotations[2], 0.0, 0.0, 1.0)

        if self.needs_new_displaylist == False:
            glCallList(self.displaylist)
        else:
            # By binding all the required textures, we ensure
            # that the texture is in fact generated by SFML
            # and it is sent to the gpu. Note that this must be done
            # outside of the display list creation, otherwise things
            # slow down considerably.
            for texture, lst in self.coords:
                texture.img.Bind()

            # This is rather slow, so do it here once
            glEnable(GL_LIGHT0)
            glLightfv(GL_LIGHT0, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
            #glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
            #glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 0.0, 1.0, 1.0])
            glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, -30, 1.0])

            # MATERIAL
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE)
            glMaterial(GL_FRONT_AND_BACK, GL_AMBIENT, [0, 0, 0, 1])
            # specular color does not make sense here
            #glMaterial(GL_FRONT_AND_BACK, GL_SPECULAR, [1, 1, 1, 0.2])
            glMaterial(GL_FRONT_AND_BACK, GL_EMISSION, [0, 0, 0, 1])

            #glDisable(GL_LIGHT1)
            #glDisable(GL_LIGHT2)
            #glDisable(GL_LIGHT3)
            #glDisable(GL_LIGHT4)
            #glDisable(GL_LIGHT5)
            #glDisable(GL_LIGHT6)
            #glDisable(GL_LIGHT7)

            glShadeModel(GL_SMOOTH)
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LEQUAL)
            glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

            assert self.displaylist == -1
            self.displaylist = glGenLists(1)
            assert self.displaylist != -1
            glNewList(self.displaylist, GL_COMPILE_AND_EXECUTE)

            # BUG why does this set the color
            self.GetColor()
            #x = self.GetColor()
            #glColor4b(x.r, x.g, x.b, x.a)

            idx = 0
            for texture, lst in self.coords:
                texture.img.Bind()
                glBegin(GL_QUADS)
                assert len(lst) == 4
                cross = get_cross_product(lst[1], lst[2], lst[0])
                normalize(cross)
                glNormal(cross[0], cross[1], cross[2])
                for tx, ty, x, y, z in lst:
                    glTexCoord2f(tx, ty)
                    glVertex3f(x, y, z)
                glEnd()
                idx += 1

            glEndList()
            self.needs_new_displaylist = False
        glDisable(GL_LIGHTING)


def calc_which_face_is_up(component):
    rot = component.rotations
    print "ROTATIONS",
    print rot
    sines = [math.sin(math.radians(x)) for x in rot]
    coses = [math.cos(math.radians(x)) for x in rot]
    rx = [[1, 0, 0],
          [0, coses[0], sines[0]],
          [0, -sines[0], coses[0]],
          ]
    ry = [[coses[1], 0, -sines[1]],
          [0, 1, 0],
          [sines[1], 0, coses[1]],
          ]
    rz = [[coses[2], sines[2], 0],
          [-sines[2], coses[2], 0],
          [0, 0, 1],
          ]
    rx = numpy.matrix(rx)
    ry = numpy.matrix(ry)
    rz = numpy.matrix(rz)
    print "R"
    print rx
    print ry
    print rz
    r = rz * ry * rx
    print r

    #a x b = (a2b3 - a3b2) i + (a3b1 - a1b3) j + (a1b2 - a2b1) k
    normal_to_eye = numpy.matrix([0.0, 0.0, -1.0]).transpose()
    normrot = r * normal_to_eye
    print "NORMROT"
    print normrot
    maxidx = -1
    maxvalue = -1000

    for idx, (texture, lst) in enumerate(component.coords):
        cross = get_cross_product(lst[1], lst[2], lst[0])
        normalize(cross)
        dotprod = numpy.dot(cross, normrot)
        print "FACE:", idx, dotprod
        if dotprod > maxvalue:
            maxvalue = dotprod
            maxidx = idx

    return maxidx


class Rotate3D(uiactions.Gradienter):
    """Rotates a component3d to given rotation."""
    # BUG does not take the fastest possible route. This should
    # be rewritten to not use gradienter, but take 3d space
    # into account and all three rotations.
    #
    # BUG does not rotate x,y,z at different speeds so that they finish
    # at the same time.
    #
    # IDEA 1: for slightly better results, realize that 0..360 wraps around.
    # This is however not the fastest route.
    #
    # IDEA: Transform 3-rotation into 2-rotations, and do only that.

    def __init__(self, startrot, deltarot, endrot):
        uiactions.Gradienter.__init__(self, startrot, deltarot, endrot)

    def _gradient_calculate_start(self):
        for i, rot in enumerate(self.component.rotations):
            self.component.rotations[i] = uihelp.clamp_angle(rot)
        return self.component.rotations

    def _gradienter_do(self):
        self.component.rotations[:] = self.cur[:]


import random


class DiceD6RollAction(uiactions.Action):

    def __init__(self, dx, dy, dz):
        uiactions.Action.__init__(self)
        self.dx = dx
        self.dy = dy
        self.dz = dz

    def _set_component(self, component):
        uiactions.Action._set_component(self, component)
        self.dice = random.randrange(1, 7)
        s = 140
        win = component.get_window()
        self.wall_left = 0 + s
        self.wall_right = win.window.GetWidth() - s
        self.wall_top = 0 + s
        self.wall_bottom = win.window.GetHeight() - s

        self._old_sgndscale = 0

        self.time = 0
        self.zforce = 1.0
        self.wind_drag_speed = 0.98
        self.bounce_drag_speed = 0.4
        self.bounce_drag_zforce = 0.6

        dx = self.dx
        dy = self.dy

        self.speed = math.sqrt(dx * dx + dy * dy)
        self.rollspeed = self.speed
        print "DX DY", dx, dy
        self.move_direction = -math.degrees(math.atan2(dy, dx))
        self.roll_direction = math.degrees(math.atan2(dy, dx)) + 90
        print "ROLL DICE", self.speed, self.move_direction, self.roll_direction

    def step_action(self):
        # BUG real time
        self.time += .00001

        k = 0.0006
        oldscale = self.component.GetScale()[0]

        scale = 1.0 + abs(math.sin(self.time * k) * self.zforce)
        scale *= 0.5
        self.component.SetScale(scale, scale)

        self.speed *= self.wind_drag_speed

        # Bounce?
        sgndscale = uihelp.sign(scale - oldscale)
        if sgndscale:
            if sgndscale != self._old_sgndscale:
                self._old_sgndscale = sgndscale
                if sgndscale == 1:
                    print "BOUNCE"
                    self.zforce *= self.bounce_drag_zforce
                    self.speed *= self.bounce_drag_speed
                    self.rollspeed *= self.bounce_drag_speed
                    if self.zforce < 0.1:
                        self.component.set_dice_value(\
                            calc_which_face_is_up(self.component) + 1)
                        print "FINNISH!"
                        return True

        r = math.radians(self.move_direction)
        dx = math.cos(r) * self.speed
        dy = -math.sin(r) * self.speed
        x, y = self.component.GetPosition()
        x += dx
        y += dy

        self.move_direction = uihelp.clamp_angle(self.move_direction)
        self.roll_direction = uihelp.clamp_angle(self.roll_direction)

        if x < self.wall_left:
            x = abs(x)
            if (90 <= self.move_direction <= 270):
                self.move_direction = 2 * 0 + 180 - self.move_direction
        elif x > self.wall_right:
            x = self.wall_right - (x - self.wall_right)
            if (self.move_direction <= 90 or 270 <= self.move_direction):
                self.move_direction = 2 * 0 + 180 - self.move_direction

        self.move_direction = uihelp.clamp_angle(self.move_direction)

        if y < self.wall_top:
            y = abs(y)
            if (self.move_direction <= 180):
                print "MV1", self.move_direction
                self.move_direction = 2 * 90 + 180 - self.move_direction
        elif y > self.wall_bottom:
            y = self.wall_bottom - (y - self.wall_bottom)
            if (180 <= self.move_direction):
                print "MV2", self.move_direction
                self.move_direction = 2 * 90 + 180 - self.move_direction

        r = math.radians(self.roll_direction)
        dx = math.cos(r) * self.rollspeed
        dy = -math.sin(r) * self.rollspeed
        dz = self.dz * self.rollspeed * 0.2
        rot = self.component.rotations
        k = 0.1 #
        rot[0] += dx * k
        rot[1] += dy * k
        rot[2] += dz * k

        self.component.SetPosition(x, y)


class Dice(TextureMapped):

    def __init__(self, parent, filenames):
        TextureMapped.__init__(self, parent)
        self.set_enable_hitting(True)

        self.signal_dice_rolled = signalslot.Signal("DiceRoll")
        self.set_center_rel(ui.CENTER)
        self.dice_value = 6

        dice_texture_images = []
        for fname in filenames:
            t = ImageFile.new_image(fname)
            dice_texture_images.append(t)

        # front face
        self.add_coord(dice_texture_images[0],
                       [(0.0, 0.0, -0.5, -0.5, 0.5),
                        (1.0, 0.0, 0.5, -0.5, 0.5),
                        (1.0, 1.0, 0.5, 0.5, 0.5),
                        (0.0, 1.0, -0.5, 0.5, 0.5),
                        ])

        # Top Face
        self.add_coord(dice_texture_images[1],
                       [(0.0, 1.0, -0.5, 0.5, -0.5),
                        (0.0, 0.0, -0.5, 0.5, 0.5),
                        (1.0, 0.0, 0.5, 0.5, 0.5),
                        (1.0, 1.0, 0.5, 0.5, -0.5),
                        ])

        # Right face
        self.add_coord(dice_texture_images[2],
                       [(1.0, 0.0, 0.5, -0.5, -0.5),
                        (1.0, 1.0, 0.5, 0.5, -0.5),
                        (0.0, 1.0, 0.5, 0.5, 0.5),
                        (0.0, 0.0, 0.5, -0.5, 0.5),
                        ])

        # Left Face
        self.add_coord(dice_texture_images[3],
                       [(0.0, 0.0, -0.5, -0.5, -0.5),
                        (1.0, 0.0, -0.5, -0.5, 0.5),
                        (1.0, 1.0, -0.5, 0.5, 0.5),
                        (0.0, 1.0, -0.5, 0.5, -0.5),
                        ])

        # Bottom Face
        self.add_coord(dice_texture_images[4],
                       [(1.0, 1.0, -0.5, -0.5, -0.5),
                        (0.0, 1.0, 0.5, -0.5, -0.5),
                        (0.0, 0.0, 0.5, -0.5, 0.5),
                        (1.0, 0.0, -0.5, -0.5, 0.5),
                        ])

        # Back Face
        self.add_coord(dice_texture_images[5],
                       [(1.0, 0.0, -0.5, -0.5, -0.5),
                        (1.0, 1.0, -0.5, 0.5, -0.5),
                        (0.0, 1.0, 0.5, 0.5, -0.5),
                        (0.0, 0.0, 0.5, -0.5, -0.5),
                        ])

        self.action_pan_previous_mousepos = None
        self.rolled_due_to_pan = False

    def _get_unscaled_width(self):
        return 256

    def _get_unscaled_height(self):
        return 256

    def set_dice_value(self, v):
        self.dice_value = v
        print "Set dice value to ", v
        e = signalslot.Event("DiceRollEvent",
                             dice = self.dice_value)
        self.signal_dice_rolled.call(e)

    def roll(self, dx, dy, dz):
        d = DiceD6RollAction(dx, dy, dz)
        self.add_action_sequence([d])
        self.set_enable_hitting(False)

    def user_hit(self, gameloop, x, y):
        s = 150
        dx = random.randrange(-s, s)
        dy = math.sqrt(s * s - dx * dx) + random.randrange(30)
        dz = random.randrange(-20, 20)
        self.roll(dx, dy, dz)

    def start_pan(self, event):
        t = time.time()
        self.action_pan_start_mousepos = [event[0],
                                          event[1],
                                          t]

        self.action_pan_previous_mousepos = [event[0],
                                             event[1],
                                             t]

    def do_pan(self, event):
        if self.rolled_due_to_pan:
            return
        x = event[0]
        y = event[1]
        t = time.time()

        dx = x - self.action_pan_previous_mousepos[0]
        dy = y - self.action_pan_previous_mousepos[1]
        dt = t - self.action_pan_previous_mousepos[2]

        self.action_pan_previous_mousepos[0] = x
        self.action_pan_previous_mousepos[1] = y
        self.action_pan_previous_mousepos[2] = t

        s = 40
        if abs(dx) > s or abs(dy) > s or \
                (abs(dx) < 4 and abs(dy) < 4 and dt > 0.2):
            dx = x - self.action_pan_start_mousepos[0]
            dy = y - self.action_pan_start_mousepos[1]
            self._start_roll(dx, dy)

    def end_pan(self, event):
        if self.rolled_due_to_pan:
            return
        x = event[0]
        y = event[1]
        dx = x - self.action_pan_start_mousepos[0]
        dy = y - self.action_pan_start_mousepos[1]
        self._start_roll(dx, dy)

    def _start_roll(self, dx, dy):
        self.rolled_due_to_pan = True
        dt = time.time() - self.action_pan_start_mousepos[2]
        dt = max(dt, 0.01)
        k = 20
        dx /= dt * k
        dy /= dt * k
        dz = random.randrange(-50, 50) / (dt * k)
        dz = max(min(dz, 20), -20)
        while abs(dx) < 0.2:
            dx += 0.05
        while abs(dy) < 0.2:
            dy += 0.05
        # Ensure enough speed
        while True:
            s = math.sqrt(dx * dx + dy * dy)
            if s >= 150:
                break
            dx *= 1.1
            dy *= 1.1

        self.roll(dx, dy, dz)
