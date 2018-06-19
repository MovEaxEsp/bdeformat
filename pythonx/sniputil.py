""""
sniptil.py: Utility functions for building bdeformat snippets

This module defines functions that are used to generate UltiSnip snippets for
various BDE-style portions of C++.
"""

import bdeformatutil
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
    empty, as determined by the specified 'expandWhenNotEmpty'.
    """

    if not text or len(text) == 0:
        return "";

    if not isinstance(snipNum, list):
        snipNum = [snipNum]

    op = ">" if not expandWhenNotEmpty else "=="
    innerCondition = "filter(lambda x: x %s 0, [len(t[num]) for num in %s])" \
            % (">" if not expandWhenNotEmpty else "==",
               str(snipNum))

    return "`!p snip.rv = \"\"\"%s\"\"\" if len(list(%s)) == 0 else ''`" \
                                                       % (text, innerCondition)

def genTabStop(tabStopNum, defaultVal=None, pre=None, post=None):
    """
    Generate some python to produce a tabstop with some text before, and some
    text after the tabstop if the tabstop isn't empty
    """

    ret = ""

    # Pre text
    ret += snipOptional(tabStopNum, pre)

    # Tab stop
    if defaultVal and len(defaultVal) > 0:
        ret += "${" + str(tabStopNum) + ":" + defaultVal + "}"
    else:
        ret += "$" + str(tabStopNum)

    # Post text
    ret += snipOptional(tabStopNum, post)

    return ret

def genCctorSnippet(classname, memberDefs):
    """
    Generate a snippet for a copy constructor of the specified 'classname',
    using the optionally specified 'memberDefs' as the member variable
    definitions.
    """
    lines = [genTabStop(1, classname) + "::$1(const $1& other" + \
             genTabStop(2, "basicAllocator", pre=", bslma::Allocator *",
                                             post = " = 0") +  ")"]

    snipNum = 3
    separator = ": "
    for typeName, mem in parseutil.parseMembers(memberDefs):
        snipLine = separator
        snipLine += mem + "(other." + mem
        snipLine += genTabStop(snipNum, "$2", pre=", ")
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

def genCtorInitializerList(className, argTypes, memberDefs, snipNum):
    """
    Generate a snippet for the initializer list of a constructor definition
    for a class with the specified 'className', the specified argument name to
    type map 'argTypes' and the specified member variable declaration section
    'memberDefs', starting snippet tab stops with the specified 'snipNum'.
    Return a tuple containing the generated snippet and the next snipNum after
    the last one used by this function.
    """

    # Figure out if this is a copy constructor
    cctorOtherArg = None
    cctorOtherType = "const %s&" % className
    for argName, argType in argTypes.items():
        if argType == cctorOtherType:
            cctorOtherArg = argName
            break

    # Find the allocator arg, if any
    allocName = None
    if "allocator" in argTypes:
        allocName = "allocator"
    elif "basicAllocator" in argTypes:
        allocName = "basicAllocator"

    lines = []

    separator = ": "
    for typeName, mem in parseutil.parseMembers(memberDefs):
        snipLine = separator
        separator = ", "
        snipLine += mem + "("

        # Figure out what the default arg should be
        defArg = None

        genAllocTabStop = True
        if allocName and typeName  == "bslma::Allocator *":
            defArg = "bslma::Default::allocator(%s)" % allocName
            genAllocTabStop = False

        if not defArg and cctorOtherArg:
            defArg = "%s.%s" % (cctorOtherArg, mem)

        if not defArg:
            cleanNameMatch = re.match(r'd_([^_]*)_?p?', mem)
            if cleanNameMatch and cleanNameMatch.group(1) in argTypes:
                defArg = cleanNameMatch.group(1)

        argSnip = snipNum
        snipNum += 1
        snipLine += genTabStop(argSnip, defArg)

        if allocName and genAllocTabStop:
            allocSnip = snipNum
            snipNum += 1
            snipLine += snipOptional([argSnip, allocSnip], ", ")
            snipLine += genTabStop(allocSnip, allocName)

        snipLine += ")"
        lines.append(snipLine)

    return ("\n".join(lines), snipNum)

def genDefSnippet(classname, decls, inHeader, memberDefs=""):
    """
    Generate a snippet for the definitions of the specified 'decls' of the
    specified 'classname' with the specified 'memberDefs' member variable
    declarations.  If the specified 'inHeader' is 'True', prepend
    each definition with an 'inline'.
    """

    parsedMembers = parseutil.parseFuncDeclarations(decls)

    # Generate the snippet, with a tab stop inside of each function
    snipLines = []
    snipNum = 1
    for mem in parsedMembers:
        if inHeader:
            snipLines.append("inline")

        if not isinstance(mem, tuple):
            snipLines.append(mem)
            continue

        # Parse out the args
        (funcRetType, funcName, argsStr, funcSuffix) = mem
        declArgsList = parseutil.determineElements(
                                                  argsStr, (0, len(argsStr)-1))

        parsedArgs = parseutil.fixParsedElements(
                             [parseutil.parseElement(e) for e in declArgsList])
        argTypes = {argName: argType + argStars \
                       for (argType, argStars, argName, _, _, _) in parsedArgs}

        # Clean up the suffix
        funcSuffix = re.sub(r';', '', funcSuffix)
        funcSuffix = re.sub(r'=\s*0', '', funcSuffix)
        funcSuffix = funcSuffix.strip()

        # Gen the snippet
        declText = funcRetType
        if len(funcRetType) > 0 and funcRetType[-1] != "*":
            declText += " "

        declText += classname + "::" + funcName + "("
        insideParenPos = len(declText)
        for (argType, argStars, argName, _, _, _) in parsedArgs:
            declText += argType + " " + argStars + " " + argName + ","
        if len(parsedArgs) > 0:
            declText = declText[:-1] # Remove trailing ,

        declText += ")"
        if len(funcSuffix) > 0:
            declText += " " + funcSuffix

        if argsStr != "()":
            def lineSource(lineNum):
                return declText if lineNum == 1 else "// CREATORS"

            snipLines.append("\n".join(
                    bdeformatutil.formatBde(lineSource, 1, insideParenPos)[1]))
        else:
            snipLines.append(declText)

        if classname == funcName:
            # Constructor, so gen initializer list
            initList, snipNum = genCtorInitializerList(classname,
                                                       argTypes,
                                                       memberDefs,
                                                       snipNum)
            snipLines.append(initList)

        snipLines.append("{" + genTabStop(snipNum, "// TODO", pre="\n    "))
        snipLines.append("}")
        snipLines.append("")

        snipNum += 1

    return "\n".join(snipLines)

def genAccessorDeclSnippet(typeName, cleanName, snipNum):
    """
    Generate a snippet for a accessor function definition, i.e. a const
    function that returns either a value or a const reference to a member
    variable of the specific 'typeName' type, with the specified 'cleanName',
    creating any snippets starting at the specified 'snipNum'.  A 'cleanName'
    is the variable name without the leading 'd_' or any trailing '_p'.
    """

    line = "    " + snipOptional(snipNum, "const ") + typeName
    if typeName[-1] != "*":
        line += genTabStop(snipNum, "&") + " "
    else:
        line += genTabStop(snipNum, "&", post=" ")

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
    """
    Generate a snippet for a direct manipulator declaration for a member
    variable of the specified 'typeName' with the specified 'cleanName',
    starting any snippets at the specified 'snipNum'.  A 'cleanName' is the
    variable name without the leading 'd_' or any trailing '_p'.
    """

    line = "    " +  typeName + "& " + cleanName + "();\n"

    # Add comment
    line += s_commentTextwrap.fill(
        ("Return a reference providing modifiable access to the '%s' " + \
        "property of this object.") % cleanName)

    return line

def genSetterDeclSnippet(typeName, cleanName, snipNum):
    """
    Generate a snippet for a setter declaration for a member variable of the
    specified 'typeName' with the specified 'cleanName', starting any snippets
    at the specified 'snipNum'.  A 'cleanName' is the variable name without
    the leading 'd_' or any trailing '_p'.
    """
    line = "    void set" + cleanName[0].upper() + cleanName[1:]
    line += "(" + snipOptional(snipNum, "const ") + typeName
    if typeName[-1] != "*":
        line += genTabStop(snipNum, "&") + " "
    else:
        line += genTabStop(snipNum, "&", post=" ")

    line += "value);\n"

    # Add comment
    line += s_commentTextwrap.fill(
        ("Set the value of the '%s' property of this object to the " + \
         "specified 'value'.") % cleanName)

    return line

def genDeclSnippet(memberDefs, funcSnipGen):
    """
    Generate a snippet for the declarations of functions for the member
    variables defined in the specified 'memberDefs' using the specified
    'funcSnipGen' to generate the snippet for each parsed variable definition.
    """

    snipLines = []
    snipNum = 2
    for typeName, mem in parseutil.parseMembers(memberDefs):
        cleanName = re.match(r'd_([^_]*)_?p?', mem).group(1)

        line = ""
        if snipNum > 2:
            line += "}"
        line += "${%d:" % (snipNum - 1)
        line += funcSnipGen(typeName, cleanName, snipNum)
        snipLines.append(line)

        snipLines.append("")

        snipNum += 2

    snipLines.append("}")

    return "\n".join(snipLines)
