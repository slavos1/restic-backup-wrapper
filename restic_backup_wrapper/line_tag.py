"""
{% line %}
this
text
will
be
one line after
{% endline %}

{% linex %}
echo  -e 'a, b'
{% endlinex %}

will be (removed spaces)
echo -e 'a, b'
"""
import re
import shlex

from jinja2 import nodes
from jinja2.ext import Extension


def _make_one_line(s: str) -> str:
    return re.sub("[\n\r]+", " ", s.strip()) if s else ""


class OneLineExtension(Extension):
    tags = {"line"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(["name:endline"], drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_make_one_line", [], None, None), [], [], body
        ).set_lineno(lineno)

    def _make_one_line(self, caller):
        return _make_one_line(caller()).rstrip()


class OneLineShlexExtension(Extension):
    tags = {"linex"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(["name:endlinex"], drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_make_one_line", [], None, None), [], [], body
        ).set_lineno(lineno)

    def _make_one_line(self, caller):
        return shlex.join(shlex.split(_make_one_line(caller())))
