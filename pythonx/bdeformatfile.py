#!/usr/bin/env python
"""
bdeformatfile.py: BDE formatter that modifies a specific section of a file

This module can be executed on the command line to modify a particular section
of a file and format it according to the BDE standard.  If the formatting
fails for any reason, an error code is returned and the original file is
unmodified.
"""

import mmap
import os
import sys

import bdeformatutil

def formatBde(fileName, row, col):
    """
    Format the code around the specified 'col' of the specified 'row' in the
    specified 'fileName' and overwrite the specified 'fileName' if the
    formatting succeeds.
    """

    with open(fileName, "r+b") as f:
        m = mmap.mmap(f.fileno(), 0)
        linePositions = []
        def lineSource(r):
            while len(linePositions) <= r:
                linePositions.append(m.tell())
                m.readline()

            pos = m.tell()
            m.seek(linePositions[r])
            ret = m.readline()[:-1]
            m.seek(pos)

            return ret

        try:
            startEnd, lines = bdeformatutil.formatBde(lineSource, row, col)
        except ValueError as e:
            print e
            return 1

        # Make sure we have the position of the line after the end line
        start, end = startEnd
        while end + 1 >= len(linePositions):
            m.seek(linePositions[-1])
            m.readline()
            linePositions.append(m.tell())

        # Update the file
        fixed = "\n".join(lines)
        fixedLen = len(fixed) + 1 # Add a newline at the end
        startPos = linePositions[start]
        endPos = linePositions[end + 1]
        replaceLen = endPos - startPos
        moveDest = endPos + fixedLen - replaceLen
        moveSrc = endPos
        moveSize = m.size() - endPos

        if fixedLen > replaceLen:
            # Grow the file, then move
            m.resize(m.size() + fixedLen - replaceLen)
            m.move(moveDest, moveSrc, moveSize)
        elif fixedLen < replaceLen:
            # Move, then shrink file
            m.move(moveDest, moveSrc, moveSize)
            m.resize(m.size() + fixedLen - replaceLen)

        m.seek(startPos)
        m.write(fixed)
        m.write("\n")
        m.close()

    # Touch the file, so editors detect that it changed
    os.utime(fileName, None)

    return 0;

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: <fileName> <0-based row number> <0-based column number>"
        sys.exit(1)

    ret = formatBde(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    sys.exit(ret)
