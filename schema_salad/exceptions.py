class SchemaSaladException(Exception):
    """Base class for all schema-salad exceptions."""

    def __init__(self, msg, sl = None, children = [], bullet = ""):
        super(SchemaSaladException, self).__init__(msg)
        self.children = children
        self.bullet = bullet if len(children) > 1 else ""
        self.with_sourceline(sl)
        self.message = self.args[0]
        self.propagate_sourceline()

    def propagate_sourceline(self):
        if self.file is None:
            return
        for c in self.children:
            if c.file is None:
                c.file = self.file
                c.start = self.start
                c.end = self.end
                c.propagate_sourceline()

    def with_sourceline(self, sl):
        if sl:
            self.file = sl.file()
            self.start = (sl.line(), sl.column())
            self.end = (sl.line(), sl.column()+1)
        else:
            self.file = None
            self.start = None
            self.end = None
        return self

    def prefix(self):
        if self.file:
            return "{}:{}:{}:".format(self.file, self.start[0], self.start[1])
        else:
            return ""

    def __str__(self):
        return self.pretty_str()

    def pretty_str(self, level=0, bullet = ""):
        indent_per_level = 2
        ret = ""
        next_level = level+1
        spaces = (level*indent_per_level)*" "
        print("MSG: `{}`, level: {}, #spaces: {}".format(self.message, level, (level*indent_per_level)))
        if len(self.message):
            if self.file:
                ret = "{}:{}:{}:{}{} {}".format(self.file, self.start[0], self.start[1],
                                                spaces, bullet, self.message)
            else:
                ret = "{}{} {}".format(spaces, bullet, self.message)
        else:
            next_level = level

        return "\n".join((e for e in [ret, *[c.pretty_str(next_level, self.bullet) for c in self.children]] if len(e)))


class SchemaException(SchemaSaladException):
    """Indicates error with the provided schema definition."""

    pass


class ValidationException(SchemaSaladException):
    """Indicates error with document against the provided schema."""

    pass


class ClassValidationException(ValidationException):
    pass
