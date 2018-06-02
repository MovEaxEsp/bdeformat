import string
import vim
import parseutil

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
