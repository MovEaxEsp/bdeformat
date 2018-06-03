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
from parseutil import *
from functools import reduce

from sectiontype import SectionType

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

        # Write stars
        line = line + elem[1]

        nameStart = len(line)

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
    maxLineLen = reduce(max, [len(x) for x in writtenElements])

    if len(comments[-1]) == 0:
        maxLineLen = max(maxLineLen, len(writtenElements[-1]) + len(suffix))

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

    # Add suffix.  If last element has a comment, put the suffix on its own
    # line
    if len(suffix) > 0:
        if len(comments[-1]) > 0:
            ret.append((suffix.rjust(len(suffix) + elemStartColumn), ""))
        else:
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

    # Figure out the comment width that will result in the fewest lines being
    # generated.  The possible widths can be the remaining space in any line
    # or simply maxWidth

    possibleWidths = set()
    possibleWidths.add(maxWidth)
    for lineAndComment in linesAndComments:
        # - 2 because there are 2 spaces before the comment starts
        pWidth = lineWidth - len(lineAndComment[0]) - 2
        if pWidth <= maxWidth and pWidth > 0:
            possibleWidths.add(pWidth)

    maxCommentWidth = reduce(max, [len(x[1]) for x in linesAndComments])
    if maxCommentWidth > 0:
        # +3 is for '// '
        maxCommentWidth += 3

    best = []
    bestWidth = lineWidth
    for commentWidth in possibleWidths:
        commentPos = lineWidth - commentWidth
        if commentWidth <= 3:
            continue

        haveMultiline = maxCommentWidth + maxContentWidth > lineWidth

        result = []
        commentPrefix = ' ' * commentPos
        for line, comment in linesAndComments:
            commentLines = splitCommentIntoLines(comment, commentWidth - 3)

            contentWidth = len(line) + 2
            if not commentLines or commentPos < contentWidth:
                # Write 'line' on its own line and put the comment on a
                # separate line, if there is a comment
                result.append(line)
            else:
                # Write first line of comment along with 'line
                result.append(line.ljust(commentPos) + "// " + commentLines[0])
                commentLines = commentLines[1:]


            for commentLine in commentLines:
                result.append(commentPrefix + "// " + commentLine)

            if haveMultiline and spaceIfMultiline:
                result.append("")

        while result[-1] == "":
            result = result[:-1]

        isBest = len(best) == 0
        isBest = isBest or len(best) > len(result)
        isBest = isBest or (len(best) == len(result) and
                            commentWidth < bestWidth)
        if isBest:
            best = result
            bestWidth = commentWidth

    if len(best) == 0:
        best = [x[0] for x in linesAndComments]

    return best


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

    # If the closing character is '>', and the char before it is '>', put a
    # space between them. (Once we have C++11 compilers, this won't be
    # necessary)
    if text[openClose[1]] == '>':
        prevChar = openClose[1] - 1#
        while text[prevChar] in " \#n":
            prevChar -= 1          #
                                   #
        if text[prevChar] == '>':
            text = text[:openClose[1]] + ' ' + text[openClose[1]:]
            openClose = (openClose[0], openClose[1] - 1)

    elements = [parseElement(e) for e in determineElements(text, openClose)]
    elements = fixParsedElements(elements);

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

    namePos = multilineRet[1]
    maxCommentWidth = width - namePos - 2

    ret = writeComments(multilineRet[0],
                        minCommentWidth,
                        maxCommentWidth,
                        width,
                        False)

    return preLines + ret + postLines


def fixBdeData(text, width, minCommentWidth):
    """
    Fix the BDE data section in the specified 'text' according to the
    specified 'width' and 'minCommentWidth', and return a list of lines
    consisting of the fixed text, or 'None' if there was a problem parsing the
    data definitions.
    """
    openClose = (-1, len(text))
    elements = [parseElement(e) for e in determineElements(text, openClose)]
    elements = fixParsedElements(elements);

    prefix = " " * (len(text) - len(text.lstrip()))
    multilineRet = writeBdeGroupMultiline(elements, width, prefix, "")

    namePos = multilineRet[1]
    maxCommentWidth = width - namePos - 2
    ret = writeComments(multilineRet[0],
                        minCommentWidth,
                        maxCommentWidth,
                        width,
                        True)

    # Add a newline after the last line to separate this section from the next
    # one
    ret.append("")

    return ret

def formatBde(lineSource, row, col):
    """
    Using the specified 'lineSource', which takes an integer row argument and
    returns this row of text from the code being formatter, format the bde
    block/section around the specified 'col' of the specified 'row'.  Return a
    tuple ((start, end), lines) where '(start, end) is the range of lines
    (inclusive) to be replaced by the 'lines', which is a list of strings.
    Throw a ValueError if there is a problem formatting.
    """

    startRow = endRow = row
    text = lineSource(startRow)

    def checkSectionSize(startRow, endRow):
        if endRow - startRow >= 300:
            raise ValueError("Can't find group/section")

    # Find start of group/section
    sectionType = SectionType.check(text)
    while sectionType == None:
        if findOpen(text, col):
            break;

        checkSectionSize(startRow, endRow)

        startRow -= 1
        sectionType = SectionType.check(lineSource(startRow))
        if sectionType == None:
            text = lineSource(startRow) + "\n" + text
            col += len(lineSource(startRow)) + 1
        else:
            startRow += 1

    if sectionType == None:
        # We found the start of a group
        while not findClose(text, col):
            endRow += 1
            text = text + "\n" + lineSource(endRow)

            checkSectionSize(startRow, endRow)
    else:
        # We found the start of a section
        endRow += 1
        while SectionType.check(lineSource(endRow)) == None:
            text = text + "\n" + lineSource(endRow)
            endRow += 1
            checkSectionSize(startRow, endRow)

        endRow -= 1

    if sectionType == SectionType.DATA:
        fixedBlock = fixBdeData(text, 79, 40)
    else:
        fixedBlock = fixBdeBlock(text, col, 79, 30)

    if not fixedBlock:
        raise ValueError("Couldn't find BDE block")

    return ((startRow, endRow), fixedBlock)
