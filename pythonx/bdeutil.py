#!/usr/bin/env python

"""
bdeutil.py: Utility functions for formatting C++ according to BDE standard.

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

def findNextOccurrence(line, pos, chars, direction):
    """
    Find the position in 'line' of the next occurrence (if 'direction' is
    '1') or previous occurrence (if 'direction' is '-1) of any of the
    specified 'chars' starting at the specified 'pos'.  Return -1 if none is
    found
    """

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

    return (openPos, closePos) if openPos and closePos else None

def determineElements(line, openClose):
    """
    Return a list containing the comma separated elements within the
    specified 'openClose'. Any comment following an element is assumed to be a
    part of the element.
    """
    elements = []
    startPos = openClose[0] + 1
    while startPos < openClose[1]:
        endPos = findSkippingGroups(line, startPos, ",", 1)
        if endPos == -1 or endPos >= openClose[1]:
            endPos = openClose[1]

        element = line[startPos:endPos + 1].strip()
        if len(element) >= 2 and element[0] == '/' and element[1] == '/':
            # This 'element' starts with a comment.  Append the comment to the
            # end of the previous element

            commentEndPos = element.find('\n')
            elements[len(elements)-1] += " " + element[0:commentEndPos].strip()

            element = element[commentEndPos + 1:].strip()

        startPos = endPos + 1

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
    is raised
    """
    endPos = findSkippingGroups(element, 0, ",;)}>]", 1)
    if endPos == -1:
        raise ValueError("\"" + element + "\" has no end character")

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
    else:
        typeStr = ""

    starsStr = element[starsStart:nameStart].replace(" ", "")
    nameStr = " ".join(element[nameStart:nameEnd + 1].strip().split())

    if equalPos > 0:
        valueStr = element[equalPos:endPos].strip()
    else:
        valueStr = ""

    endChar = element[endPos]

    commentStr = element[endPos  + 1:].replace("//", "").replace("\n", " ")
    commentStr = commentStr.strip()

    return (typeStr, starsStr, nameStr, valueStr, endChar, commentStr)

def alignElementParts(parsedElements):
    """
    Align the parts of all the specified 'parsedElements' which is a list of
    tuples returned by 'parseElement' by appropriately padding the 'type',
    'stars, 'name', and 'value' elements of each and returning a new list of
    these aligned tuples.
    """
    typeWidth = 0
    starsWidth = 0
    nameWidth= 0
    numWithValues = 0

    for elem in parsedElements:
        typeWidth = max(typeWidth, len(elem[0]))
        starsWidth = max(starsWidth, len(elem[1]))
        nameWidth= max(nameWidth, len(elem[2]))
        if len(elem[3]) > 0:
            numWithValues += 1

    if typeWidth == 0:
        # If there are no types, ignore aligning the stars
        starsWidth = 0

    retList = []
    for elem in parsedElements:
        newType = elem[0].ljust(typeWidth)
        newStars = elem[1].rjust(starsWidth)

        # Pad the name on the right if this element has a value
        if numWithValues > 1 and len(elem[3]) > 0:
            newName = elem[2].ljust(nameWidth)
        else:
            newName = elem[2]

        retList.append((newType, newStars, newName, elem[3], elem[4], elem[5]))

    return retList

def writeAlignedElements(alignedElements):
    """
    Return '([(<elem>, <comment>), ...], <namePos>)'
    where <elem> is the complete printed representation of an element in the
    specified 'alignedElements', <comment> is the corresponding comment, and
    <namePos> is the column where the <name> of each element starts.
    """

    ret = []
    nameStart = 0
    for elem in alignedElements:
        line = ""

        # Write type
        if len(elem[0]) > 0:
            line = elem[0] + " "
            nameStart = len(line) + 1

        # Write stars
        line = line + elem[1]

        # Write name
        line = line + elem[2]

        # Write value
        if len(elem[3]) > 0:
            line = line + " " + elem[3]

        line = line + elem[4]

        ret.append((line, elem[5]))

    return (ret, nameStart)

def tryWriteBdeGroupOneLine(parsedElements, width):
    """
    Return the specified 'parsedElements' written on a single line if the
    result would be at most 'width' characters, or 'None' otherwise
    """

    for elem in parsedElements:
        if len(elem[5]) > 0:
            # If any element has a comment, we can't write on one line
            return None

    ret = " ".join(
       [" ".join(filter(len, [elem[0], elem[1] + elem[2], elem[3]])) +
                 elem[4] + elem[5] for elem in parsedElements])

    return None if len(ret) > width else ret

def writeBdeGroupMultiline(parsedElements, width, prefix, suffix):
    """
    Return '([(<line>, <comment>), ...], <namePos>)'
    where <line>  is a correctly aligned
    line consisting of the specified 'prefix' and/or an element of the
    specified 'parsedElements' without the comments at most 'width' characters,
    and the last element ends with the specified 'suffix', <comment> is a
    comment corresponding to this line, and <namePos> is the column where the
    names start in the lines
    """

    writeAlignedElementsRet = writeAlignedElements(
                                             alignElementParts(parsedElements))
    writtenElements = [x[0] for x in writeAlignedElementsRet[0]]
    comments = [x[1] for x in writeAlignedElementsRet[0]]

    # We need to figure out if we can write the first element on the same line
    # as the prefix or not
    maxWrittenElemWidth = reduce(max, [len(x) for x in writtenElements])

    maxLineLen = max(maxWrittenElemWidth,
                     len(writtenElements[-1]) + len(suffix))


    ret = []
    if len(prefix) + maxLineLen > width:
        # Need to put prefix on its own line
        ret.append((prefix, ""))
        elemStartColumn = width - maxLineLen
    else:
        # Write first element on same line as prefix
        ret.append((prefix + writtenElements[0], comments[0]))
        writtenElements = writtenElements[1:]
        comments = comments[1:]
        elemStartColumn = len(prefix)

    for elem, comment in zip(writtenElements, comments):
        ret.append((elem.rjust(len(elem) + elemStartColumn), comment))

    ret[-1] = (ret[-1][0] + suffix, ret[-1][1])
    return (ret, writeAlignedElementsRet[1] + elemStartColumn)

def splitCommentIntoLines(comment, maxWidth):
    """
    Return a list of lines, each at most 'maxWidth' characters (where
    possible), consisting of the specified 'comment'
    """

    ret = []
    comment = comment.strip()
    while len(comment) > maxWidth:
        if comment[maxWidth] != ' ':
            # The line ends in the middle of a word.  Find the last space
            spacePos = comment.rfind(' ', 0, maxWidth)
            if spacePos == -1:
                # The word is longer than 'maxWidth'.  Include it on its own
                # line.
                spacePos = comment.find(' ')
        else:
            spacePos = maxWidth

        # The line ends at a word end
        ret.append(comment[:spacePos].strip())
        comment = comment[spacePos:].strip()

    if len(comment) > 0:
        ret.append(comment)

    return ret

def writeComments(linesAndComments,
                  minCommentWidth,
                  maxWidth,
                  lineWidth,
                  spaceIfMultiline):
    """
    Return a list of lines using the specified 'linesAndComments' which looks
    like '[(<line>, <comment>),...]', the specified 'minCommentWidth' to
    indicate the least amount of remaining space on a line to still start a
    comment on it, the specified 'maxWidth' to indicate the maximum width
    comments can use on any line, the specified 'lineWidth' to indicate the
    maximum line width, and the specified 'spaceIfMultiline' to indicate if an
    empty line should be placed between each <line> and associated <comment>
    if any <line>, <comment> pair ends up spanning multiple lines
    """

    # + 2 because there are 2 spaces before the comment starts
    maxContentWidth = reduce(max, [len(x[0]) for x in linesAndComments]) + 2
    remainingSpaceOnLine = lineWidth - maxContentWidth
    if remainingSpaceOnLine >= minCommentWidth:
        commentWidth = remainingSpaceOnLine
    else:
        commentWidth = maxWidth

    commentPos = lineWidth - commentWidth

    # +3 is for '// '
    maxCommentWidth = reduce(max, [len(x[1]) for x in linesAndComments]) + 3
    haveMultiline = (maxCommentWidth > commentWidth)

    ret = []
    commentPrefix = ' ' * (commentPos - 1)
    for line, comment in linesAndComments:
        commentLines = splitCommentIntoLines(comment, commentWidth - 3)

        contentWidth = len(line) + 2
        if not commentLines or (contentWidth + commentWidth) > lineWidth:
            # Write 'line' on its own line and put the comment on a separate
            # line, if there is a comment
            ret.append(line)
        else:
            # Write first line of comment along with 'line
            ret.append(line.ljust(commentPos - 1) + "// " + commentLines[0])
            commentLines = commentLines[1:]


        for commentLine in commentLines:
            ret.append(commentPrefix + "// " + commentLine)

        if haveMultiline and spaceIfMultiline:
            ret.append("")

    return ret


def fixBdeBlock(text, pos, width, minCommentWidth):
    """
    Fix the bde block containing the specified 'pos' in the specified 'text'
    according to the specified 'width' and 'minCommentWidth', and return a
    list of lines consisting of the fixed text, or 'None' if a block
    couldn't be found.
    """
    openClose = findOpenClose(text, pos)
    if not openClose:
        return None

    elements = [parseElement(e) for e in determineElements(text, openClose)]

    preLines = text[:openClose[0] + 1].splitlines()
    postLines = text[openClose[1] + 1:].splitlines()

    prefix = preLines[-1] if preLines else ""
    preLines = preLines[:-1]

    suffix = postLines[0] if postLines else ""
    postLines = postLines[1:]

    oneLine = tryWriteBdeGroupOneLine(elements,
                                      width - len(prefix) - len(suffix))
    if oneLine:
        return preLines + [prefix + oneLine + suffix] + postLines

    multilineRet = writeBdeGroupMultiline(elements, width, prefix, suffix)

    # TODO call writeComments

    return preLines + [x[0] for x in multilineRet[0]] + postLines
