""""
sniptil.py: Utility functions for building bdeformat snippets

This module defines functions that are used to generate UltiSnip snippets for
various BDE-style portions of C++.
"""

import bdeformatutil
import vim
import parseutil
import re
from sectiontype import SectionType
import textwrap

s_commentTextwrap = textwrap.TextWrapper()
s_commentTextwrap.width = 79
s_commentTextwrap.initial_indent = "        // "
s_commentTextwrap.subsequent_indent = s_commentTextwrap.initial_indent

def snipOptional(snipNum, text, expandWhenNotEmpty = True):
    """
    Return a snippet string that will have the specified 'text' depending on
    whether the content of the specified 'snipNum' snippet tabstop isn't
    empty, as determined by the specified 'expansdWhenNotEmpty'.
    """

    return "`!p snip.rv = \"\"\"" + text + "\"\"\" " + \
            "if len(t[" + str(snipNum) + "]) " +\
            (">" if expandWhenNotEmpty else "==") + " 0 else ''`";


def genTabStopPrePost(preText, tabStopNum, defaultVal, postText):
    """
    Generate some python to produce a tabstop with some text before, and some
    text after the tabstop if the tabstop isn't empty
    """

    ret = ""

    # Pre text
    if len(preText) > 0:
        ret += snipOptional(tabStopNum, preText)

    # Tab stop
    if defaultVal and len(defaultVal) > 0:
        ret += "${" + str(tabStopNum) + ":" + defaultVal + "}"
    else:
        ret += "$" + str(tabStopNum)

    # Post text
    if len(postText) > 0:
        ret += snipOptional(tabStopNum, postText)

    return ret

def extractClassSectionAnywhere(className, section):
    """
    Use 'parseutil.extractClassSection' to attempt to find the specified
    'section' of the specified 'class'.  If it's not found in the current
    file, and the current file is a .cpp, open the corresponding .h and try to
    find it there before giving up.
    """

    def lineGen():
        for line in range(0, len(vim.current.buffer)):
            yield vim.current.buffer[line]

    content = parseutil.extractClassSection(lineGen(), className, section)
    if content != None:
        return content

    # See if we can load the header,  and find the section there
    bufName = vim.current.buffer.name
    if not bufName.endswith(".cpp"):
        return None

    bufName = bufName.replace(".cpp", ".h")
    try:
        with open(bufName) as f:
            def hLineGen():
                for line in f:
                    yield line.rstrip("\n")

            content = parseutil.extractClassSection(hLineGen(),
                                                    className,
                                                    section)
    except e:
        # File doesn't exist.  Do nothing; content will remain None
        pass

    return content

def genCctorSnippet(classname, memberDefs):
    """
    Generate a snippet for a copy constructor of the specified 'classname',
    using the optionally specified 'memberDefs' as the member variable
    definitions.
    """
    lines = [genTabStopPrePost("", 1, classname, "")+\
        "::$1(const $1& other" + \
        genTabStopPrePost(
                       ", bslma::Allocator *", 2, "basicAllocator", " = 0") + \
        ")"]

    snipNum = 3
    separator = ": "
    for typeName, mem in parseutil.parseMembers(memberDefs):
        snipLine = separator
        snipLine += mem + "(other." + mem
        snipLine += genTabStopPrePost(", ", snipNum, "$2", "")
        snipLine += ")"
        lines.append(snipLine)

        separator = ", "
        snipNum += 1

    lines.append("{")
    lines.append("}")

    return "\n".join(lines)

def genCtorMemSnippet(memberDefs, separator):
    """
    Generate a snippet for initializing member variables from the specified
    'memberDefs' class member definition section, using the specified
    'separator' as the separator to put before the first variable.
    """

    lines = []
    snipNum = 1
    for typeName, mem in parseutil.parseMembers(memberDefs):
        snipLine = separator
        snipLine += mem + ("($%d" % snipNum)
        snipLine += ")"
        lines.append(snipLine)

        snipNum += 1
        separator = ", "

    return "\n".join(lines)

def genDefSnippet(classname, decls, inHeader):
    """
    Generate a snippet for the definitions of the specified 'decls' of the
    specified 'classname'.  If the specified 'inHeader' is 'True', prepend
    each definition with an 'inline'.
    """

    parsedMembers = parseutil.parseFuncDeclarations(decls)

    # Generate the snippet, with a tab stop inside of each function
    snipLines = []
    snipNum = 1
    for mem in parsedMembers:
        if inHeader:
            snipLines.append("inline")

        if isinstance(mem, tuple):
            snipLine = mem[0]
            if mem[0][-1] != "*":
                snipLine += " "
            snipLine += classname + "::" + mem[1]

            openParenPos = len(snipLine)

            snipLine += mem[2]

            suffix = mem[3][:-1].replace("= 0", "")
            if len(suffix) > 0:
                snipLine += " " + suffix

            if mem[2] != "()":
                def lineSource(lineNum):
                    return snipLine if lineNum == 1 else "// ACCESSORS"

                formatRet = bdeformatutil.formatBde(lineSource,
                                                    1,
                                                    openParenPos+1)

                snipLines += formatRet[1]
            else:
                snipLines.append(snipLine)
        else:
            snipLines.append(mem)

        snipLines.append("{")
        snipLines.append("    $%d" % snipNum)
        snipLines.append("}")
        snipLines.append("")

        snipNum += 1

    return "\n".join(snipLines)

def genAccessorDeclSnippet(typeName, cleanName, snipNum):
    line = "    " + snipOptional(snipNum, "const ") + typeName
    if typeName[-1] != "*":
        line += genTabStopPrePost("", snipNum, "&", "") + " "
    else:
        line += genTabStopPrePost("", snipNum, "&", " ")

    line += cleanName + "() const;\n"

    # Add comment
    refComment = s_commentTextwrap.fill(
        ("Return a reference providing const access to the '%s' " + \
         "property of this object.") % cleanName)
    noRefComment = s_commentTextwrap.fill(
        "Return the '%s' property of this object." % cleanName)

    line += snipOptional(snipNum, refComment, True) + \
            snipOptional(snipNum, noRefComment, False)

    return line

def genManipulatorDeclSnippet(typeName, cleanName, snipNum):
    line = "    " +  typeName + "& " + cleanName + "();\n"

    # Add comment
    line += s_commentTextwrap.fill(
        ("Return a reference providing modifiable access to the '%s' " + \
        "property of this object.") % cleanName)

    return line

def genSetterDeclSnippet(typeName, cleanName, snipNum):
    line = "    void set" + cleanName[0].upper() + cleanName[1:]
    line += "(" + snipOptional(snipNum, "const ") + typeName
    if typeName[-1] != "*":
        line += genTabStopPrePost("", snipNum, "&", "") + " "
    else:
        line += genTabStopPrePost("", snipNum, "&", " ")

    line += "value);\n"

    # Add comment
    line += s_commentTextwrap.fill(
        ("Set the value of the '%s' property of this object to the " + \
         "specified 'value'.") % cleanName)

    return line

def genDeclSnippet(classname, memberDefs, funcSnipGen):
    # Generate a snippet for accessors

    snipLines = []
    snipNum = 2
    for typeName, mem in parseutil.parseMembers(memberDefs):
        cleanName = re.match(r'd_([^_]*)_?p?', mem).group(1)

        line = ""
        if snipNum > 2:
            line += "}"
        line += "${%d:" % (snipNum - 1)
        line += funcSnipGen(typeName, cleanName, snipNum)
        #line += genAccessorDeclSnippet(typeName, cleanName, snipNum)
        snipLines.append(line)

        snipLines.append("")

        snipNum += 2

    snipLines.append("}")

    return "\n".join(snipLines)
