#
#  Copyright (C) 2009 The JAGSAT project team.
#
#  This software is in development and the distribution terms have not
#  been decided yet. Therefore, its distribution outside the JAGSAT
#  project team or the Project Course evalautors in Abo Akademy is
#  completly forbidden without explicit permission of their authors.
#

import unittest
from base.signal import *
from base.meta import mixin


CleverSlot = mixin (Trackable, Slot)

class TestSignalSlot (unittest.TestCase):

    class Counter (object):
        def __init__ (self, val = 0):
            super (TestSignalSlot.Counter, self).__init__ ()
            self.val = val
        def increase (self):
            self.val += 1
            return self.val
        def decrease (self):
            self.val -= 1
            return self.val

    def test_signal (self):
        sig = Signal ()
        cnt = TestSignalSlot.Counter ()

        slt_a = sig.connect (cnt.increase)
        sig += cnt.decrease
        self.assertEquals (sig.count, 2)

        sig.notify ()
        self.assertEquals (cnt.val, 0)
        self.assertEquals (sig.fold (lambda x, y: x+y), 1)
        self.assertEquals (sig.fold (lambda x, y: x+y, 1), 2)

        sig.disconnect (cnt.decrease)
        self.assertEquals (sig.count, 1)
        
        sig.notify ()
        self.assertEquals (cnt.val, 1)

        sig.disconnect (slt_a)
        self.assertEquals (sig.count, 0)

    def test_cleverness (self):
        
        sig_a = Signal ()
        sig_b = Signal ()
        cnt = TestSignalSlot.Counter ()
        slt = CleverSlot (cnt.increase)
        
        sig_a += slt
        sig_a += slt
        sig_b += slt
        self.assertEquals (slt.source_count, 2)

        sig_a ()
        self.assertEquals (cnt.val, 1)
        sig_b ()
        self.assertEquals (cnt.val, 2)

        slt.disconnect_sources ()
        self.assertEquals (slt.source_count, 0)
        self.assertEquals (sig_a.count, 0)
        self.assertEquals (sig_b.count, 0)

    def test_decorator (self):
        class Decorated:
            @slot
            def function (self):
                return "called"

        d = Decorated ()
        self.assertEquals (d.function (), "called")
        self.assertTrue (isinstance (d.function, Trackable))
        self.assertEquals (d.function, d.function)
        
    def test_decorator_slotable (self):

        class Decorated (Tracker):
            @slot
            def one (self):
                return "one"
            @slot
            def two (self):
                return "two"

        d = Decorated ()
        s = Signal ()

        s += d.one
        self.assertEqual (d._trackables, [d.one])
        self.assertEqual (s.count, 1)
        
        s += d.two
        self.assertEqual (d._trackables, [d.one, d.two])
        self.assertEqual (s.count, 2)

        s += d.two
        self.assertEqual (d._trackables, [d.one, d.two])
        self.assertEqual (s.count, 2)

        d.disconnect_all ()
        self.assertEqual (s.count, 0)

    def test_decorator_signal (self):

        class Decorated (object):
            def __init__ (self):
                self.value = 1
            @signal
            def after (self, param):
                self.value = self.value + param
                return self.value
            @signal_before
            def before (self, param):
                self.value = self.value - param
                return self.value

        d = Decorated ()

        d.after += lambda _: self.assertEquals (d.value, 2)
        d.before += lambda _: self.assertEquals (d.value, 2)
        
        res = d.after (1)
        self.assertEquals (res, 2)
        res = d.before (1)
        self.assertEquals (res, 1)

    def test_auto_signaler_set (self):
        self._test_auto_signaler (AutoSignalSender)

    def test_auto_forward_get (self):
        self._test_auto_signaler (AutoSignalSenderGet)

    def _test_auto_signaler (self, base_class):

        class Tester (Receiver, base_class):
            def __init__ (self):
                base_class.__init__ (self)
                self.value = 0
                self.signal = Signal ()
                self.signal += self.non_decorated
                
            @signal
            def decorated (self, param):
                self.value += param

            def non_decorated (self, param):
                self.value += -param

        source = Tester ()
        dest = Tester ()

        source.connect (dest)
        source.signal (1)
        self.assertEqual (dest.value, -1)

        source.decorated (2)
        self.assertEqual (dest.value, 1)