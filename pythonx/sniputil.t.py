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
        class Snip:
            def __init__(self):
                self.rv = "Def"

        def T(snipNum, text, expandWhenNotEmpty, ts, res):

            code = sniputil.snipOptional(snipNum, text, expandWhenNotEmpty)

            ctx = {"snip": Snip(), "t": ts}
            # Strip out the `!p and `
            exec code[4:-1] in ctx
            self.assertEqual(ctx["snip"].rv, res)

        T(1, "a", True, [0, "b"], "a")
        T(1, "a", True, [0, ""], "")
        T(1, "a", False, [0, "b"], "")
        T(1, "a", False, [0, ""], "a")
        T([1, 2], "a", True, [0, "a", "b"], "a")
        T([1, 2], "a", True, [0, "", "b"], "")
        T([1, 2], "a", True, [0, "a", ""], "")
        T([1, 2], "a", True, [0, "", ""], "")
        T([1, 2], "a", False, [0, "a", "b"], "")
        T([1, 2], "a", False, [0, "", "b"], "")
        T([1, 2], "a", False, [0, "a", ""], "")
        T([1, 2], "a", False, [0, "", ""], "a")

    def test_genTabStop(self):
        F = sniputil.genTabStop
        A = lambda a, b: self.assertEqual(a, b, printStrDiff(a, b))

        A(F(1, ""),
          "$1")

        A(F(2, "abc"),
          "${2:abc}")

        A(F(3, "def", pre="preA"),
          "%s${3:def}" % sniputil.snipOptional(3, "preA"))

        A(F(4, "ghi", pre="preB", post="postA"),
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
""" % (sniputil.genTabStop(
                 2, "basicAllocator", pre=", bslma::Allocator *", post=" = 0"),
       sniputil.genTabStop(3, "$2", pre=", "),
       sniputil.genTabStop(4, "$2", pre=", ")))

        T("Foo",
          "",
          """
${1:Foo}::$1(const $1& other%s)
{
}
""" % (sniputil.genTabStop(
                2, "basicAllocator", pre=", bslma::Allocator *", post=" = 0")))

        T("",
          "",
          """
$1::$1(const $1& other%s)
{
}
""" % (sniputil.genTabStop(
                2, "basicAllocator", pre=", bslma::Allocator *", post=" = 0")))

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
        SO = sniputil.snipOptional;
        GT = sniputil.genTabStop;
        def T(className, decls, inHeader, memberDefs, expStr, expNum):
            ret = F(className, decls, inHeader, memberDefs)
            A(ret[0], expStr[1:-1])
            self.assertEqual(ret[1], expNum)

        T("APrettyLongClassNameReallyReallyLong",
          """
    void *getMem1();
        // Some function

    int& someOtherFunc(int a, char *foo, const bslma::ManagedPtr<void>& b);
        // A really fancy function
          """,
          False,
          "",
          """
void *APrettyLongClassNameReallyReallyLong::getMem1()
{%s
}

int& APrettyLongClassNameReallyReallyLong::someOtherFunc(
                                           int                             a,
                                           char                           *foo,
                                           const bslma::ManagedPtr<void>&  b)
{%s
}

""" % (sniputil.genTabStop(1, "// TODO", "\n    "),
       sniputil.genTabStop(2, "// TODO", "\n    ")), 3)

        T("APrettyLongClassNameReallyReallyLong",
          """
    int& someOtherFunc(int a, char *foo, const bslma::ManagedPtr<void>& b);
        // A really fancy function
          """,
          True,
          "",
          """
inline
int& APrettyLongClassNameReallyReallyLong::someOtherFunc(
                                           int                             a,
                                           char                           *foo,
                                           const bslma::ManagedPtr<void>&  b)
{%s
}

""" % (sniputil.genTabStop(1, "// TODO", "\n    ")), 2)

        T("ClassName",
          """
          int someAccessor() const; // my accessor
          """,
          False,
          "",
          """
int ClassName::someAccessor() const
{%s
}

""" % GT(1, "// TODO", pre="\n    "), 2)

        T("ClassName",
          """
          static ClassName(int intArg, double doubleArg, void *voidArg,
                    int *intPtr = 0,
                    bslma::Allocator *basicAllocator = 0);
                // A constructor
          """,
          False,
          """
          double d_doubleArg;
          void *d_voidArg_p;
          void *d_oneMoreMem_p;
          bslma::Allocator *d_allocator_p;
          """,
          """
ClassName::ClassName(int               intArg,
                     double            doubleArg,
                     void             *voidArg,
                     int              *intPtr,
                     bslma::Allocator *basicAllocator)
: d_doubleArg(%s)
, d_voidArg_p(%s)
, d_oneMoreMem_p(%s)
, d_allocator_p(%s)
{%s
}

""" % (GT(1, "doubleArg") + SO([1,2], ", ") + GT(2, "basicAllocator"),
       GT(3, "voidArg") + SO([3,4], ", ") + GT(4, "basicAllocator"),
       GT(5) + SO([5, 6], ", ") + GT(6, "basicAllocator"),
       GT(7, "bslma::Default::allocator(basicAllocator)"),
       GT(8, "// TODO", pre="\n    ")), 9)

        T("ClassName",
          """
          explicit virtual ClassName(const ClassName& orig,
          bslma::Allocator *basicAllocator = 0);
                // A constructor
          """,
          True,
          """
          double d_doubleArg;
          void *d_voidArg_p;
          void *d_oneMoreMem_p;
          bslma::Allocator *d_allocator_p;
          """,
          """
inline
ClassName::ClassName(const ClassName& orig, bslma::Allocator *basicAllocator)
: d_doubleArg(%s)
, d_voidArg_p(%s)
, d_oneMoreMem_p(%s)
, d_allocator_p(%s)
{%s
}

""" % (GT(1, "orig.d_doubleArg") + SO([1,2], ", ") + GT(2, "basicAllocator"),
       GT(3, "orig.d_voidArg_p") + SO([3,4], ", ") + GT(4, "basicAllocator"),
       GT(5, "orig.d_oneMoreMem_p") + SO([5,6], ", ")+GT(6, "basicAllocator"),
       GT(7, "bslma::Default::allocator(basicAllocator)"),
       GT(8, "// TODO", pre="\n    ")), 9)

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
