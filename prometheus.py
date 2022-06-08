import re
from pygments.token import Token
from pygments_promql import PromQLLexer

lexer = PromQLLexer()

# Simple class to represent labels filtering
class LabelFiltering():
    def __init__(self, key, value):
        self.key = key
        self.value = value
    def __str__(self):
        return f"{self.key}=\"{self.value}\""

# parse the promql query and a set of all variables
def parse_variables(promql_expr: str):
    return set([i[1] for i in lexer.get_tokens(promql_expr) if i[0] == Token.Name.Variable ])

# add_filter add a filter to a promql expression.
#  It doesn't validate the input expression. 
def add_filter(promql_expr: str, filter: LabelFiltering):
    variables = parse_variables(promql_expr)
    for v in variables:
        variable_extraction_re =  r"([^a-zA-Z0-9_:]|^)({})([^a-zA-Z0-9_:]|$)".format(v)
        promql_expr = re.sub(variable_extraction_re, 
            r"\1{}{}\3".format(v, '{' + str(filter) + '}'), 
            promql_expr)
    # Sanitize the query `}{` -> `,` because of the upper regex.
    return re.sub(r'}[ \t\n]*{', ',', promql_expr)
