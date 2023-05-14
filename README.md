# parserLLM

Use a context-free grammar and a parser generator to determine valid next tokens for an LLM generation. 

Extending [ReLLM](https://github.com/r2d4/rellm) to handle context-free grammars in addition to regular expressions.

### Usage

```bash
pip install parserllm
```

See [examples/example.py](examples/example.py) for an example of how to use this library. 

Run it with `python examples/example.py`.

### How does it work?

See this [ post](https://matt-rickard.com/context-free-grammar-parsing-with-llms) for a more in-depth explanation.

The general strategy goes like this:

First, define a context-free grammar. You might use this for a simplified version of JSON (in EBNF form):
```ebnf
?start: value

    ?value: object

          | array

          | string

          | "true"             -> true

          | "false"            -> false

          | "null"             -> null

    array  : "[" [value ("," value)*] "]"

    object : "{" [pair ("," pair)*] "}"

    pair   : string ":" value

    string : ESCAPED_STRING

    %import common.ESCAPED_STRING

    %import common.SIGNED_NUMBER

    %import common.WS

    %ignore WS
```
Next, to practically support multiple CFGs, use a parser generator to parse the language. This library uses Lark, simply because it’s written in Python and fairly easy to use.

Next, run the partial output through the parser generator. At step zero, this is just the empty string. The parser will return all of the possible next tokens. You can see the valid first completion of this grammar is any “value,” which can be an array, string, true/false, or null. This means the valid starting tokens are `{`, `[`, `”`, `true`, `false`, and `null`.

Ncompile those tokens to their regular expressions. Now we have an equivalent problem to [ReLLM](https://github.com/r2d4/rellm). Simply run the regexps through ReLLM to generate the next possible token. ReLLM will squash the logits of the non-matching characters and the LLM will only consider valid partial or full next tokens.

Iterate until max tokens are reached, or the parser sees only an empty string or stop token as the next token.

Some interesting features:

- You can describe the syntax of most programming and configuration languages as a CFG.
- The LLM won’t produce an invalid result, but there’s no guarantee it will finish and produce a stop token.