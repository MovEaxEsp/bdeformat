"""
sectiontype.py: Enumeration of C++ and BDE section types and utility for
determining them
"""

class SectionType:

    DATA = 1
        # A DATA section, containing field definitions

    MANIPULATORS = 2
        # A MANIPULATORS section, containing member function
        # declarations/definitions

    ACCESSORS = 3
        # An ACCESSORS section, containing member function
        # declarations/definitions

    CREATORS = 4
        # A CREATORS section, containing constructors/destructor

    PUBLIC = 5
        # A 'public:' section

    PROTECTED = 6
        # A 'protected:' section

    PRIVATE = 7
        # A 'private:' section

    OTHER = 99
        # A different known section type

    __sectionMap = {
        "// DATA"                 : DATA,
        "// PUBLIC DATA"          : DATA,
        "// MANIPULATORS"         : MANIPULATORS,
        "// PRIVATE MANIPULATORS" : MANIPULATORS,
        "// ACCESSORS"            : ACCESSORS,
        "// PRIVATE ACCESSORS"    : ACCESSORS,
        "// CREATORS"             : CREATORS,
        "// PRIVATE CREATORS"     : CREATORS,
        "public:"                 : PUBLIC,
        "protected:"              : PROTECTED,
        "private:"                : PRIVATE,
        "// NOT IMPLEMENTED"      : OTHER,
        "// TYPES"                : OTHER,
        "// PRIVATE TYPES"        : OTHER
    }

    @staticmethod
    def check(s):
        """
        Check the specified string 's' to see if it specifies a BDE or C++
        section header.  Return one of the above enumerated values if so, and
        'None' otherwise.
        """
        s = s.strip()
        if s in SectionType.__sectionMap:
            return SectionType.__sectionMap[s]
        else:
            return None
