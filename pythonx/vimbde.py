import sys
import os
import vim

import bdeutil

def fixBdeBlock():
    buf = vim.current.buffer
    row, col = vim.current.window.cursor

    startRow = endRow = row - 1
    text = buf[startRow]

    while not bdeutil.findOpen(text, col) and endRow - startRow < 20:
        startRow -= 1
        prevLine = buf[startRow]
        text = prevLine + "\n" + text
        col += len(prevLine) + 1

    while not bdeutil.findClose(text, col) and endRow - startRow < 20:
        endRow += 1
        text = text + "\n" + buf[endRow]

    try:
        fixedBlock = bdeutil.fixBdeBlock(text, col, 79, 30)
    except ValueError as e:
        print e
        return

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
