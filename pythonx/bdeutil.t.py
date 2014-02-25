#!/usr/bin/env python

import unittest
import bdeutil

class TestDriver(unittest.TestCase):

    def test_findNextOccurrence(self):
        f = lambda s, c, d: bdeutil.findNextOccurrence(s.replace("@", ""),
                                                       s.find("@"),
                                                       c,
                                                       d)
        A = self.assertEqual

        # Use '@' to indicate the position of the start of the search, and '#'
        # to indicate the end.  If '#' isn't in the test string, the search is
        # assumed to fail.
        T = lambda s, c, d: A(f(s.replace("#", ""), c, d),
                              s.replace("@", "").find("#"))


        T("@a#bcd", "b", 1)
        T("@a#bcd", "bc", 1)
        T("@abc", "bc", -1)
        T("a@#bcd", "bc", -1)
        T("ab@#cd", "bc", 1)
        T("ab@#cd", "bc", -1)
        T("ab#c@d", "bc", -1)
        T("@#abcd", "a", 1)
        T("@#abcd", "a", -1)
        T("abc@#d", "d", 1)
        T("abc@#d", "d", -1)

    def test_findSkippingGroups(self):
        f = lambda s, c, d: bdeutil.findSkippingGroups(s.replace("@", ""),
                                                       s.find("@"),
                                                       c,
                                                       d)
        A = self.assertEqual

        # Use '@' to indicate the position of the start of the search, and '#'
        # to indicate the end.  If '#' isn't in the test string, the search is
        # assumed to fail.
        T = lambda s, c, d: A(f(s.replace("#", ""), c, d),
                              s.replace("@", "").find("#"))

        T("@a(abc)#b", "b", 1)
        T("a@(abc)#b", "b", 1)
        T("a(@a#bc)b", "b", 1)
        T("@(a)(a)#a", "a", 1)
        T("#a->b@cd", "a", -1)
        T("@a<b->c>#c", "c", 1)

    def test_findOpenClose(self):
        # Use '@' to indicate the position of the start of the search, and '#'
        # to indicate the 'open' and 'close' positions.  If '#' aren't in the
        # test string, the search is assumed to fail.
        def T(s):
            noAt = s.replace("@", "")
            ret = (noAt.find("#"), noAt.find("#", noAt.find("#") + 1) - 1)
            if ret == (-1, -2):
                ret = None

            self.assertEqual(bdeutil.findOpenClose(
                                             s.translate(None, "@#"),
                                             s.translate(None, "#").find("@")),
                             ret)

        T("@foo(i a, i b) s")
        T("foo@(i a, i b) s")
        T("foo#(@i a, i b#) s")
        T("foo#(i@ a, i b#) s")
        T("foo#(i a, i @b#) s")
        T("foo(i a, i b@) s")

    def test_determineElements(self):
        def T(s):
            noPipe = s.replace("|", "")
            openPos = noPipe.find("#")
            openClose = (openPos, noPipe.find("#", openPos + 1) - 1)

            rawS = s.translate(None, "#|")
            ret = bdeutil.determineElements(rawS, openClose)
            expected = []

            noHash = s.translate(None, "#")

            pipe1Pos = noHash.find("|")
            pipe2Pos = noHash.find("|", pipe1Pos + 1)
            while pipe1Pos != -1 and pipe2Pos != -1:
                expected.append(noHash[pipe1Pos + 1:pipe2Pos])
                pipe1Pos = noHash.find("|", pipe2Pos + 1)
                pipe2Pos = noHash.find("|", pipe1Pos + 1)

            self.assertEqual(bdeutil.determineElements(rawS, openClose),
                             expected)

        T("#(|int a,| |int b#)|")
        T("#(|int a#)|")
        T("#[|int a,| |int (*f)(),| |int<void> x#]|"),
        T("""#(|int a, // some arg|
               |void *c, // another arg|
               |something& else#)|;""")

    def test_parseElement(self):
        f = bdeutil.parseElement
        A = self.assertEqual

        def T(s):
            expected = []
            prevPipePos = s.find("|")
            pipePos = s.find("|", prevPipePos + 1)
            while prevPipePos != -1 and pipePos != -1:
                expected.append(s[prevPipePos + 1:pipePos].strip(" /"))
                prevPipePos = pipePos
                pipePos = s.find("|", pipePos + 1)

            self.assertEqual(bdeutil.parseElement(s.translate(None, "|")),
                                                  tuple(expected))

        T("|int|| a||;||")
        T("  |const int|| a||;||")
        T("|||(int *)c||;||")
        T('|int|| f| = "123"|;||')
        T("|int| **|c| = 0|;| // something|")
        T("|int&|| c||)||")
        T("|int *&|| d||}||")
        T("|int| *|   e||;||")
        T("|||&a||,||")

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

        l = ["int         | |a||,|",
             "char        | |b||,|",
             "void        |*|c||,|",
             "another type| |x|= 2|,|"]
        A(f(l), l)

        l = ["int         |   |abc|= 123|,|",
             "char        |   |b  |= 2345|,|",
             "void        |***|c||,|",
             "void ***&   |***|c||,|",
             "another type|   |x  |= 2|,|"]
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

    def test_fixBdeBlock(self):
        f = bdeutil.fixBdeBlock
        A = self.assertEqual

        # Special characters
        # '@' - position to start search.  If multiple are present, the
        #       function is called multiple times, once for each '@'
        # 'W' - width marker.  The position of this specifies the 'width' arg
        #       to the function.  If this isn't present, '79' is assumed.
        # 'C' - the distance from this to 'W' specifies the comment width.  If
        #       this isn't present, '40' is assumed
        def T(inS, outS, width=79, commentWidth=40):
            wPos = inS.find("W")
            if wPos != -1:
                width = wPos

            cPos = inS.find("C")
            if cPos != -1:
                commentWidth = width - cPos

            inS = inS.translate(None, "CW")

            expected = outS.split("\n")

            numAt = 0
            atPos = inS.find("@")
            self.assertNotEqual(atPos, -1)
            while atPos != -1:
                ret = bdeutil.fixBdeBlock(inS.translate(None, "@"),
                                          atPos - numAt,
                                          width,
                                          commentWidth)

                atPos = inS.find("@", atPos + 1)
                numAt += 1

                self.assertEqual(ret, expected)

        T("""
            int foo(@int bar,@ void *baz, bslma::AllocatorW *alloc = @0) = 0;
          ""","""
            int foo(int               bar,
                    void             *baz,
                    bslma::Allocator *alloc = 0) = 0;
          """)

        T("""
            Subscription newSubscription(requ@est->sub@scriptionId(),
                                 request->subscrib@er().ptr());
          ""","""
            Subscription newSubscription(request->subscriptionId(),
                                         request->subscriber().ptr());
          """)

        T("""
            int foo(int bar, void *@baz, bslma::AllWocator *alloc = 0) = 0;
          ""","""
            int foo(
                   int               bar,
                   void             *baz,
                   bslma::Allocator *alloc = 0) = 0;
          """)

        T("""
            int foo(int   bar, void *   @baz, bslmaW::Allocator
            *alloc = 0) = 0;
          ""","""
            int foo(
                   int               bar,
                   void             *baz,
                   bslma::Allocator *alloc = 0) = 0;
          """)

        T("""
            int foo(int bar,@ void *bazxx, bslmaW::Allocator *a = 0) = 0;
          ""","""
            int foo(int               bar,
                    void             *bazxx,
                    bslma::Allocator *a = 0) = 0;
          """)

        # TODO test
    #bdema_ManagedPtr<dmpit::PublisherRequest> req(
                                          #new (*alloc) PublisherRequest(alloc),
                                          #alloc);

    # TODO test
                #ret = bdeutil.fixBdeBlock(     in.translate(None, "@"),
                                          #atPos - numAt,
                                                  #width,
                                                  #commentWidth)

# Test functions in 'bdeutil
if __name__ == "__main__":
    unittest.main();
