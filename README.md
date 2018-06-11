BDEFormat
=========

BDEFormat attempts to make writing BDE-style code easier by automating the
formatting of various constructs in C++ according to BDE style, as well as by
automatically generating correctly formatted code where possible.

Examples
--------
The easiest way of showing what BDEFormat can do is with a couple of examples.

With a single command, it can turn

```C++
    // DATA
    int d_a;  // some variable
    double d_c; // another member of the same class
    bslma::ManagedPtr<Foo> d_mp;  // some managedPtr to some stuff that we
    // don't much care about for this example
```

into

```C++
    // DATA
    int                    d_a;   // some variable

    double                 d_c;   // another member of the same class

    bslma::ManagedPtr<Foo> d_mp;  // some managedPtr to some stuff that we
                                  // don't much care about for this example
```

It can transform

```C++
void MyClass::RandomFunction(int anInt, double aDouble, void *aVoidStar,
                const Foo& aFooRef, IUnknown *unknown);
```

into

```C++
void MyClass::RandomFunction(int         anInt,
                             double      aDouble,
                             void       *aVoidStar,
                             const Foo&  aFooRef,
                             IUnknown   *unknown);
```

And transmogrify

```C++
                        d_myObj_p->someFunction(foo,   // a foo,
                                                        &bar,  // some bar ptr
                                                        7,     // a magic
                                                               // constant
                                                        "STRING");
```

into:

```C++
                        d_myObj_p->someFunction(foo,        // a foo,
                                                &bar,       // some bar ptr
                                                7,          // a magic constant
                                                "STRING");
```

But that's not all.  If you've got the
[UltiSnips](https://github.com/SirVer/ultisnips/) plugin installed, it can
also help you generate a lot of code that's annoying and repetative to write
by hand.

Another example can illustrate.
If you start with the following `example.h` file:

```C++
                               // =============
                               // class Example
                               // =============

class Example {
  private:
    // DATA
    int           d_myIntMember;
    SomeClass    *d_otherPointer_p;
    const char   *d_hostname_p;
    AnotherClass  d_lastMember;

    // CREATORS
    Example(bslma::Allocator *basicAllocator = 0);
        // Default constructor

    Example(const Example& other, bslma::Allocator *basicAllocator = 0);
        // Copy constructor

    // MANIPULATORS
    decl [[1]]

    // ACCESSORS
    decl [[2]]
};

// ============================================================================
//                      INLINE AND TEMPLATE FUNCTION IMPLEMENTATIONS
// ============================================================================

// ACCESSORS
def [[3]]
```

and the following `example.cpp`:

```C++
                               // -------------
                               // class Example
                               // -------------

// CREATORS
Example(bslma::Allocator *basicAllocator)
ctormem [[4]]

cctor [[5]]

// MANIPULATORS
def [[6]]
```

Then by expanding the snippets at [[1]] to [[6]] by pressing TAB (or whatever
else you might have bound to it), you can turn these files with a few extra key
strokes into this header:

```C++
                               // =============
                               // class Example
                               // =============

class Example {
  private:
    // DATA
    int           d_myIntMember;
    SomeClass    *d_otherPointer_p;
    const char   *d_hostname_p;
    AnotherClass  d_lastMember;

    // CREATORS
    Example(bslma::Allocator *basicAllocator = 0);
        // Default constructor

    Example(const Example& other, bslma::Allocator *basicAllocator = 0);
        // Copy constructor

    // MANIPULATORS
    int& myIntMember();
        // Return a reference providing modifiable access to the 'myIntMember'
        // property of this object.

    SomeClass *& otherPointer();
        // Return a reference providing modifiable access to the 'otherPointer'
        // property of this object.

    const char *& hostname();
        // Return a reference providing modifiable access to the 'hostname'
        // property of this object.

    AnotherClass& lastMember();
        // Return a reference providing modifiable access to the 'lastMember'
        // property of this object.

    // ACCESSORS
    int myIntMember() const;
        // Return the 'myIntMember' property of this object.

    const SomeClass *& otherPointer() const;
        // Return a reference providing const access to the 'otherPointer'
        // property of this object.

    const char *hostname() const;
        // Return the 'hostname' property of this object.

    const AnotherClass& lastMember() const;
        // Return a reference providing const access to the 'lastMember'
        // property of this object.
};

// ============================================================================
//                      INLINE AND TEMPLATE FUNCTION IMPLEMENTATIONS
// ============================================================================

// ACCESSORS
inline
int Example::myIntMember() const
{
    
}

inline
const SomeClass *& Example::otherPointer() const
{
    
}

inline
const char *Example::hostname() const
{
    
}

inline
const AnotherClass& Example::lastMember() const
{
    
}
```

and this implementation file:

```C++
                               // -------------
                               // class Example
                               // -------------

// CREATORS
Example(bslma::Allocator *basicAllocator)
: d_myIntMember()
, d_otherPointer_p()
, d_hostname_p()
, d_lastMember()
{
}

Example::Example(const Example& other, bslma::Allocator *basicAllocator = 0)
: d_myIntMember(other.d_myIntMember, basicAllocator)
, d_otherPointer_p(other.d_otherPointer_p, basicAllocator)
, d_hostname_p(other.d_hostname_p, basicAllocator)
, d_lastMember(other.d_lastMember, basicAllocator)
{
}

// MANIPULATORS
int& Example::myIntMember()
{
    
}

SomeClass *& Example::otherPointer()
{
    
}

const char *& Example::hostname()
{
    
}

AnotherClass& Example::lastMember()
{
    
}
```

The above example shows the 4 snippets `decl`, `def`, `cctormem` and `cctor`
in action.

* `decl` is used to generate function declarations.  Currently, it's limited
  to generating declarations for manipulators, getters, and (with another
  snippet `decl_setters`) setters for member variables.  It will either
  generate declarations for all the member variables of the class you're
  working on, or for whatever variables you have selected when you expand the
  snippet using UltiSnips Visual Placeholders feature.
* `def` takes the function declarations from a class definition and turns them
  into implementation stubs.  This is probably the most generally useful
  snippet in BDEFormat as it can be useful when writing any class.  If
  expanded in a header file, it will make the functions 'inline' and as with
  'decl' if you have some function declarations selected when expanding it,
  it'll generate stubs only for those functions.
* `ctormem` is a simple snippet for turning member variable declarations into
  a constructor initialization list.
* `cctor` generates a full copy constructor implementation using the member
  variable definitions either in the class body, or in the visual selection.

All these snippets can get their source data (member variable definitions or
function declarations) in one of two ways: they will either search the current
file and corresponding header (if in a .cpp), or will simply use whatever's
selected at the time they're expanded.  This lets you do things like easily
add more definitions or declare more accessors after the class has already
been written.

The searching deserves a bit more explanation.  The snippets determine what
class they're under by searching up for a comment block like

```C++
                               // =============
                               // class Example
                               // =============
```

or

```C++
                               // -------------
                               // class Example
                               // -------------
```

The `decl` and `def` snippets know what kind of functions/definitions to
generate by looking for lines like:

```C++
    // ACCESSOS

    // MANIPULATORS
```

which are standard BDE section delimiters.

Future Enhancements
-------------------
A number enhancements/additions to these snippets could be implemented.

* Improving the generation of constructor definitions.  Ideally, `def` can be
  made to work for CREATORS, and this will be the next item of work.
* `def` can prepopulate the function bodies with appropriate content if it can
  figure out that it's defining a simple accessor/manipulator or setter.
* If working under just a class header without a section, `def` can also be
  made to just generate the stubs/creators for everything in the class.
