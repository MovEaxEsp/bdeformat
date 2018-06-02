# TODO fix comment and move test drivers
"""
bdeformatutil.py: Utility functions for formatting C++ according to BDE
standard.

This module defines a number of functions that together can be used to format
a wide range of C++ constructs according to BDE style.  These include:

* Function definitions
    int someFunctions(const char        *arg1,
                      const SomeObject&  arg2,
                      bslma::Allocator  *allocator) const;

* Function calls
    int ret = foo->doSomething(y,
                               static_cast<void *>(x),
                               someReallyLongVariable);

* Class data definitions
    int               d_version;      // version of the widget

    const char       *d_name;         // name of the widget

    double            d_foo;          // a member with a very complicated
                                      // purpose that requires a long
                                      // explanation

    bslma::Allocator *d_allocator_p;  // held, not owned

As well as variations on these such as template parameter lists and POD
initialization lists
"""

import re

from sectiontype import SectionType

def findNextOccurrence(line, pos, chars, direction):
    """
    Find the position in 'line' of the next occurrence (if 'direction' is
    '1') or previous occurrence (if 'direction' is '-1) of any of the
    specified 'chars' starting at the specified 'pos'.  Return -1 if none is
    found
    """

    if pos < len(line):
        end = -1 if direction < 0 else len(line)
        for i in range(pos, end, direction):
            for c in chars:
                if line[i] == c:
                    return i

    return -1

def findSkippingGroups(line, pos, chars, direction):
    """
    Find the first of the specified 'chars', searching forwards (if 'direction'
    is '1') or backwards (if 'direction' is '-1') from position 'pos'
    in the specified 'line', skipping sections surrounded by (), <>, or [].
    Return its position, or -1 if not found
    """

    toFind = ""
    groupMap = ""
    if direction > 0:
        toFind = "(<[{" + chars
        groupMap = {"(" : ")", "<" : ">", "[" : "]", "{" : "}"}
    else:
        toFind = ")>]}" + chars
        groupMap = {")" : "(", ">" : "<", "]" : "[", "}" : "{"}

    while True:
        pos = findNextOccurrence(line, pos, toFind, direction)

        # Can't find the character or a group character
        if pos == -1:
            return -1

        #If we found a '>', see if it's actually '->', and shouldn't be
        #treated as the close of a group
        if pos > 0 and line[pos] == '>' and line[pos-1] == '-':
            # Skip this character.
            pos += direction
        elif line[pos] in chars:
            # Found one of the characters we're looking for
            return pos
        else:
            break

    # We found an opening or closing character for a group.  Recursively call
    # this function to skip over the group, and look for our character again
    groupChar = groupMap[line[pos]]

    pos += direction

    pos = findSkippingGroups(line, pos, groupChar, direction)
    if pos == -1:
        # No corresponding group character
        return -1

    return findSkippingGroups(line, pos + direction, chars, direction)

def findOpen(line, pos):
    """
    Return the position of the opening character surrounding the specified
    'pos' in the specified 'line', or return 'None' if it couldn't be found.
    """
    openPos = findSkippingGroups(line, pos, "(<[{", -1)
    return None if openPos == -1 else openPos

def findClose(line, pos):
    """
    Return the position of the closing character surrounding the specified
    'pos' in the specified 'line', or return 'None' if it couldn't be found.
    """
    closePos = findSkippingGroups(line, pos, ")>]}", 1)
    return None if closePos == -1 else closePos

def findOpenClose(line, pos):
    """
    Return a tuple '(open, close)' containing the positions of the opening and
    closing characters surrounding the specified 'pos' in the specified
    'line', or return 'None' if they couldn't be found.
    """

    openPos = findOpen(line, pos)
    closePos = findClose(line, pos)

    if openPos == pos:
        openPos = findOpen(line, pos - 1)
        if openPos != None:
            closePos = findClose(line, openPos + 1)
    elif closePos == pos:
        closePos = findClose(line, pos + 1)
        if closePos != None:
            openPos = findOpen(line, closePos - 1)

    return (openPos, closePos) if openPos != None and closePos != None else None
def findComment(line, start, end):
    """
    Find end position of the comment block starting at the specified 'start'
    position in the specified 'line', going up to the specified 'end'
    position'.  A comment block consists of any whitespace up to the starting
    '//' sequence, and any subsequent comment lines until either 'end' is
    reached, or a non-comment line is found.
    If a comment isn't found from the 'start' position, return '-1'.
    """
    while start < end and line[start] in " \n":
        start += 1

    commentEnd = -1
    while start < end:
        if line[start] == " ":
            start += 1
            continue

        if line.find("//", start) == start:
            nlPos = line.find("\n", start)
            if nlPos == -1 or nlPos >= end:
                start = end
            else:
                start = nlPos + 1

            commentEnd = start
        else:
            break

    return commentEnd

def determineElements(line, openClose):
    """
    Return a list containing the comma/semicolon separated elements within the
    specified 'openClose'. Any comment following an element is assumed to be a
    part of the element.
    """
    elements = []
    startPos = openClose[0] + 1
    while startPos < openClose[1]:
        # 's' will be the position to start search on first non-comment line
        s = startPos

        endPos = findSkippingGroups(line, s, ",;", 1)
        if endPos == -1 or endPos >= openClose[1]:
            endPos = openClose[1]

        commentEnd = findComment(line, endPos + 1, openClose[1])
        if commentEnd >= 0:
            endPos = commentEnd

        element = line[startPos:endPos + 1].strip()

        startPos = endPos + 1

        if len(element) > 0:
            elements.append(element)

    return elements

def parseElement(element):
    """
    Parse the specified C++ 'element', which can be any of the following:
    * A definition of a function/template parameter
    * An argument in a function call/template definition
    * A variable declaration
    Return a tuple containing '(<type>, <stars>, <name>, <value>, <endChar>,
    <comment>)'
    where any piece that isn't present in 'element' is an empty string. For
    example, member variable declaration like
    'const unsigned char *abc = "123"; // easy'
    would return
    '("const unsigned char", "*", "abc", "= "123"", ";", "// easy")'
    Note:
    For references, the '&' is part of the type if there is a type and the
    'name' if there isn't.  If the 'element' couldn't be parsed, a ValueError
    is raised.

    Note that this function isn't perfect, and will parse certain 'value'
    constructs, such as 'a - b' or 'const char *' for example, as having both
    a type and value.  However, it should be able to correctly parse any
    element that does have a type and value.  Use 'fixParsedElements' below to
    make a group of parsed elements consistent in this regard.
    """
    END_CHARS = ",;)}>]"
    endPos = findSkippingGroups(element, 0, END_CHARS, 1)
    commentPos = element.find("//")
    if commentPos >= 0 and commentPos < endPos:
        # the element has no normal 'end' character, so end it where the
        # comment starts
        endPos = commentPos

    if endPos == -1:
        endPos = len(element)

    equalPos = findSkippingGroups(element, 0,"=", 1)
    if equalPos > endPos:
        # We don't care about an '=' in the comment
        equalPos = -1

    if equalPos > 0:
        nameEnd = equalPos - 1
    else:
        nameEnd = endPos - 1

    while element[nameEnd] == ' ':
        nameEnd -= 1

    nameStart = findSkippingGroups(element, nameEnd, " *&", -1)
    if nameStart == -1:
        # The 'element' starts with the name
        nameStart = 0
    elif element[nameStart] == " " or element[nameStart] == "*":
        nameStart += 1

    starsStart = nameStart - 1;
    while element[starsStart] == '*' or element[starsStart] == ' ':
        starsStart -= 1

    starsStart += 1

    typeStart = 0
    while element[typeStart] in " *":
        typeStart += 1

    if typeStart < starsStart and element[typeStart] != '(':
        # We assume that if the 'element' doesn't start with a '(...)' part,
        # and there are some characters before 'starsStart', that it starts
        # with the type
        haveType = True
    else:
        haveType = False

    if haveType:
        typeStr = element[:starsStart].strip()
        starsStr = element[starsStart:nameStart].replace(" ", "")
    else:
        typeStr = ""
        starsStr = ""
        nameStart = 0

    nameStr = " ".join(element[nameStart:nameEnd + 1].strip().split())

    if equalPos > 0:
        valueStr = element[equalPos:endPos].strip()
    else:
        valueStr = ""

    endChar = element[endPos] if endPos < len(element) else ""
    if endChar not in END_CHARS:
        endChar = ""

    whitespaceRegex = re.compile(r'\s+')

    commentStr = ""
    if commentPos >= 0:
        commentStr = element[commentPos:].replace("//", "").replace("\n", " ")
        commentStr = commentStr.strip()
        commentStr = whitespaceRegex.sub(" ", commentStr)

    return (typeStr, starsStr, nameStr, valueStr, endChar, commentStr)

def fixParsedElements(parsedElements):
    """
    'parseElements' isn't perfect and will occasionally flag what should
    be just a value or just a type as having both.  This function will attempt
    to make the specified 'parsedElements' (obtained from multiple calls to
    'parseElement') consistent by putting all types and values into the
    'value' field of the element if any of the parsed elements is missing a
    type or value.  It returns the fixed (or unmodified) elements.
    """

    needFix = False
    for elem in parsedElements:
        if len(elem[0]) == 0 or len(elem[2]) == 0:
            needFix = True
            break

    if needFix:
        ret = []
        for elem in parsedElements:
            newName = " ".join(filter(len, [elem[0], elem[1] + elem[2]]))
            ret.append(("", "", newName, elem[3], elem[4], elem[5]))

        return ret
    else:
        return parsedElements

def parseMembers(decl):
    """
    Parse the specified member variable declaration section 'decl' and
    return a list of the members defined there.
    """

    # Remove comments
    mems = re.sub(r'//.*', '', decl)

    # Remove empty lines
    mems = re.sub(r'\n\s*\n', '\n', mems, 0, re.MULTILINE)

    # Remove last newline, if any
    mems = re.sub(r'\n\s*$', '', mems, 0, re.MULTILINE)

    # Remove declarations/semicolon
    mems = [re.sub(r'.*[ *&]([^ *&]*);.*', r'\1', l) \
                    for l in mems.split('\n')]

    return mems

def findClassName(lineGen):
    """
    Keep getting lines from the specified 'lineGen' generator, looking for
    a class/struct section name, and return the class name if found,
    otherwise return None.  A section name looks like
    // ---------- (or ======)
    // class Foo
    // ---------
    """

    if not hasattr(findClassName, "pattern"):
        findClassName.pattern = re.compile(r'^ *// (?:class|struct) (.*)')

    for line in lineGen:
        match = findClassName.pattern.match(line)
        if (match):
            return match.group(1)

    return None

def extractClassSection(lineGen, className, section):
    """
    Using the specified 'lineGen' generator of lines, look for the definition
    of the specified 'className' and extract from within it the specified
    'section' 'SectionType'.  Return the content of the requested section or
    None if it couldn't be found.
    """

    # First search for the class
    foundClass = findClassName(lineGen)
    while foundClass != None and foundClass != className:
        foundClass = findClassName(lineGen)

    if foundClass == None:
        # Couldn't find class section
        return None

    # Look for the requested section
    foundSection = False
    for line in lineGen:
        if SectionType.check(line) == section:
            foundSection = True
            break

    if not foundSection:
        # Couldn't find the requested section
        return None

    # Keep collecting lines until we hit another SectionType
    res = []
    for line in lineGen:
        if SectionType.check(line) == None:
            res.append(line)
        else:
            break

    return "\n".join(res)
