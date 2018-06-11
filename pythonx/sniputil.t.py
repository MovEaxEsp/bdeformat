#!/usr/bin/env python

import unittest
import sniputil

def printStrDiff(a, b):
    aLen = len(a)
    bLen = len(b)

    diffPos = -1
    for i in range(0, min(aLen, bLen)):
        if a[i] != b[i]:
            diffPos = i
            break

    if diffPos == -1:
        if aLen != bLen:
            diffPos = min(aLen, bLen)
            print("A: " +  a[:diffPos] + "[[[" + a[diffPos:])
            print("B: " +  b[:diffPos] + "[[[" + b[diffPos:])

        return

    preChars = min(20, diffPos)
    print("A: " +  a[:diffPos] + "[[[" + a[diffPos] + "]]]" + a[diffPos+1:])
    print("B: " +  b[:diffPos] + "[[[" + b[diffPos] + "]]]" + b[diffPos+1:])

class TestDriver(unittest.TestCase):

    def test_snipOptional(self):
        F = sniputil.snipOptional

        self.assertEqual(
            F(1, "abc"),
            "`!p snip.rv = \"\"\"abc\"\"\" if len(t[1]) > 0 else ''`")

        self.assertEqual(
            F(2, "'\"'", True),
            "`!p snip.rv = \"\"\"'\"'\"\"\" if len(t[2]) > 0 else ''`")

        self.assertEqual(
            F(20, "abc", False),
            "`!p snip.rv = \"\"\"abc\"\"\" if len(t[20]) == 0 else ''`")

    def test_genTabStopPrePost(self):
        F = sniputil.genTabStopPrePost
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))

        A(F("", 1, "", ""),
          "$1")

        A(F("", 2, "abc", ""),
          "${2:abc}")

        A(F("preA", 3, "def", ""),
          "%s${3:def}" % sniputil.snipOptional(3, "preA"))

        A(F("preB", 4, "ghi", "postA"),
          "%s${4:ghi}%s" % (sniputil.snipOptional(4, "preB"),
                            sniputil.snipOptional(4, "postA")))

    def test_genCctorSnippet(self):
        F = sniputil.genCctorSnippet
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))
        def T(className, members, expected):
            A(F(className, members), expected[1:-1])

        T("Foo",
           """
           int a;
           void *b_p;
           """,
           """
${1:Foo}::$1(const $1& other%s)
: a(other.a%s)
, b_p(other.b_p%s)
{
}
""" % (sniputil.genTabStopPrePost(
                          ", bslma::Allocator *", 2, "basicAllocator", " = 0"),
       sniputil.genTabStopPrePost(", ", 3, "$2", ""),
       sniputil.genTabStopPrePost(", ", 4, "$2", "")))

        T("Foo",
          "",
          """
${1:Foo}::$1(const $1& other%s)
{
}
""" % (sniputil.genTabStopPrePost(
                         ", bslma::Allocator *", 2, "basicAllocator", " = 0")))

        T("",
          "",
          """
$1::$1(const $1& other%s)
{
}
""" % (sniputil.genTabStopPrePost(
                         ", bslma::Allocator *", 2, "basicAllocator", " = 0")))

    def test_genCtorMemSnippet(self):
        F = sniputil.genCtorMemSnippet
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))
        def T(members, separator, expected):
            A(F(members, separator), expected[1:-1])

        T("""
        int d_a;
        void *d_b_p;
        const char *d_c_p;
        bool& d_d;
        """,
        ": ",
        """
: d_a($1)
, d_b_p($2)
, d_c_p($3)
, d_d($4)
""")

    def test_genDefSnippet(self):
        F = sniputil.genDefSnippet
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))
        def T(className, decls, inHeader, expected):
            A(F(className, decls, inHeader), expected[1:-1])

        T("APrettyLongClassNameReallyReallyLong",
          """
    void *getMem1();
        // Some function

    int& someOtherFunc(int a, char *foo, const bslma::ManagedPtr<void>& b);
        // A really fancy function
          """,
          False,
          """
void *APrettyLongClassNameReallyReallyLong::getMem1()
{
    $1
}

int& APrettyLongClassNameReallyReallyLong::someOtherFunc(
                                           int                             a,
                                           char                           *foo,
                                           const bslma::ManagedPtr<void>&  b)
{
    $2
}

""")

        T("APrettyLongClassNameReallyReallyLong",
          """
    void *getMem1();
        // Some function

    int& someOtherFunc(int a, char *foo, const bslma::ManagedPtr<void>& b);
        // A really fancy function
          """,
          True,
          """
inline
void *APrettyLongClassNameReallyReallyLong::getMem1()
{
    $1
}

inline
int& APrettyLongClassNameReallyReallyLong::someOtherFunc(
                                           int                             a,
                                           char                           *foo,
                                           const bslma::ManagedPtr<void>&  b)
{
    $2
}

""")

    def test_genAccessorDeclSnippet(self):
        F = sniputil.genAccessorDeclSnippet
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))
        SO = sniputil.snipOptional
        def T(typeName, cleanName, snipNum, expected):
            A(F(typeName, cleanName, snipNum), expected[1:-1])

        T("void *", "myVar", 2,
          """
    %svoid *${2:&}%smyVar() const;
%s%s
""" % (SO(2, "const "),
       SO(2, " "),
       SO(2, """
        // Return a reference providing const access to the 'myVar' property of
        // this object."""[1:]),
       SO(2, """
        // Return the 'myVar' property of this object."""[1:],
         False)
      ))

        T("ClassType", "myVar", 2,
          """
    %sClassType${2:&} myVar() const;
%s%s
""" % (SO(2, "const "),
       SO(2, """
        // Return a reference providing const access to the 'myVar' property of
        // this object."""[1:]),
       SO(2, """
        // Return the 'myVar' property of this object."""[1:],
         False)
      ))

    def test_genManipulatorDeclSnippet(self):
        F = sniputil.genManipulatorDeclSnippet
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))
        SO = sniputil.snipOptional
        def T(typeName, cleanName, snipNum, expected):
            A(F(typeName, cleanName, snipNum), expected[1:-1])

        T("void *", "myVar", 2,
          """
    void *& myVar();
        // Return a reference providing modifiable access to the 'myVar'
        // property of this object.
""")

    def test_genSetterDeclSnippet(self):
        F = sniputil.genSetterDeclSnippet
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))
        SO = sniputil.snipOptional
        def T(typeName, cleanName, snipNum, expected):
            A(F(typeName, cleanName, snipNum), expected[1:-1])

        T("void *", "myVar", 2,
          """
    void setMyVar(%svoid *${2:&}%svalue);
        // Set the value of the 'myVar' property of this object to the
        // specified 'value'.
""" % (SO(2, "const "),
       SO(2, " ")))

        T("ClassType", "myVar", 2,
          """
    void setMyVar(%sClassType${2:&} value);
        // Set the value of the 'myVar' property of this object to the
        // specified 'value'.
""" % (SO(2, "const ")))

    def test_genDeclSnippet(self):
        F = sniputil.genDeclSnippet
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))
        SO = sniputil.snipOptional

        def funcSnipGen(typeName, cleanName, snipNum):
            return "(%s, %s, %s)" % (typeName, cleanName, snipNum)

        def T(memberDefs, expected):
            A(F(memberDefs, funcSnipGen), expected[1:-1])

        T("""
        int d_a;
        void *d_b_p;
        const char *d_c_p;
        bslma::ManagedPtr<void>& d_d;
        """,
        """
${1:(int, a, 2)

}${3:(void *, b, 4)

}${5:(const char *, c, 6)

}${7:(bslma::ManagedPtr<void>&, d, 8)

}
""")

if __name__ == "__main__":
    unittest.main();
