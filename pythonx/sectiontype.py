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

    PRIVATE_MANIPULATORS = 3
        # A PRIVATE MANOPIULATORS section, containing member function
        # declaratoions/definitions

    ACCESSORS = 4
        # An ACCESSORS section, containing member function
        # declarations/definitions

    PRIVATE_ACCESSORS = 5
        # A PRIVATE ACCESSORS section, containing member function
        # declarations/definitions

    CREATORS = 6
        # A CREATORS section, containing constructors/destructor

    PUBLIC = 7
        # A 'public:' section

    PROTECTED = 8
        # A 'protected:' section

    PRIVATE = 9
        # A 'private:' section

    OTHER = 99
        # A different known section type

    __sectionMap = {
        "// DATA"                 : DATA,
        "// PUBLIC DATA"          : DATA,
        "// MANIPULATORS"         : MANIPULATORS,
        "// PRIVATE MANIPULATORS" : PRIVATE_MANIPULATORS,
        "// ACCESSORS"            : ACCESSORS,
        "// PRIVATE ACCESSORS"    : PRIVATE_ACCESSORS,
        "// CREATORS"             : CREATORS,
        "// PRIVATE CREATORS"     : CREATORS,
        "public:"                 : PUBLIC,
        "protected:"              : PROTECTED,
        "private:"                : PRIVATE,
        "// NOT IMPLEMENTED"      : OTHER,
        "// TYPES"                : OTHER,
        "// PRIVATE TYPES"        : OTHER,
        "// FRIENDS"              : OTHER,
        "// TRAITS"               : OTHER,
        "}"                       : OTHER,
        "};"                      : OTHER
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
