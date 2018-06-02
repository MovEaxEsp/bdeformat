#!/usr/bin/env python

import unittest
import bdeformatutil

class TestDriver(unittest.TestCase):

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

        T("""
        typedef bsl::unordered_map<bsls::Types::Int64,@
                                   bsl::vector<bsls::Types::Int64> >
          """)

        T("""
        int ret = dmcu::BlobUtil::writeBytes(
                                     @result,
                                     dmcu::BlobPosition(0, sizeof(DMPMessage)),
                                     (const char*)&recapMsg,
                                     sizeof(RecapMessageV1));
          """)

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

        T("""
    dmpu::SmallBlobBufferAllocator d_smallBlobBufferAllocator;
                                     // used to allocate small, known sized
                                     // buffers needed when splitting messages

          """)

        T("""
    dmpip::Publisher2            **d_publisher_p;
                                     // the publisher to use wen sending
                                     // responses to subscribers

    dmpit::Types::SubscriptionId   d_subscriptionIdStart;
                                     // the first subscriptionId we should use

          """)

# Test functions in 'bdeformatutil'
if __name__ == "__main__":
    unittest.main();
