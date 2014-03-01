"""
bdeformatutil.py: Utility for formating a block or section of code according
to the BDE standard
"""

import bdeutil
from sectiontype import SectionType

def _checkSectionSize(startRow, endRow):
    if endRow - startRow >= 50:
        raise ValueError("Can't find group/section")

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

    # Find start of group/section
    sectionType = SectionType.check(text)
    while sectionType == None:
        if bdeutil.findOpen(text, col):
            break;

        _checkSectionSize(startRow, endRow)

        startRow -= 1
        sectionType = SectionType.check(lineSource(startRow))
        if sectionType == None:
            text = lineSource(startRow) + "\n" + text
            col += len(lineSource(startRow)) + 1
        else:
            startRow += 1

    if sectionType == None:
        # We found the start of a group
        while not bdeutil.findClose(text, col):
            endRow += 1
            text = text + "\n" + lineSource(endRow)

            _checkSectionSize(startRow, endRow)
    else:
        # We found the start of a section
        endRow += 1
        while SectionType.check(lineSource(endRow)) == None:
            text = text + "\n" + lineSource(endRow)
            endRow += 1
            _checkSectionSize(startRow, endRow)

        endRow -= 1

    if sectionType == SectionType.DATA:
        fixedBlock = bdeutil.fixBdeData(text, 79, 40)
    else:
        fixedBlock = bdeutil.fixBdeBlock(text, col, 79, 30)

    if not fixedBlock:
        raise ValueError("Couldn't find BDE block")

    return ((startRow, endRow), fixedBlock)
