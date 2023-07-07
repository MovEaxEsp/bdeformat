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

    PRIVATE_CREATORS = 7
        # A PRIVATE CREATORS section, containing constructors/destructor

    PUBLIC = 8
        # A 'public:' section

    PROTECTED = 9
        # A 'protected:' section

    PRIVATE = 10
        # A 'private:' section

    END = 11
        # A section end that doesn't indicate the start of another section

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
        "// PRIVATE CREATORS"     : PRIVATE_CREATORS,
        "public:"                 : PUBLIC,
        "protected:"              : PROTECTED,
        "private:"                : PRIVATE,
        "// NOT IMPLEMENTED"      : OTHER,
        "// TYPES"                : OTHER,
        "// PRIVATE TYPES"        : OTHER,
        "// FRIENDS"              : OTHER,
        "// TRAITS"               : OTHER,
        "// PRIVATE CLASS METHODS": OTHER,
        "// CLASS METHODS"        : OTHER,
        "}"                       : END,
        "};"                      : END
    }

    __reverseMap = {val: name for name, val in  __sectionMap.items()}

    @staticmethod
    def check(s):
        """
        Check the specified string 's' to see if it specifies a BDE or C++
        section header.  Return one of the above enumerated values if so, and
        'None' otherwise.
        """
        return SectionType.__sectionMap.get(s.strip(), None)

    @staticmethod
    def getName(section):
        """
        Return the string representation of the specified numeric 'section',
        which is one of the values of this component's enumeration.
        """
        return SectionType.__reverseMap.get(section, "UNKNOWN")
