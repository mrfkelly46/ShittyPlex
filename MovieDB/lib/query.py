from pprint import pprint
from enum import Enum


class Query:
    fields = {}

    def __init__(self, model, default_field, default_field_display=None):
        self.model = model
        self.default_field = default_field
        self.default_field_display = default_field_display
        self._setup()
        self.parser = Parser()

    def _setup(self):
        self.fields = {}
        for field in self.model._meta.fields:
            self.fields[field.name] = field

    def get_filters_dict(self, string):
        filters = {}
        chunks = self.parser.parse(string)
        for field, queries in chunks.items():
            field = self._match(field)
            for operator, values in queries.items():
                lookup = field + self._operator(field, operator)
                if len(values) > 1 and field != self.default:
                    raise Exception('Cannot build filters dict for multiple values on "{2}": "{1}"'.format(field, values))
                value = ' '.join(values)
                filters[lookup] = value
        return filters

    def get_query(self, string, query):
        chunks = self.parser.parse(string)
        for field, queries in chunks.items():
            field = self._match(field)
            for operator, values in queries.items():
                lookup = field + self._operator(field, operator)
                for value in values:
                    query = query.filter(**{lookup:value})
        return query

    def get_message(self, string):
        if not string.strip():
            return ''
        message = []
        chunks = self.parser.parse(string)
        for field, queries in chunks.items():
            field = self._match(field)
            if field == self.default_field and self.default_field_display is not None:
                field = self.default_field_display
            for operator, values in queries.items():
                if operator in [':', '=']:
                    if self._is_numeric(field):
                        operator = 'equals'
                    else:
                        operator = 'includes'
                for value in values:
                    message.append('the {0} {1} {2}'.format(field, operator, value))
        return ' and '.join(message)

    def _match(self, field):
        if field == '':
            return self.default_field
        for f in self.fields:
            if f.lower().startswith(field.lower()):
                return f 
        return field

    def _is_numeric(self, field):
        numerics = [
            'IntegerField',
            'DecimalField',
        ]
        return self.fields[field].get_internal_type() in numerics
        
    def _operator(self, field, operator):
        operators = {
            ':': '__icontains',
            '=': '__icontains',
            '>': '__gt',
            '<': '__lt',
            '>=': '__gte',
            '<=': '__lte',
        }
        if operator in ['=', ':'] and self._is_numeric(field):
            return '__exact'
        return operators[operator]
            

        
        
        

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

