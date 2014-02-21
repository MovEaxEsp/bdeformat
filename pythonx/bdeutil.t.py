#!/usr/bin/env python

import unittest
import bdeutil

class TestDriver(unittest.TestCase):

    def test_findNextOccurrence(self):

        f = bdeutil.findNextOccurrence
        A = self.assertEqual

        A(f("abcd", 0, "b",  1), 1)
        A(f("abcd", 0, "bc", 1), 1)
        A(f("abcd", 0, "bc", -1), -1)
        A(f("abcd", 1, "bc", -1), 1)
        A(f("abcd", 2, "bc", 1), 2)
        A(f("abcd", 2, "bc", -1), 2)
        A(f("abcd", 3, "bc", -1), 2)
        A(f("abcd", 0, "a", 1), 0)
        A(f("abcd", 0, "a", -1), 0)
        A(f("abcd", 3, "d", 1), 3)
        A(f("abcd", 3, "d", -1), 3)

    def test_findSkippingGroups(self):
        f = bdeutil.findSkippingGroups
        A = self.assertEqual

        A(f("a(abc)b", 0, "b", 1), 6)
        A(f("a(abc)b", 1, "b", 1), 6)
        A(f("a(abc)b", 2, "b", 1), 3)

        A(f("(a)(a)a", 0, "a", 1), 6)

    def test_findOpenClose(self):
        f = bdeutil.findOpenClose
        A = self.assertEqual

        A(f("foo(i a, i b) s", 0), None)
        A(f("foo(i a, i b) s", 3), None)
        A(f("foo(i a, i b) s", 4), (3, 12))
        A(f("foo(i a, i b) s", 5), (3, 12))
        A(f("foo(i a, i b) s", 11), (3, 12))
        A(f("foo(i a, i b) s", 12), None)

    def test_determineElements(self):
        f = lambda x: bdeutil.determineElements(x, (0, len(x) - 1))
        g = lambda x, b, e: bdeutil.determineElements(x, (b, len(x) - 1 - e))
        A = self.assertEqual

        A(f("(int a, int b)"), ["int a,", "int b)"])
        A(f("(int a)"), ["int a)"])
        A(f("[int a, int (*f)(), int<void> x]"),
            ["int a,", "int (*f)(),", "int<void> x]"])
        A(g("""(int a, // some arg\n
                void *c, // another arg\n
                something& else);""", 0, 1),
          ["int a, // some arg",
           "void *c, // another arg",
           "something& else)"])

    def test_parseElement(self):
        f = bdeutil.parseElement
        A = self.assertEqual

        A(f("int a;"), ("int", "a", "", ";", ""))
        A(f(" const int a;"), ("const int", "a", "", ";", ""))
        A(f("(int *)c,"), ("", "(int *)c", "", ",", ""))
        A(f('int f = "123";'), ("int", "f", '= "123"', ";", ""))
        A(f("int **c = 0; // something"),
           ("int", "**c", "= 0", ";", "something"))
        A(f("int& c)"), ("int&", "c", "", ")", ""))
        A(f("int *& d}"), ("int *&", "d", "", "}",""))

    def test_alignElementParts(self):
        # 'f' takes a list of strings, replaces '|' with some spaces in
        # each, calls 'parseElement' on each to build a list suitable for
        # 'alignElementParts', and then joins each element of the returned
        # list back with "|"
        f = lambda x: ["|".join(a) for a in
                        bdeutil.alignElementParts(
                                         [bdeutil.parseElement(
                                           e.replace("|", "   ")) for e in x])]
        A = self.assertEqual

        l = ["int         | a||,|",
             "char        | b||,|",
             "void        |*c||,|",
             "another type| x|= 2|,|"]
        A(f(l), l)

        l = ["int         |   abc|= 123|,|",
             "char        |   b  |= 2345|,|",
             "void        |***c||,|",
             "void ***&   |***c||,|",
             "another type|   x  |= 2|,|"]
        A(f(l), l)

    def test_writeAlignedElements(self):
        f = lambda x: bdeutil.writeAlignedElements(
                        bdeutil.alignElementParts(
                                         [bdeutil.parseElement(e) for e in x]))
        A = self.assertEqual

        l = ["int            a;",
             "char           character = 0;",
             "unsigned char  x         = 'c';",
             "void          *d;"]
        A(f(l), ([(x, "") for x in l], 15))

        l = ["a,",
             "bcd,",
             "**eg,",
             "&h)"]
        A(f(l), ([(x, "") for x in l], 0))

    def test_tryWriteBdeGroupOneLine(self):
        f =  lambda x, w: bdeutil.tryWriteBdeGroupOneLine(
                                       [bdeutil.parseElement(e) for e in x], w)
        A = self.assertEqual

        l = ["int     a,", "char    *b,", "some other type x)"]
        s = "int a, char *b, some other type x)"

        A(f(l, len(s) + 1), s)
        A(f(l, len(s)), s)
        A(f(l, len(s) - 1), None)

    def test_writeBdeGroupMultiline(self):
        f =  lambda x, w, p, s: bdeutil.writeBdeGroupMultiline(
                                  [bdeutil.parseElement(e) for e in x], w, p,s)
        A = self.assertEqual

        l = ["int a,",
             "char character = 0,",
             "unsigned char  x         = 'c',",
             "void *d)"]
        out = ["foo(int            a,",
               "    char           character = 0,",
               "    unsigned char  x         = 'c',",
               "    void          *d);"]
        A(f(l, 80, "foo(", ";"), ([(x, "") for x in out], 19))

        out = ["foobarbazzzzzz(",
               "         int            a,",
               "         char           character = 0,",
               "         unsigned char  x         = 'c',",
               "         void          *d);"]
        A(f(l, 40, "foobarbazzzzzz(", ";"), ([(x, "") for x in out], 24))

    def test_splitCommentIntoLines(self):
        f = bdeutil.splitCommentIntoLines
        A = self.assertEqual

        s = "some decently long string for a test"
        A(f(s, 4), [
            "some",
            "decently",
            "long",
            "string",
            "for",
            "a",
            "test"])

        A(f(s, 5), [
            "some",
            "decently",
            "long",
            "string",
            "for a",
            "test"])

        A(f(s, 10), [
            "some",
            "decently",
            "long",
            "string for",
            "a test"])

    def test_writeComments(self):
        f = bdeutil.writeComments
        A = self.assertEqual

        linesAndComments = [
            ("int         d_foo;", "a simple variable"),
            ("const char *d_name;", "a longer var with a long comment"),
            ("double      d_noComment;", ""),
            ("void       *d_void;", "last line")]

        A(f(linesAndComments, 40, 65, 79, True), [
            "int         d_foo;       // a simple variable",
            "const char *d_name;      // a longer var with a long comment",
            "double      d_noComment;",
            "void       *d_void;      // last line"])

        A(f(linesAndComments, 20, 50, 60, False), [
            "int         d_foo;       // a simple variable",
            "const char *d_name;      // a longer var with a long",
            "                         // comment",
            "double      d_noComment;",
            "void       *d_void;      // last line"])

        A(f(linesAndComments, 20, 50, 60, True), [
            "int         d_foo;       // a simple variable",
            "",
            "const char *d_name;      // a longer var with a long",
            "                         // comment",
            "",
            "double      d_noComment;",
            "",
            "void       *d_void;      // last line",
            ""])

    def no_test_fixBdeBlock(self):
        f = bdeutil.fixBdeBlock
        A = self.assertEqual

        A(f("int foo(int bar, void *baz, bslma::Allocator *alloc = 0) = 0;",
            20, 41, 0),
            ["int foo(int               bar,",
             "        void             *baz,",
             "        bslma::Allocator *alloc = 0) = 0;"])

        A(f("int foo(int bar, void *baz, bslma::Allocator *alloc = 0) = 0;",
            20, 40, 0),
            ["int foo(",
             "       int               bar,",
             "       void             *baz,",
             "       bslma::Allocator *alloc = 0) = 0;"])

        # TODO fix.  Should handle spaces between * and name correctly
        A(f("int foo(int bar, void *  baz, bslma::Allocator *alloc = 0) = 0;",
            20, 40, 0),
            ["int foo(",
             "       int               bar,",
             "       void             *baz,",
             "       bslma::Allocator *alloc = 0) = 0;"])

        # TODO fix.  Shouldn't align the '=' if there is only one
        A(f("int foo(int bar, void *bazxx, bslma::Allocator *a = 0) = 0;",
            20, 40, 0),
            ["int foo(",
             "       int               bar,",
             "       void             *bazxx,",
             "       bslma::Allocator *a = 0) = 0;"])

        # TODO fix.  Should handle definitions without names
        A(f("bdef_Function<void (*)(int, char, void *, bslma::Allocator *)> "
                                                                  "Something;",
            20, 80, 0),
            ["bdef_Function<void (*)(int,",
             "                       char,",
             "                       void *,",
             "                       bslma::Allocator *)> Something;"]);

        # TODO test this with a func that uses -> in an arg, and the search
        # that starts after the >

# Test functions in 'bdeutil
if __name__ == "__main__":
    unittest.main();
