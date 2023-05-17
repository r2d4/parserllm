
import regex
from lark import UnexpectedInput, Lark
from rellm import complete_re
from transformers import PreTrainedModel, PreTrainedTokenizer


def extract_terminal_regex(parser, stop_token):
    regex_map = {}
    for term in parser.terminals:
        if term.pattern:
            regex_map[term.name] = regex.compile(term.pattern.to_regexp())
    
    regex_map['$END'] = regex.compile(stop_token)
    return regex_map

class ParserState():
    def __init__(self, parser:Lark):
        self.parser:Lark = parser
        self.partial_token = ""
    
    def next_lex(self, input_str):
        try:
            self.parser.parse(input_str)
        except UnexpectedInput as e:
            # Assuming that self.parser is always LALR
            interactive = self.parser.parse_interactive(input_str)
            interactive.exhaust_lexer()
            return interactive.accepts()
 
        return []

def complete_cf(prompt:str, parser, partial_completion, tokenizer: PreTrainedTokenizer, 
                model: PreTrainedModel, max_new_tokens: int = 3, 
                debug: bool = False,
                **model_kwargs):
    """
    Complete a prompt with a regex pattern.
    """
    gen_tokens = 0
    prompt_plus_completion = prompt + partial_completion

    terminal_regexes = extract_terminal_regex(parser, tokenizer.decode(tokenizer.eos_token_id))
    parser_state = ParserState(parser )
    
    while gen_tokens < max_new_tokens:
        valid_next_lex = parser_state.next_lex(partial_completion)
        if len(valid_next_lex) == 0 or (len(valid_next_lex) == 1 and '$END' in valid_next_lex):
            break
        r = [terminal_regexes[t] for t in valid_next_lex]
        if debug:print(f"valid next token: {r}")
        next_token_completion = complete_re(prompt_plus_completion, r, tokenizer, model, max_new_tokens=max_new_tokens, stop_after_match=True, debug=debug, **model_kwargs)
        partial_completion += next_token_completion
        prompt_plus_completion = prompt_plus_completion + next_token_completion
        gen_tokens += 1

    return partial_completion
