""""
sniptil.py: Utility functions for building/writing snippets

This module defines a number of functions that are useful either in the
process of writing UltiSnips snippets, or that generate snippets themselves.
"""

import bdeformatutil
import string
import vim
import parseutil
from sectiontype import SectionType

def copyright():
    import datetime
    return """// ----------------------------------------------------------------------------
// NOTICE:
//      Copyright (C) Bloomberg L.P., {0}
//      All Rights Reserved.
//      Property of Bloomberg L.P. (BLP)
//      This software is made available solely pursuant to the
//      terms of a BLP license agreement which governs its use.
// ------------------------------ END-OF-FILE ---------------------------------""".format(datetime.date.today().year)

def getFtCommentStr(ft = None):
    """
    Get the comment string for the specified 'ft', or for the filetype of the
    current vim buffer if 'ft == None'
    """

    if not ft:
        ft = vim.current.buffer.options['ft']

    if ft == "c" or ft == "cpp" or ft == "javascript":
        return "// "
    elif ft == "python":
        return "# "
    else:
        # Most other things use # (I think)
        return "# "

def rightAlign(width, text):
    return (width - len(text))*' ' + text

def centerPadding(text):
    """
    Return the padding necessary to center the specified 'text' in a line 79
    chars wide.
    """
    return ' ' * int(39 - (len(text))/2)

def centerBorder(border, text, commentStr="// "):
    """
    Return the border consisting of the specified 'border' character,
    beginning with the specified 'commentStr' for the specified 'text'
    centered in a line 79 chars wide.
    """
    return centerPadding(commentStr + text) + commentStr + border*len(text)

def centerComment(text, commentStr="// "):
    """
    Return the beginning of a centered comment, i.e. the padding and the
    specified 'commentStr' characters needed to center the specified 'text' in
    a line 79 chars wide.
    """
    return centerPadding(commentStr + text) + commentStr

def header(border, text):
    lines = [
        centerBorder(border, text),
        centerComment(text) + text,
        centerBorder(border, text)]
    return "\n".join(lines)


def classDef(name):
    """
    Return the class definition for a class with the specified 'name'.
    """

    template = string.Template("""class $name {
    // TODO

  private:
    // DATA

    // NOT IMPLEMENTED
    $name(const $name&);
    $name& operator=(const $name&);

  public:
    // TRAITS
    BSLMF_NESTED_TRAIT_DECLARATION($name,
                                   bslma::UsesBslmaAllocator);

    // CREATORS
    explicit $name(bslma::Allocator *basicAllocator = 0);

    // MANIPULATORS

    // ACCESSORS
};""")

    return template.safe_substitute({"name":name})

def structDef(name):
    """
    Return the definition for a struct with the specified 'name'.
    """

    template = string.Template("""struct $name {
    // TODO

  public:
    // PUBLIC DATA

    // NOT IMPLEMENTED
    $name(const $name&);
    $name& operator=(const $name&);

  public:
    // TRAITS
    BSLMF_NESTED_TRAIT_DECLARATION($name,
                                   bslma::UsesBslmaAllocator);

    // CREATORS
    explicit $name(bslma::Allocator *basicAllocator = 0);

    // MANIPULATORS

    // ACCESSORS
};""")

    return template.safe_substitute({"name":name})

def utilDef(name):
    """
    Return the definition for a utility struct with the specified 'name'.
    """

    template = string.Template("""struct $name {
    // TODO

    // CLASS METHODS
};""")

    return template.safe_substitute({"name":name})

def protocolDef(name):
    """
    Return the definition of a protocol class with the specified 'name'.
    """

    template = string.Template("""class $name {

  public:
    // CREATORS
    virtual ~$name();

    // MANIPULATORS
};""")

    return template.safe_substitute({"name":name})

def enumDef(name):
    """
    Return the definition of an enum struct with the specified 'name'.
    """

    template = string.Template("""struct $name {

    enum Enum {

    };
};""")

    return template.safe_substitute({"name":name})

def genTabStopPrePost(preText, tabStopNum, defaultVal, postText):
    """
    Generate some python to produce a tabstop with some text before, and some
    text after the tabstop if the tabstop isn't empty
    """

    ret = ""

    # Pre text
    if len(preText) > 0:
        ret += "`!p snip.rv = '" + preText + "' " + \
                "if len(t[" + str(tabStopNum) + "]) > 0 else ''`";

    # Tab stop
    if defaultVal and len(defaultVal) > 0:
        ret += "${" + str(tabStopNum) + ":" + defaultVal + "}"
    else:
        ret += "$" + str(tabStopNum)

    # Post text
    if len(postText) > 0:
        ret += "`!p snip.rv = '" + postText + "' " + \
                "if len(t[" + str(tabStopNum) + "]) > 0 else ''`";

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
    for mem in parseutil.parseMembers(memberDefs):
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
    for mem in parseutil.parseMembers(memberDefs):
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
