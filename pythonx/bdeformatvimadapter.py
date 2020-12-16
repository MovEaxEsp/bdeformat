"""
bdeformatvimadapter.py: Adapter to expose 'bdeformat' inside vim
"""

import vim
import bdeformatutil

def formatBde():
    buf = vim.current.buffer
    lineSource = lambda row: buf[row]
    try:
        row, col = vim.current.window.cursor
        startEnd, lines = bdeformatutil.formatBde(lineSource, row - 1, col)
    except ValueError as e:
        print(e)
        return

    # Figure out if we need to add or remove lines
    startRow, endRow = startEnd
    oldLines = endRow - startRow + 1
    newLines = len(lines)
    if oldLines < newLines:
        # Add lines
        for i in range(newLines - oldLines):
            vim.command("normal o")
    elif newLines < oldLines:
        # Delete lines
        del buf[startRow:startRow + oldLines - newLines]

    for i in range(len(lines)):
        buf[startRow + i] = lines[i]
