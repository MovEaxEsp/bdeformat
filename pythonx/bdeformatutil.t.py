#!/usr/bin/env python

import unittest
import bdeformatutil

class TestDriver(unittest.TestCase):

    def test_findNextOccurrence(self):
        f = lambda s, c, d: bdeformatutil.findNextOccurrence(
                                                            s.replace("@", ""),
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
        f = lambda s, c, d: bdeformatutil.findSkippingGroups(
                                                            s.replace("@", ""),
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
            expected = (noAt.find("#"), noAt.find("#", noAt.find("#") + 1) - 1)
            if expected == (-1, -2):
                expected = None

            self.assertEqual(bdeformatutil.findOpenClose(
                                             s.translate(None, "@#"),
                                             s.translate(None, "#").find("@")),
                             expected)

        T("@foo(i a, i b) s")
        T("foo@(i a, i b) s")
        T("foo#(@i a, i b#) s")
        T("foo#(i@ a, i b#) s")
        T("foo#(i a, i @b#) s")
        T("foo(i a, i b@) s")
        T("#(foo@(i a) something#)")
        T("#(foo(i a@)#)")

    def test_determineElements(self):
        def T(s):
            noPipe = s.replace("|", "")
            openPos = noPipe.find("#")
            openClose = (openPos, noPipe.find("#", openPos + 1) - 1)

            rawS = s.translate(None, "#|")
            expected = []

            noHash = s.translate(None, "#")

            pipe1Pos = noHash.find("|")
            pipe2Pos = noHash.find("|", pipe1Pos + 1)
            while pipe1Pos != -1 and pipe2Pos != -1:
                expected.append(noHash[pipe1Pos + 1:pipe2Pos])
                pipe1Pos = noHash.find("|", pipe2Pos + 1)
                pipe2Pos = noHash.find("|", pipe1Pos + 1)

            self.assertEqual(bdeformatutil.determineElements(rawS, openClose),
                             expected)

        T("#(|int a,| |int b#)|")
        T("#(|int a#)|")
        T("#[|int a,| |int (*f)(),| |int<void> x#]|"),
        T("""#(|int a, // some arg|
               |void *c, // another arg|
               |something& else#)|;""")
        T("""#
            |int d_a; // something|
            |double d_b; // something else|
            |char *d_c; // last thing|#
          """)

        T("""#
            |int d_a; // something \n // with multi line comment|
            |double d_b; // something with a short comment|
            |char *d_c; // last thing \n // with multi line comment|#
          """)
        T("""#
            |int d_a; // a, comment,
                      // with, commas|

            |double d_b; // another, comment,
                         // with, commas|#""")

        T("""#
            |int              d_a; // my (member)|
            |const char      *d_b_p; // my other member|
            |unsigned int *&  d_c; // yet another member|#
          """)

    def test_parseElement(self):
        def T(s, commentStr=""):
            expected = []
            prevPipePos = s.find("|")
            pipePos = s.find("|", prevPipePos + 1)
            while prevPipePos != -1 and pipePos != -1:
                expected.append(s[prevPipePos + 1:pipePos].strip(" /"))
                prevPipePos = pipePos
                pipePos = s.find("|", pipePos + 1)

            if len(commentStr) > 0:
                expected[5] = commentStr

            self.assertEqual(bdeformatutil.parseElement(
                                                       s.translate(None, "|")),
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
        T("|int|| a||;| // multi line\n // comment|", "multi line comment")
        T("|int|| d_a||;| // my (member)|")
        T("|int|| a||;| // a, cmt, \n with, commas|", "a, cmt, with, commas")

    def test_alignElementParts(self):
        # 'f' takes a list of strings, replaces '|' with some spaces in
        # each, calls 'parseElement' on each to build a list suitable for
        # 'alignElementParts', and then joins each element of the returned
        # list back with "|"
        f = lambda x: ["|".join(a) for a in
                        bdeformatutil.alignElementParts(
                                         [bdeformatutil.parseElement(
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
        f = lambda x: bdeformatutil.writeAlignedElements(
                        bdeformatutil.alignElementParts(
                                   [bdeformatutil.parseElement(e) for e in x]))
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
        f =  lambda x, w: bdeformatutil.tryWriteBdeGroupOneLine(
                                 [bdeformatutil.parseElement(e) for e in x], w)
        A = self.assertEqual

        l = ["int     a,", "char    *b,", "some other type x)"]
        s = "int a, char *b, some other type x)"

        A(f(l, len(s) + 1), s)
        A(f(l, len(s)), s)
        A(f(l, len(s) - 1), None)

    def test_writeBdeGroupMultiline(self):
        f =  lambda x, w, p, s: bdeformatutil.writeBdeGroupMultiline(
                            [bdeformatutil.parseElement(e) for e in x], w, p,s)
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
        f = bdeformatutil.splitCommentIntoLines
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
        # Special characters
        # 'W' - position indicates max line width
        # 'M' - distance from W specifies the minCommentWidth
        # 'X' - distance from W specifies the max comment width
        # These should appear on the first line of the input only
        def T(inS, outS, spaceIfMultiline = True):
            lines = filter(lambda s: len(s.strip()), inS.split("\n"))
            lineWidth = lines[0].find("W")
            self.assertTrue(lineWidth != -1)
            minCommentWidth = lineWidth - lines[0].find("M")
            maxWidth = lineWidth - lines[0].find("X")
            lines[0] = lines[0].translate(None, "WMX").rstrip()
            linesAndComments = [tuple(line.split("|")) for line in lines]

            expected = outS.split("\n")[1:-1]
            ret = bdeformatutil.writeComments(linesAndComments,
                                              minCommentWidth,
                                              maxWidth,
                                              lineWidth,
                                              spaceIfMultiline)

            if (ret != expected):
                print "BAD RETURN:"
                print "\n".join(ret)

            self.assertEqual(ret, expected)

        T("""
    int         d_Xfoo;|a simple Mvariable                            W
    const char *d_name;|a longer var with a long comment
    double      d_noComment;|
    void       *d_void;|last line
          """, """
    int         d_foo;        // a simple variable
    const char *d_name;       // a longer var with a long comment
    double      d_noComment;
    void       *d_void;       // last line
          """)

        T("""
    int         d_Xfoo;|a simple Mvariable             W
    const char *d_name;|a longer var with a long comment
    double      d_noComment;|
    void       *d_void;|last line
          """, """
    int         d_foo;        // a simple variable

    const char *d_name;       // a longer var with a
                              // long comment

    double      d_noComment;

    void       *d_void;       // last line
          """)

        T("""
    int         d_Xfoo;|a simple Mvariable             W
    const char *d_name;|a longer var with a long comment
    double      d_noComment;|
    void       *d_void;|last line
          """, """
    int         d_foo;        // a simple variable
    const char *d_name;       // a longer var with a
                              // long comment
    double      d_noComment;
    void       *d_void;       // last line
          """, False)

        T("""
    int         d_Xa;|                  W
    const char *d_m;|
    void       *d_v;|
          """, """
    int         d_a;
    const char *d_m;
    void       *d_v;
          """)

        T("""
    int foo(int               a,|arg 1                     W
            char             *c,|next arg
            bslma::Allocator *basicAllocator,|allocator
            void             *last = 0)|
          """, """
    int foo(int               a,               // arg 1
            char             *c,               // next arg
            bslma::Allocator *basicAllocator,  // allocator
            void             *last = 0)
          """, False)



    def test_fixBdeBlock(self):
        # Special characters
        # '@' - position to start search.  If multiple are present, the
        #       function is called multiple times, once for each '@'
        # 'W' - width marker.  The position of this specifies the 'width' arg
        #       to the function.  If this isn't present, '79' is assumed.
        # 'C' - the distance from this to 'W' specifies the comment width.  If
        #       this isn't present, '40' is assumed
        def T(inS, outS = None, width=79, commentWidth=40):
            inS = "\n".join(inS.split("\n")[1:-1])

            if outS == None:
                outS = inS.translate(None, "@WC")
                outS = "\n".join(map(lambda s: s.rstrip(), outS.split("\n")))
            else:
                outS = "\n".join(outS.split("\n")[1:-1])

            wPos = inS.find("W") + 1
            if wPos != 0:
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
                ret = bdeformatutil.fixBdeBlock(inS.translate(None, "@"),
                                                atPos - numAt,
                                                width,
                                                commentWidth)

                atPos = inS.find("@", atPos + 1)
                numAt += 1

                if ret != expected:
                    print "BAD RETURN:"
                    print "\n".join(ret)
                    print "EXPECTED:"
                    print "\n".join(expected)

                self.assertEqual(ret, expected)

        T("""
            int foo(@int bar,@ void *baz, bslma::AllocatorW *alloc = @0) = 0;
          ""","""
            int foo(int               bar,
                    void             *baz,
                    bslma::Allocator *alloc = 0) = 0;
          """)

        T("""
            Subscription newSubscription(requ@est->sub@scriptionId@(@),
                                 request->subscrib@er().ptr@(@));
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

        T("""
    bdema_ManagedPtr<dmpit::PublisherRequest> req(
                                          new (*alloc) PublisherRequest(alloc),
                                          @alloc);
          """);

        T("""
                ret = bdeformatutil.fixBdeBlock(in.@translate(None, 'o'),
                                                atPos - numAt,
                                                width,
                                                commentwidth)
          """)

        T("""
    int foo(int a, //arg 1@
            char *c, // next arg
            bslma::Allocator *basicAllocator, // allocator
            void *last = 0);
          """, """
    int foo(int               a,               // arg 1
            char             *c,               // next arg
            bslma::Allocator *basicAllocator,  // allocator
            void             *last = 0);
          """)

        T("""
    ITERMSubscriberManagerImp(
               bcema_BlobBufferFactory                    *@factory,
               ITERMPaintProxy                            *proxy,
               MessageEncoder                             *encoder,
               dmpu::ThreadUtil                           *threadUtil,
               dmpip::Statcollector                       *statcollector,
               dmpip::Statcollector2                      *statcollector2,
               dmpip::RequestTracer                       *requestTracer,
               int                                         heartbeatwarningSec,
               bool                                        checkInvalidLuws,
               const Mappingclearedcb&                     mappingclearedcb,
               bcema_SharedPtr<ITERMSubscriberManagerImp> *selfSP,
               bslma_Allocator                            *allocator = 0);
          """)

        T("""
    void jshjdjahdjasdjkhjfahsjkhafjweushjkhvcnxbdghfuiasysdjksbvjshfjhdf(
                                                                int         a@,
                                                                const char *c,
                                                                bool        b);
          """);

       # TODO fix
       #T("""
       #typedef bsl::unordered_map<bsls::Types::Int64,@
       #                           bsl::vector<bsls::Types::Int64> >
       #  """)

    def test_fixBdeData(self):
        # Special characters
        # 'W' - width marker.  The position of this specifies the 'width' arg
        #       to the function.  If this isn't present, '79' is assumed.
        # 'C' - the distance from this to 'W' specifies the comment width.  If
        #       this isn't present, '40' is assumed
        def T(inS, outS = None, width=79, commentWidth=40):
            inS = "\n".join(inS.split("\n")[1:-1])

            if outS == None:
                outS = inS.translate(None, "WC")
                outS = "\n".join(map(lambda s: s.rstrip(), outS.split("\n")))
            else:
                outS = "\n".join(outS.split("\n")[1:-1])

            wPos = inS.find("W") + 1
            if wPos != 0:
                width = wPos

            cPos = inS.find("C")
            if cPos != -1:
                commentWidth = width - cPos

            inS = inS.translate(None, "CW")

            expected = outS.split("\n")

            ret = bdeformatutil.fixBdeData(inS.translate(None, "@"),
                                           width,
                                           commentWidth)

            if ret != expected:
                print "BAD RETURN:"
                print "\n".join(ret)
                print "EXPECTED:"
                print "\n".join(expected)

            self.assertEqual(ret, expected)

        T("""
    int d_member1;
void *d_ptr_p;
          """, """
    int   d_member1;
    void *d_ptr_p;

          """)

        T("""
                                int              d_a;    // my member
                                const char      *d_b_p;  // my other member
                                unsigned int *&  d_c;    // yet another member

          """)

        T("""
                                int              d_a;    // my (member)
                                const char      *d_b_p;  // my other member
                                unsigned int *&  d_c;    // yet another member

          """)

        T("""
                                int              d_a;    // my member

                                const char      *d_b_p;  // my other member

                                unsigned int *&  d_c;    // yet another awesome
                                                         // member

          """)

        T("""
                                            int   d_longMemberName1;
                                                    // a comment

                                            char *d_longMemberName2;
                                                    // a longer comment

                                            void *d_longMemberName3;
                                                    // the loooooongest
                                                    // commentt

          """)

        T("""
                                            int   d_mem;     // a, comment,,
                                                             // commas

                                            char *d_member;  // another,
                                                             // comment, with,
                                                             // commas

          """)

# Test functions in 'bdeformatutil'
if __name__ == "__main__":
    unittest.main();
