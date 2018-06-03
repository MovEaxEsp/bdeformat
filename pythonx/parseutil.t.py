#!/usr/bin/env python

import unittest
import parseutil
from sectiontype import SectionType

class TestDriver(unittest.TestCase):

    def test_findNextOccurrence(self):
        f = lambda s, c, d: parseutil.findNextOccurrence(s.replace("@", ""),
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
        f = lambda s, c, d: parseutil.findSkippingGroups(s.replace("@", ""),
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

            self.assertEqual(parseutil.findOpenClose(
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

    def test_findComment(self):
        def T(s):
            start = s.find("#")
            end = s.find("#", start + 1) - 2
            trans = s.translate(None, "#@")
            ret = parseutil.findComment(trans, start, end)

            expected = s.find("@") - 1
            if expected == -2:
                expected = -1

            if expected == -1:
                self.assertEqual(expected, ret)
            elif ret != expected:
                print "BAD RETURN:"
                print trans[start:ret]
                print "EXPECTED:"
                print trans[start:expected]
                self.assertEqual(ret, expected)

        T("""
            int a;#
                // a long, multiline, comment
                // sjhdf, sdfhj
@
            int b;# // next"
          """)

    def test_determineElements(self):
        def T(s):
            noPipe = s.replace("|", "")
            openPos = noPipe.find("#")
            if openPos == -1:
                openClose = (-1, len(noPipe))
            else:
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

            self.assertEqual(parseutil.determineElements(rawS, openClose),
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
        T("""
            |int d_a; // a, comment,
                      // with, commas|

            |double d_b; // another, comment,
                         // with, commas|""")

        T("""
            |int              d_a; // my (member)|
            |const char      *d_b_p; // my other member|
            |unsigned int *&  d_c; // yet another member|
          """)

        T("""
   |dmpu::SmallBlobBufferAllocator  d_smallBlobBufferAllocator;
                            // used to allocate small, known sized
                            // buffers needed when splitting messages|
          """)
        T("""
|dmpu::SmallBlobBufferAllocator d_smallBlobBufferAllocator;
                                 // used to allocate small, known sized
                                 // buffers needed when splitting messages|
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

            self.assertEqual(parseutil.parseElement(s.translate(None, "|")),
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
        T("|int|| a||| // comment, commas|")
        T("|||bsl::vector<int>||||")
        T("|||*&var||,||")
        T("|||(const char*)&recapMsg||,||")

    def test_parseMembers(self):
        def T(s, res):
            expected = res.split(",")
            parsed = parseutil.parseMembers(s)

            self.assertEqual(parsed, expected)

        T("int d_abc;", "d_abc")
        T("""int d_a;
             int d_b;
          """, "d_a,d_b")
        T("""const Type *& d_a;
             int           d_b;
             double       &d_c; // some comment
                                // that spans lines
             volatile A*   d_d;
          """, "d_a,d_b,d_c,d_d")

    def test_parseFuncDeclaration(self):
        def T(s, expected):
            ret = parseutil.parseFuncDeclaration(s)
            self.assertEqual(ret, expected)

        T("void foo(int a);", ("void", "foo", "(int a)", ";"))
        T("const char *getStr() const;",
          ("const char *", "getStr", "()", "const;"))
        T("int& get_int(int arg) = 0;",
          ("int&", "get_int", "(int arg)", "= 0;"))

    def test_parseFuncDeclarations(self):
        def T(s, expected):
            ret = parseutil.parseFuncDeclarations(s)
            self.assertEqual(ret, expected)

        T("""
          int foo();
            // Some comments

          bool& bar(int arg) const; // some other comments


          // Some comments above mayb
          int<abc>foo[]garbage; // and on the side
          // and uner

          bsl::shared_ptr<int&> *baz(int abc, char def) = 0;
            // Some more comments
          """,
          [
              ("int", "foo", "()", ";"),
              ("bool&", "bar", "(int arg)", "const;"),
              "int<abc>foo[]garbage;",
              ("bsl::shared_ptr<int&> *", "baz", "(int abc, char def)", "= 0;")
          ])


    def test_findClassName(self):
        def T(s, expected):
            def gen():
                for line in s.split("\n"):
                    yield line

            res = parseutil.findClassName(gen())
            self.assertEqual(res, expected)

        T("""
            a
            b
             // class foo
           """, "foo")
        T("""
            // -----------
            // struct MySecondClass
            // struct MyThirdClass
          """, "MySecondClass")
        T("""
            a
            b
            c
          """, None)

    def test_extractClassSection(self):
        def T(s, className, section, expected):
            def gen():
                for line in s.split("\n"):
                    yield line

            res = parseutil.extractClassSection(gen(), className, section)
            self.assertEqual(res, None if expected == None else expected[1:])

        T("""
          a
          b
           // class Foo
           // DATA
           int a;
           int b; // comment
           };
          """, "Foo", SectionType.DATA,
          """
           int a;
           int b; // comment""")
        T("""
           // class A
           // DATA
           int a;

           // struct B

           // PUBLIC DATA
           int b;
           abcd
           random garbage

           public:
           """, "B", SectionType.DATA,
           """
           int b;
           abcd
           random garbage
""")
        T("""
          // class Bar

          // ACCESSORS
          int foo(); // something
          void bar(); // something
                      // something

          // DATA
          int d_a;
          """,
          "Bar", SectionType.ACCESSORS,
          """
          int foo(); // something
          void bar(); // something
                      // something
""")
        T("""
          // class Foo

          // DATA
          int d_a
          """,
          "Foo", SectionType.ACCESSORS,
          None)

# Test functions in 'bdeformatutil'
if __name__ == "__main__":
    unittest.main();
