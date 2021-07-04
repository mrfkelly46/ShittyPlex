from pprint import pprint
from enum import Enum


class Query:
    fields = {}

    operators = {
        ':': '__icontains',
        '=': '__icontains',
        '>': '__gt',
        '<': '__lt',
        '>=': '__gte',
        '<=': '__lte',
    }

    def __init__(self, model, default):
        self.model = model
        self.default = default
        self._setup()
        self.parser = Parser()

    def _setup(self):
        self.fields = {}
        for field in self.model._meta.fields:
            self.fields[field.name] = field

    def build(self, query):
        filters = {}
        chunks = self.parser.parse(query)
        for field, queries in chunks.items():
            field = self._match(field)
            for operator, values in queries.items():
                lookup = field + self.operators[operator]
                if len(values) > 1 and field != self.default:
                    raise Exception('Currently cannot query "{0}" on multiple values: "{1}"'.format(field, values))
                value = ' '.join(values)
                filters[lookup] = value
        return filters
        
    def _match(self, field):
        if field == '':
            return self.default
        for f in self.fields:
            if f.lower().startswith(field.lower()):
                return f 
        

class ParserStep(Enum):
    field = 1
    separator = 2
    value = 3
    done = 4


class ParserException(Exception):
    pass
    

class Parser:

    SEPARATORS = [':', '=', '>', '<']
    QUOTES = ['"', '\'']

    def __init__(self, fields=None, separators=None, quotes=None):
        self.fields = fields or {}
        # TODO: Rather than pass in dict, do we want to inherit this Parser object and have the user 
        #       create their own Parser with fields set by them, ala Django/SQLAlchemy models? then they
        #       set fields (and accepted alternatives) there, among(us) other things e.g. is int (year), double (rating),
        #       ... or set if field accepts >/</>=/<= 
        for target, children in self.fields.items():
            target = target.lower()
            if target not in self.fields:
                self.fields[target] = [child.lower() for child in children]

        self.separators = separators
        if not self.separators:
            self.separators = self.SEPARATORS

        self.quotes = quotes
        if not self.quotes:
            self.quotes = self.QUOTES

        self.chunks = {}

    def parse(self, query):
        self.chunks = {}

        field = []
        separator = []
        value = []

        step = ParserStep.field
        quoted_by = None

        for index, c in enumerate(query.strip()):
            # print(index, c, field, value, step)
            if step is ParserStep.done:
                self._add(''.join(field), ''.join(separator), ''.join(value))
                field = []
                separator = []
                value = []
                step = ParserStep.field

            if step is ParserStep.field:
                if c in self.separators:
                    step = ParserStep.separator
                    separator.append(c)
                    if not field:
                        raise ParserException('Missing field name at position {0}'.format(index))
                    continue
                    
                if not field and c.isspace():
                    continue

                if not c.isspace():
                    field.append(c)

                if field and c.isspace():
                    # Found value on its own, save as default=value and continue
                    self._add('', '=', ''.join(field))
                    field = []
                    
                continue

            if step is ParserStep.separator:
                if c in self.separators:
                    separator.append(c)
                else:
                    step = ParserStep.value

            if step is ParserStep.value:
                if not value and c in self.quotes:
                    quoted_by = c
                    continue
                if quoted_by and c == quoted_by:
                    quoted_by = None
                    step = ParserStep.done
                    continue
                if not quoted_by and c.isspace():
                    step = ParserStep.done
                    continue
                value.append(c)
                continue

        if field and not separator and not value:
            # Found value on its own, save as default=value and continue
            self._add('', '=', ''.join(field))
        else:
            self._add(''.join(field), ''.join(separator), ''.join(value))

        return self.chunks

    def _add(self, field, separator, value):
        field = field.lower()
        # for parent, children in self.groups.items():
        #     if field in children
        if field not in self.chunks:
            self.chunks[field] = {}
        if separator not in self.chunks[field]:
            self.chunks[field][separator] = []
        self.chunks[field][separator].append(value)

    def __repr__(self):
        string = '{\n'
        for field, values in self.chunks.items():
            string += '\t"{0}":\n'.format(field)
            for value in values:
                string += '\t\t"{0}"\n'.format(value)
            string += '\n'
        string += '}'
        return string
        

def main():
    test = input("Query String: ")
    parser = Parser()
    chunks = parser.parse(test)
    pprint(chunks)


if __name__ == '__main__':
    main()
