import sys
import os
import vim

import bdeutil
from sectiontype import SectionType

def _checkSectionSize(startRow, endRow):
    if endRow - startRow >= 50:
        raise ValueError("Can't find group/section")

def _fixBdeBlockImp():
    buf = vim.current.buffer
    row, col = vim.current.window.cursor

    startRow = endRow = row - 1
    text = buf[startRow]

    # Find start of group/section
    sectionType = SectionType.check(text)
    while sectionType == None:
        if bdeutil.findOpen(text, col):
            break;

        _checkSectionSize(startRow, endRow)

        startRow -= 1
        sectionType = SectionType.check(buf[startRow])
        if sectionType == None:
            text = buf[startRow] + "\n" + text
            col += len(buf[startRow]) + 1
        else:
            startRow += 1

    if sectionType == None:
        # We found the start of a group
        while not bdeutil.findClose(text, col):
            endRow += 1
            text = text + "\n" + buf[endRow]

            _checkSectionSize(startRow, endRow)
    else:
        # We found the start of a section
        endRow += 1
        while SectionType.check(buf[endRow]) == None:
            text = text + "\n" + buf[endRow]
            endRow += 1
            _checkSectionSize(startRow, endRow)

        endRow -= 1

    if sectionType == SectionType.DATA:
        fixedBlock = bdeutil.fixBdeData(text, 79, 40)
    else:
        fixedBlock = bdeutil.fixBdeBlock(text, col, 79, 30)

    if not fixedBlock:
        print "Couldn't find BDE block"
        return

    # Figure out if we need to add or remove lines
    oldLines = endRow - startRow + 1
    newLines = len(fixedBlock)
    if oldLines < newLines:
        # Add lines
        for i in range(newLines - oldLines):
            vim.command("normal o")
    elif newLines < oldLines:
        # Delete lines
        del buf[startRow:startRow + oldLines - newLines]

    for i in range(len(fixedBlock)):
        buf[startRow + i] = fixedBlock[i]

def fixBdeBlock():
    try:
        _fixBdeBlockImp()
    except ValueError as e:
        print e
