#
#  Copyright (C) 2009 The JAGSAT project team.
#
#  This software is in development and the distribution terms have not
#  been decided yet. Therefore, its distribution outside the JAGSAT
#  project team or the Project Course evalautors in Abo Akademy is
#  completly forbidden without explicit permission of their authors.
#

import unittest

from base.tree import *

class TestAutoTree (unittest.TestCase):

    class ValueTree (AutoTree):
        def __init__ (self, default = None):
            super (TestAutoTree.ValueTree, self).__init__ ()
            self.value = default

    class CountingTree (AutoTree):
        def __init__ (self):
            super (TestAutoTree.CountingTree, self).__init__ ()
            self.childs = 0
        def _handle_tree_new_child (self, child):
            self.childs += 1
        def _handle_tree_del_child (self, child):
            self.childs -= 1

    def setUp (self):
        self._tree_1 = TestAutoTree.ValueTree ()
        self._tree_1.child ('a').value = 1
        self._tree_1.path ('a.b.c').value = 2

    def tearDown (self):
        self._tree_1 = None

    def test_paths_rename (self):
        child_1 = self._tree_1.child ('a')
        child_2 = self._tree_1.path ('a.b.c')

        self.assertEqual (child_1.value, 1)
        self.assertEqual (child_2.value, 2)
        self.assertEqual (child_2.get_path_name (), '.a.b.c')

        child_1.rename ('d')
        self.assertEqual (child_2.get_path_name (), '.d.b.c')
    
    def test_adopt (self):
        child = self._tree_1.path ('a.b')
        self._tree_1.child ('d').adopt (child, 'b')

        self.assertEqual (self._tree_1.path ('a.b.c').value, None)
        self.assertEqual (self._tree_1.path ('d.b.c').value, 2)

    def test_events (self):
        tree = TestAutoTree.CountingTree ();

        tree.child ('a')
        self.assertEqual (tree.childs, 1)
        tree.child ('b')
        self.assertEqual (tree.childs, 2)
        tree.child ('a')
        self.assertEqual (tree.childs, 2)
        tree.remove ('a')
        self.assertEqual (tree.childs, 1)
        tree.remove ('b')
        self.assertEqual (tree.childs, 0)

    def test_crawling (self):
        list_pre  = []
        list_post = []
        
        def mk_appender (list):
            def appender (x):
                return list.append (x.get_name ())
            return appender
        
        self._tree_1.dfs_preorder (mk_appender (list_pre))
        self._tree_1.dfs_postorder (mk_appender (list_post))

        self.assertEqual (list_pre, ["", "a", "b", "c"])
        self.assertEqual (list_post, ["c", "b", "a", ""])
    
        
 
