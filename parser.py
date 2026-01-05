# Amir Hossein Ravan Nakhjavani - 400104975
# Maedeh Heydari - 400104918

from scanner import Scanner
from tokens import Token, TokenType


class ParseNode:
    """Represents a node in the parse tree."""
    def __init__(self, name: str, is_terminal: bool = False):
        self.name = name
        self.is_terminal = is_terminal
        self.children = []
    
    def add_child(self, child):
        # Skip None children (from failed match attempts)
        if child is not None:
            self.children.append(child)
    
    def to_string(self, prefix: str = "", is_root: bool = True, is_last: bool = True) -> str:
        """Convert parse tree to required string format with tree-drawing characters."""
        result = ""
        
        # For root node (no prefix)
        if is_root:
            result = self.name + "\n"
            # Root's children use ├── for all except last which uses └──
            for i, child in enumerate(self.children):
                is_last_child = (i == len(self.children) - 1)
                result += child.to_string("", False, is_last_child)
        else:
            # Use tree-drawing characters
            connector = "└── " if is_last else "├── "
            result = prefix + connector + self.name + "\n"
            
            # Prepare prefix for children
            extension = "    " if is_last else "│   "
            new_prefix = prefix + extension
            
            for i, child in enumerate(self.children):
                is_last_child = (i == len(self.children) - 1)
                result += child.to_string(new_prefix, False, is_last_child)
        
        return result


class Parser:
    """Predictive Recursive Descent Parser for C-minus."""
    
    def __init__(self, scanner: Scanner):
        self.scanner = scanner
        self.current_token = None
        self.syntax_errors = []
        self.parse_tree = None
        self.eof_error_reported = False
        self.unexpected_eof = False
        
        # First sets for non-terminals (from first-follow-predict.md)
        self.first_sets = self._init_first_sets()
        
        # Follow sets for non-terminals (from first-follow-predict.md)
        self.follow_sets = self._init_follow_sets()
        
        # Predict sets for productions (from first-follow-predict.md)
        self.predict_sets = self._init_predict_sets()
    
    def _init_first_sets(self):
        """Initialize First sets from first-follow-predict.md."""
        return {
            "Program": {"int", "void", "ε"},
            "Declaration-list": {"int", "void", "ε"},
            "Declaration": {"int", "void"},
            "Declaration-initial": {"int", "void"},
            "Declaration-prime": {"[", "("},
            "Var-declaration-prime": {"["},
            "Fun-declaration-prime": {"("},
            "Type-specifier": {"int", "void"},
            "Params": {"int", "void"},
            "Param-list": {",", "ε"},
            "Param": {"int", "void"},
            "Param-prime": {"[", "ε"},
            "Compound-stmt": {"{"},
            "Statement-list": {"ID", "NUM", ";", "(", "{", "break", "if", "for", "return", "+", "-", "ε"},
            "Statement": {"ID", "NUM", ";", "(", "{", "break", "if", "for", "return", "+", "-"},
            "Expression-stmt": {"ID", "NUM", ";", "(", "break", "+", "-"},
            "Selection-stmt": {"if"},
            "Else-stmt": {"else", "ε"},
            "Iteration-stmt": {"for"},
            "Return-stmt": {"return"},
            "Return-stmt-prime": {"ID", "NUM", ";", "(", "+", "-"},
            "Expression": {"ID", "NUM", "(", "+", "-"},
            "B": {"[", "(", "=", "==", "<", "+", "*", "/", "-", "ε"},
            "H": {"(", "=", "==", "<", "+", "*", "/", "-", "ε"},
            "Simple-expression-zegond": {"NUM", "(", "+", "-"},
            "Simple-expression-prime": {"(", "==", "<", "+", "*", "/", "-", "ε"},
            "C": {"==", "<", "ε"},
            "Relop": {"==", "<"},
            "Additive-expression": {"ID", "NUM", "(", "+", "-"},
            "Additive-expression-prime": {"(", "+", "*", "/", "-", "ε"},
            "Additive-expression-zegond": {"NUM", "(", "+", "-"},
            "D": {"+", "-", "ε"},
            "Addop": {"+", "-"},
            "Term": {"ID", "NUM", "(", "+", "-"},
            "Term-prime": {"(", "*", "/", "ε"},
            "Term-zegond": {"NUM", "(", "+", "-"},
            "G": {"*", "/", "ε"},
            "Signed-factor": {"ID", "NUM", "(", "+", "-"},
            "Signed-factor-zegond": {"NUM", "(", "+", "-"},
            "Factor": {"ID", "NUM", "("},
            "Var-call-prime": {"[", "(", "ε"},
            "Var-prime": {"[", "ε"},
            "Factor-prime": {"(", "ε"},
            "Factor-zegond": {"NUM", "("},
            "Args": {"ID", "NUM", "(", "+", "-", "ε"},
            "Arg-list": {"ID", "NUM", "(", "+", "-"},
            "Arg-list-prime": {",", "ε"},
        }
    
    def _init_follow_sets(self):
        """Initialize Follow sets from first-follow-predict.md."""
        return {
            "Program": {"$"},
            "Declaration-list": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-", "$"},
            "Declaration": {"ID", "int", "void", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-", "$"},
            "Declaration-initial": {"[", "(", ",", ")"},
            "Declaration-prime": {"ID", "int", "void", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-", "$"},
            "Var-declaration-prime": {"ID", "int", "void", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-", "$"},
            "Fun-declaration-prime": {"ID", "int", "void", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-", "$"},
            "Type-specifier": {"ID"},
            "Params": {")"},
            "Param-list": {")"},
            "Param": {")", ","},
            "Param-prime": {")", ","},
            "Compound-stmt": {"ID", "int", "void", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-", "$"},
            "Statement-list": {"}"},
            "Statement": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            "Expression-stmt": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            "Selection-stmt": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            "Else-stmt": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            "Iteration-stmt": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            "Return-stmt": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            "Return-stmt-prime": {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            "Expression": {"]", ";", ")", ","},
            "B": {"]", ";", ")", ","},
            "H": {"]", ";", ")", ","},
            "Simple-expression-zegond": {"]", ";", ")", ","},
            "Simple-expression-prime": {"]", ";", ")", ","},
            "C": {"]", ";", ")", ","},
            "Relop": {"ID", "NUM", "(", "+", "-"},
            "Additive-expression": {"]", ";", ")", ","},
            "Additive-expression-prime": {"]", ";", ")", ",", "==", "<"},
            "Additive-expression-zegond": {"]", ";", ")", ",", "==", "<"},
            "D": {"]", ";", ")", ",", "==", "<"},
            "Addop": {"ID", "NUM", "(", "+", "-"},
            "Term": {"]", ";", ")", ",", "==", "<", "+", "-"},
            "Term-prime": {"]", ";", ")", ",", "==", "<", "+", "-"},
            "Term-zegond": {"]", ";", ")", ",", "==", "<", "+", "-"},
            "G": {"]", ";", ")", ",", "==", "<", "+", "-"},
            "Signed-factor": {"]", ";", ")", ",", "==", "<", "+", "-", "*", "/"},
            "Signed-factor-zegond": {"]", ";", ")", ",", "==", "<", "+", "-", "*", "/"},
            "Factor": {"]", ";", ")", ",", "==", "<", "+", "-", "*", "/"},
            "Var-call-prime": {"]", ";", ")", ",", "==", "<", "+", "-", "*", "/"},
            "Var-prime": {"]", ";", ")", ",", "==", "<", "+", "-", "*", "/"},
            "Factor-prime": {"]", ";", ")", ",", "==", "<", "+", "-", "*", "/"},
            "Factor-zegond": {"]", ";", ")", ",", "==", "<", "+", "-", "*", "/"},
            "Args": {")"},
            "Arg-list": {")"},
            "Arg-list-prime": {")"},
        }
    
    def _init_predict_sets(self):
        """Initialize Predict sets for each production (from first-follow-predict.md)."""
        return {
            # Program → Declaration-list
            ("Program", 1): {"int", "void", "$"},
            
            # Declaration-list → Declaration Declaration-list
            ("Declaration-list", 2): {"int", "void"},
            # Declaration-list → ε
            ("Declaration-list", 3): {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-", "$"},
            
            # Declaration → Declaration-initial Declaration-prime
            ("Declaration", 4): {"int", "void"},
            
            # Declaration-initial → Type-specifier ID
            ("Declaration-initial", 5): {"int", "void"},
            
            # Declaration-prime → Fun-declaration-prime
            ("Declaration-prime", 6): {"("},
            # Declaration-prime → Var-declaration-prime
            ("Declaration-prime", 7): {"[", ";"},
            
            # Var-declaration-prime → [ NUM ] ;
            ("Var-declaration-prime", 8): {"["},
            # Var-declaration-prime → ;
            ("Var-declaration-prime", 117): {";"},
            
            # Fun-declaration-prime → ( Params ) Compound-stmt
            ("Fun-declaration-prime", 9): {"("},
            
            # Type-specifier → int
            ("Type-specifier", 10): {"int"},
            # Type-specifier → void
            ("Type-specifier", 11): {"void"},
            
            # Params → int ID Param-prime Param-list
            ("Params", 12): {"int"},
            # Params → void
            ("Params", 13): {"void"},
            
            # Param-list → , Param Param-list
            ("Param-list", 14): {","},
            # Param-list → ε
            ("Param-list", 15): {")"},
            
            # Param → Declaration-initial Param-prime
            ("Param", 16): {"int", "void"},
            
            # Param-prime → [ ]
            ("Param-prime", 17): {"["},
            # Param-prime → ε
            ("Param-prime", 18): {")", ","},
            
            # Compound-stmt → { Declaration-list Statement-list }
            ("Compound-stmt", 19): {"{"},
            
            # Statement-list → Statement Statement-list
            ("Statement-list", 20): {"ID", "NUM", ";", "(", "{", "break", "if", "for", "return", "+", "-"},
            # Statement-list → ε
            ("Statement-list", 21): {"}"},
            
            # Statement → Expression-stmt
            ("Statement", 22): {"ID", "NUM", ";", "(", "break", "+", "-"},
            # Statement → Compound-stmt
            ("Statement", 23): {"{"},
            # Statement → Selection-stmt
            ("Statement", 24): {"if"},
            # Statement → Iteration-stmt
            ("Statement", 25): {"for"},
            # Statement → Return-stmt
            ("Statement", 26): {"return"},
            
            # Expression-stmt → Expression ;
            ("Expression-stmt", 27): {"ID", "NUM", "(", "+", "-"},
            # Expression-stmt → break ;
            ("Expression-stmt", 28): {"break"},
            # Expression-stmt → ;
            ("Expression-stmt", 29): {";"},
            
            # Selection-stmt → if ( Expression ) Statement Else-stmt
            ("Selection-stmt", 30): {"if"},
            
            # Else-stmt → else Statement
            ("Else-stmt", 31): {"else"},
            # Else-stmt → ε
            ("Else-stmt", 32): {"ID", "NUM", ";", "(", "{", "}", "break", "if", "else", "for", "return", "+", "-"},
            
            # Iteration-stmt → for ( Expression ; Expression ; Expression ) Compound-stmt
            ("Iteration-stmt", 33): {"for"},
            
            # Return-stmt → return Return-stmt-prime
            ("Return-stmt", 34): {"return"},
            
            # Return-stmt-prime → Expression ;
            ("Return-stmt-prime", 35): {"ID", "NUM", "(", "+", "-"},
            # Return-stmt-prime → ;
            ("Return-stmt-prime", 36): {";"},
            
            # Expression → Simple-expression-zegond
            ("Expression", 37): {"NUM", "(", "+", "-"},
            # Expression → ID B
            ("Expression", 38): {"ID"},
            
            # B → = Expression
            ("B", 39): {"="},
            # B → [ Expression ] H
            ("B", 40): {"["},
            # B → Simple-expression-prime
            ("B", 41): {"]", ";", ")", ",", "(", "==", "<", "+", "*", "/", "-"},
            
            # H → = Expression
            ("H", 42): {"="},
            # H → G D C
            ("H", 43): {"]", ";", ")", ",", "(", "==", "<", "+", "*", "/", "-"},
            
            # Simple-expression-zegond → Additive-expression-zegond C
            ("Simple-expression-zegond", 44): {"NUM", "(", "+", "-"},
            
            # Simple-expression-prime → Additive-expression-prime C
            ("Simple-expression-prime", 45): {"]", ";", ")", ",", "(", "==", "<", "+", "*", "/", "-"},
            
            # C → Relop Additive-expression
            ("C", 46): {"==", "<"},
            # C → ε
            ("C", 47): {"]", ";", ")", ","},
            
            # Relop → ==
            ("Relop", 48): {"=="},
            # Relop → <
            ("Relop", 49): {"<"},
            
            # Additive-expression → Term D
            ("Additive-expression", 50): {"ID", "NUM", "(", "+", "-"},
            
            # Additive-expression-prime → Term-prime D
            ("Additive-expression-prime", 51): {"]", ";", ")", ",", "(", "==", "<", "+", "*", "/", "-"},
            
            # Additive-expression-zegond → Term-zegond D
            ("Additive-expression-zegond", 52): {"NUM", "(", "+", "-"},
            
            # D → Addop Term D
            ("D", 53): {"+", "-"},
            # D → ε
            ("D", 54): {"]", ";", ")", ",", "==", "<"},
            
            # Addop → +
            ("Addop", 55): {"+"},
            # Addop → -
            ("Addop", 62): {"-"},
            
            # Term → Signed-factor G
            ("Term", 56): {"ID", "NUM", "(", "+", "-"},
            
            # Term-prime → Factor-prime G
            ("Term-prime", 57): {"]", ";", ")", ",", "(", "==", "<", "+", "*", "/", "-"},
            
            # Term-zegond → Signed-factor-zegond G
            ("Term-zegond", 58): {"NUM", "(", "+", "-"},
            
            # G → * Signed-factor G
            ("G", 59): {"*"},
            # G → / Signed-factor G
            ("G", 60): {"/"},
            # G → ε
            ("G", 61): {"]", ";", ")", ",", "==", "<", "+", "-"},
            
            # Signed-factor → + Factor
            ("Signed-factor", 65): {"+"},
            # Signed-factor → - Factor
            ("Signed-factor", 66): {"-"},
            # Signed-factor → Factor
            ("Signed-factor", 64): {"ID", "NUM", "("},
            
            # Signed-factor-zegond → + Factor
            ("Signed-factor-zegond", 63): {"+"},
            # Signed-factor-zegond → - Factor
            ("Signed-factor-zegond", 62): {"-"},
            # Signed-factor-zegond → Factor-zegond
            ("Signed-factor-zegond", 67): {"NUM", "("},
            
            # Factor → ( Expression )
            ("Factor", 68): {"("},
            # Factor → ID Var-call-prime
            ("Factor", 69): {"ID"},
            # Factor → NUM
            ("Factor", 70): {"NUM"},
            
            # Var-call-prime → ( Args )
            ("Var-call-prime", 71): {"("},
            # Var-call-prime → Var-prime
            ("Var-call-prime", 72): {"]", ";", ")", ",", "==", "<", "+", "*", "/", "-", "["},
            
            # Var-prime → [ Expression ]
            ("Var-prime", 73): {"["},
            # Var-prime → ε
            ("Var-prime", 74): {"]", ";", ")", ",", "==", "<", "+", "*", "/", "-"},
            
            # Factor-prime → ( Args )
            ("Factor-prime", 75): {"("},
            # Factor-prime → ε
            ("Factor-prime", 76): {"]", ";", ")", ",", "==", "<", "+", "*", "/", "-"},
            
            # Factor-zegond → ( Expression )
            ("Factor-zegond", 77): {"("},
            # Factor-zegond → NUM
            ("Factor-zegond", 78): {"NUM"},
            
            # Args → Arg-list
            ("Args", 79): {"ID", "NUM", "(", "+", "-"},
            # Args → ε
            ("Args", 80): {")"},
            
            # Arg-list → Expression Arg-list-prime
            ("Arg-list", 81): {"ID", "NUM", "(", "+", "-"},
            
            # Arg-list-prime → , Expression Arg-list-prime
            ("Arg-list-prime", 82): {","},
            # Arg-list-prime → ε
            ("Arg-list-prime", 83): {")"},
        }
    
    def _get_token_string(self, token: Token) -> str:
        """Get token string for matching (keyword/symbol literal or token type)."""
        if token.token_type == TokenType.KEYWORD:
            return token.token_string
        elif token.token_type == TokenType.SYMBOL:
            return token.token_string
        elif token.token_type == TokenType.ID:
            return "ID"
        elif token.token_type == TokenType.NUMBER:
            return "NUM"
        elif token.token_type == TokenType.EOF:
            return "$"
        return token.token_string
    
    def _get_predict_production(self, non_terminal: str, lookahead: str):
        """Find which production to use based on predict sets."""
        for (nt, prod_num), tokens in self.predict_sets.items():
            if nt == non_terminal and lookahead in tokens:
                return prod_num
        return None
    
    def _add_error(self, message: str):
        """Add a syntax error to the error list."""
        line_num = self.current_token.line_number if self.current_token else 1
        self.syntax_errors.append(f"#{line_num} : syntax error, {message}")
    
    def _check_first_follow(self, non_terminal: str):
        """
        General panic mode handler for non-terminals.
        Returns: 'proceed', 'skip', or 'discard'
        """
        if self.unexpected_eof:
            return 'skip'
        
        lookahead = self._get_token_string(self.current_token)
        
        # If lookahead is in FIRST set, proceed normally
        if lookahead in self.first_sets.get(non_terminal, set()):
            return 'proceed'
        
        # Otherwise, panic mode (no table entry)
        if lookahead in self.follow_sets.get(non_terminal, set()):
            # Report missing and pop (don't add to tree)
            self._add_error(f"missing {non_terminal}")
            return 'skip'
        elif lookahead == "$":
            # Unexpected EOF - report once and stop parsing
            if not self.eof_error_reported:
                self._add_error("Unexpected EOF")
                self.eof_error_reported = True
            self.unexpected_eof = True
            return 'skip'
        else:
            # Report illegal and discard ONE token
            self._add_error(f"illegal {lookahead}")
            self.current_token = self.scanner.get_next_token()
            # After discarding, check if we hit EOF
            if self._get_token_string(self.current_token) == "$":
                if not self.eof_error_reported:
                    self._add_error("Unexpected EOF")
                    self.eof_error_reported = True
                self.unexpected_eof = True
                return 'skip'
            return 'discard'  # Caller should retry
    
    def match(self, expected: str) -> ParseNode:
        """Match a terminal symbol."""
        if self.unexpected_eof:
            return None
        
        token_str = self._get_token_string(self.current_token)
        
        if token_str == expected:
            # Create terminal node with token format
            if self.current_token.token_type == TokenType.ID:
                node = ParseNode(f"(ID, {self.current_token.token_string})", is_terminal=True)
            elif self.current_token.token_type == TokenType.NUMBER:
                node = ParseNode(f"(NUM, {self.current_token.token_string})", is_terminal=True)
            elif self.current_token.token_type == TokenType.KEYWORD:
                node = ParseNode(f"(KEYWORD, {self.current_token.token_string})", is_terminal=True)
            elif self.current_token.token_type == TokenType.SYMBOL:
                node = ParseNode(f"(SYMBOL, {self.current_token.token_string})", is_terminal=True)
            else:
                node = ParseNode(f"{self.current_token.token_string}", is_terminal=True)
            
            # Get next token
            self.current_token = self.scanner.get_next_token()
            return node
        else:
            # Terminal mismatch - Panic Mode
            if token_str == "$":
                if not self.eof_error_reported:
                    self._add_error("Unexpected EOF")
                    self.eof_error_reported = True
                self.unexpected_eof = True
            else:
                self._add_error(f"missing {expected}")
            # Don't consume token, return None (no node added)
            return None
    
    def parse(self) -> tuple[ParseNode, list[str]]:
        """Main parsing function."""
        # Get first token
        self.current_token = self.scanner.get_next_token()
        
        # Start parsing from the start symbol
        self.parse_tree = self.program()
        
        # Return parse tree and errors
        return self.parse_tree, self.syntax_errors
    
    def export_parse_tree(self, filename: str):
        """Export parse tree to file."""
        with open(filename, "w", encoding="utf-8") as f:
            if self.parse_tree:
                tree_str = self.parse_tree.to_string()
                # Remove trailing newline to match expected format
                if tree_str.endswith("\n"):
                    tree_str = tree_str[:-1]
                f.write(tree_str)
    
    def export_syntax_errors(self, filename: str):
        """Export syntax errors to file."""
        with open(filename, "w", encoding="utf-8") as f:
            if not self.syntax_errors:
                f.write("No syntax errors found.")
            else:
                for i, error in enumerate(self.syntax_errors):
                    f.write(error)
                    # Add newline except for the last error
                    if i < len(self.syntax_errors) - 1:
                        f.write("\n")
    
    # Grammar rule functions (one for each non-terminal)
    
    def program(self) -> ParseNode:
        """Program → Declaration-list $"""
        node = ParseNode("Program")
        node.add_child(self.declaration_list())
        
        # If unexpected EOF, stop here
        if self.unexpected_eof:
            return node
        
        # Handle any remaining tokens before EOF
        while self._get_token_string(self.current_token) != "$":
            token_str = self._get_token_string(self.current_token)
            self._add_error(f"illegal {token_str}")
            self.current_token = self.scanner.get_next_token()
        
        # Add EOF token
        node.add_child(ParseNode("$", is_terminal=True))
        return node
    
    def declaration_list(self) -> ParseNode:
        """Declaration-list → Declaration Declaration-list | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Declaration-list")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Declaration-list", lookahead)
        
        if prod_num == 2:  # Declaration Declaration-list
            node.add_child(self.declaration())
            if self.unexpected_eof:
                return node
            node.add_child(self.declaration_list())
        elif prod_num == 3:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Declaration-list")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.declaration_list()
        
        return node
    
    def declaration(self) -> ParseNode:
        """Declaration → Declaration-initial Declaration-prime"""
        if self.unexpected_eof:
            return None
        result = self._check_first_follow("Declaration")
        if result == 'skip':
            return None
        elif result == 'discard':
            return self.declaration()
        
        node = ParseNode("Declaration")
        node.add_child(self.declaration_initial())
        node.add_child(self.declaration_prime())
        return node
    
    def declaration_initial(self) -> ParseNode:
        """Declaration-initial → Type-specifier ID"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Declaration-initial")
        node.add_child(self.type_specifier())
        node.add_child(self.match("ID"))
        return node
    
    def declaration_prime(self) -> ParseNode:
        """Declaration-prime → Fun-declaration-prime | Var-declaration-prime"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Declaration-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Declaration-prime", lookahead)
        
        if prod_num == 6:  # Fun-declaration-prime
            node.add_child(self.fun_declaration_prime())
        elif prod_num == 7:  # Var-declaration-prime
            node.add_child(self.var_declaration_prime())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Declaration-prime")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.declaration_prime()
        
        return node
    
    def var_declaration_prime(self) -> ParseNode:
        """Var-declaration-prime → [ NUM ] ; | ;"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Var-declaration-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Var-declaration-prime", lookahead)
        
        if prod_num == 8:  # [ NUM ] ;
            node.add_child(self.match("["))
            node.add_child(self.match("NUM"))
            node.add_child(self.match("]"))
            node.add_child(self.match(";"))
        elif prod_num == 117:  # ;
            node.add_child(self.match(";"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Var-declaration-prime")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.var_declaration_prime()
        
        return node
    
    def fun_declaration_prime(self) -> ParseNode:
        """Fun-declaration-prime → ( Params ) Compound-stmt"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Fun-declaration-prime")
        node.add_child(self.match("("))
        node.add_child(self.params())
        node.add_child(self.match(")"))
        node.add_child(self.compound_stmt())
        return node
    
    def type_specifier(self) -> ParseNode:
        """Type-specifier → int | void"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Type-specifier")
        lookahead = self._get_token_string(self.current_token)
        
        if lookahead == "int":
            node.add_child(self.match("int"))
        elif lookahead == "void":
            node.add_child(self.match("void"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Type-specifier")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.type_specifier()
        
        return node
    
    def params(self) -> ParseNode:
        """Params → int ID Param-prime Param-list | void"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Params")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Params", lookahead)
        
        if prod_num == 12:  # int ID Param-prime Param-list
            node.add_child(self.match("int"))
            node.add_child(self.match("ID"))
            node.add_child(self.param_prime())
            node.add_child(self.param_list())
        elif prod_num == 13:  # void
            node.add_child(self.match("void"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Params")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.params()
        
        return node
    
    def param_list(self) -> ParseNode:
        """Param-list → , Param Param-list | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Param-list")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Param-list", lookahead)
        
        if prod_num == 14:  # , Param Param-list
            node.add_child(self.match(","))
            node.add_child(self.param())
            node.add_child(self.param_list())
        elif prod_num == 15:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Param-list")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.param_list()
        
        return node
    
    def param(self) -> ParseNode:
        """Param → Declaration-initial Param-prime"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Param")
        node.add_child(self.declaration_initial())
        node.add_child(self.param_prime())
        return node
    
    def param_prime(self) -> ParseNode:
        """Param-prime → [ ] | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Param-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Param-prime", lookahead)
        
        if prod_num == 17:  # [ ]
            node.add_child(self.match("["))
            node.add_child(self.match("]"))
        elif prod_num == 18:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Param-prime")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.param_prime()
        
        return node
    
    def compound_stmt(self) -> ParseNode:
        """Compound-stmt → { Declaration-list Statement-list }"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Compound-stmt")
        node.add_child(self.match("{"))
        node.add_child(self.declaration_list())
        node.add_child(self.statement_list())
        node.add_child(self.match("}"))
        return node
    
    def statement_list(self) -> ParseNode:
        """Statement-list → Statement Statement-list | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Statement-list")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Statement-list", lookahead)
        
        if prod_num == 20:  # Statement Statement-list
            node.add_child(self.statement())
            node.add_child(self.statement_list())
        elif prod_num == 21:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Statement-list")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            elif result == 'discard':
                return self.statement_list()  # Retry after discarding one token
            else:  # result == 'proceed' (shouldn't happen in else, but handle it)
                return self.statement_list()
        
        return node
    
    def statement(self) -> ParseNode:
        """Statement → Expression-stmt | Compound-stmt | Selection-stmt | Iteration-stmt | Return-stmt"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Statement")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Statement", lookahead)
        
        if prod_num == 22:  # Expression-stmt
            node.add_child(self.expression_stmt())
        elif prod_num == 23:  # Compound-stmt
            node.add_child(self.compound_stmt())
        elif prod_num == 24:  # Selection-stmt
            node.add_child(self.selection_stmt())
        elif prod_num == 25:  # Iteration-stmt
            node.add_child(self.iteration_stmt())
        elif prod_num == 26:  # Return-stmt
            node.add_child(self.return_stmt())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Statement")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.statement()
        
        return node
    
    def expression_stmt(self) -> ParseNode:
        """Expression-stmt → Expression ; | break ; | ;"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Expression-stmt")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Expression-stmt", lookahead)
        
        if prod_num == 27:  # Expression ;
            node.add_child(self.expression())
            node.add_child(self.match(";"))
        elif prod_num == 28:  # break ;
            node.add_child(self.match("break"))
            node.add_child(self.match(";"))
        elif prod_num == 29:  # ;
            node.add_child(self.match(";"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Expression-stmt")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.expression_stmt()
        
        return node
    
    def selection_stmt(self) -> ParseNode:
        """Selection-stmt → if ( Expression ) Statement Else-stmt"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Selection-stmt")
        node.add_child(self.match("if"))
        node.add_child(self.match("("))
        node.add_child(self.expression())
        node.add_child(self.match(")"))
        node.add_child(self.statement())
        node.add_child(self.else_stmt())
        return node
    
    def else_stmt(self) -> ParseNode:
        """Else-stmt → else Statement | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Else-stmt")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Else-stmt", lookahead)
        
        if prod_num == 31:  # else Statement
            node.add_child(self.match("else"))
            node.add_child(self.statement())
        elif prod_num == 32:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Else-stmt")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.else_stmt()
        
        return node
    
    def iteration_stmt(self) -> ParseNode:
        """Iteration-stmt → for ( Expression ; Expression ; Expression ) Compound-stmt"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Iteration-stmt")
        node.add_child(self.match("for"))
        node.add_child(self.match("("))
        node.add_child(self.expression())
        node.add_child(self.match(";"))
        node.add_child(self.expression())
        node.add_child(self.match(";"))
        node.add_child(self.expression())
        node.add_child(self.match(")"))
        node.add_child(self.compound_stmt())
        return node
    
    def return_stmt(self) -> ParseNode:
        """Return-stmt → return Return-stmt-prime"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Return-stmt")
        node.add_child(self.match("return"))
        node.add_child(self.return_stmt_prime())
        return node
    
    def return_stmt_prime(self) -> ParseNode:
        """Return-stmt-prime → Expression ; | ;"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Return-stmt-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Return-stmt-prime", lookahead)
        
        if prod_num == 35:  # Expression ;
            node.add_child(self.expression())
            node.add_child(self.match(";"))
        elif prod_num == 36:  # ;
            node.add_child(self.match(";"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Return-stmt-prime")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.return_stmt_prime()
        
        return node
    
    def expression(self) -> ParseNode:
        """Expression → Simple-expression-zegond | ID B"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Expression")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Expression", lookahead)
        
        if prod_num == 37:  # Simple-expression-zegond
            node.add_child(self.simple_expression_zegond())
        elif prod_num == 38:  # ID B
            node.add_child(self.match("ID"))
            node.add_child(self.b())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Expression")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.expression()
        
        return node
    
    def b(self) -> ParseNode:
        """B → = Expression | [ Expression ] H | Simple-expression-prime"""
        if self.unexpected_eof:
            return None
        node = ParseNode("B")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("B", lookahead)
        
        if prod_num == 39:  # = Expression
            node.add_child(self.match("="))
            node.add_child(self.expression())
        elif prod_num == 40:  # [ Expression ] H
            node.add_child(self.match("["))
            node.add_child(self.expression())
            node.add_child(self.match("]"))
            node.add_child(self.h())
        elif prod_num == 41:  # Simple-expression-prime
            node.add_child(self.simple_expression_prime())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("B")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.b()
        
        return node
    
    def h(self) -> ParseNode:
        """H → = Expression | G D C"""
        if self.unexpected_eof:
            return None
        node = ParseNode("H")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("H", lookahead)
        
        if prod_num == 42:  # = Expression
            node.add_child(self.match("="))
            node.add_child(self.expression())
        elif prod_num == 43:  # G D C
            node.add_child(self.g())
            node.add_child(self.d())
            node.add_child(self.c())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("H")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.h()
        
        return node
    
    def simple_expression_zegond(self) -> ParseNode:
        """Simple-expression-zegond → Additive-expression-zegond C"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Simple-expression-zegond")
        node.add_child(self.additive_expression_zegond())
        node.add_child(self.c())
        return node
    
    def simple_expression_prime(self) -> ParseNode:
        """Simple-expression-prime → Additive-expression-prime C"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Simple-expression-prime")
        node.add_child(self.additive_expression_prime())
        node.add_child(self.c())
        return node
    
    def c(self) -> ParseNode:
        """C → Relop Additive-expression | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("C")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("C", lookahead)
        
        if prod_num == 46:  # Relop Additive-expression
            node.add_child(self.relop())
            node.add_child(self.additive_expression())
        elif prod_num == 47:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("C")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.c()
        
        return node
    
    def relop(self) -> ParseNode:
        """Relop → == | <"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Relop")
        lookahead = self._get_token_string(self.current_token)
        
        if lookahead == "==":
            node.add_child(self.match("=="))
        elif lookahead == "<":
            node.add_child(self.match("<"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Relop")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.relop()
        
        return node
    
    def additive_expression(self) -> ParseNode:
        """Additive-expression → Term D"""
        if self.unexpected_eof:
            return None
        result = self._check_first_follow("Additive-expression")
        if result == 'skip':
            return None  # Missing non-terminal
        elif result == 'discard':
            return self.additive_expression()  # Retry after discarding one token
        
        # result == 'proceed'
        node = ParseNode("Additive-expression")
        node.add_child(self.term())
        node.add_child(self.d())
        return node
    
    def additive_expression_prime(self) -> ParseNode:
        """Additive-expression-prime → Term-prime D"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Additive-expression-prime")
        node.add_child(self.term_prime())
        node.add_child(self.d())
        return node
    
    def additive_expression_zegond(self) -> ParseNode:
        """Additive-expression-zegond → Term-zegond D"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Additive-expression-zegond")
        node.add_child(self.term_zegond())
        node.add_child(self.d())
        return node
    
    def d(self) -> ParseNode:
        """D → Addop Term D | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("D")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("D", lookahead)
        
        if prod_num == 53:  # Addop Term D
            node.add_child(self.addop())
            node.add_child(self.term())
            node.add_child(self.d())
        elif prod_num == 54:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("D")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.d()
        
        return node
    
    def addop(self) -> ParseNode:
        """Addop → + | -"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Addop")
        lookahead = self._get_token_string(self.current_token)
        
        if lookahead == "+":
            node.add_child(self.match("+"))
        elif lookahead == "-":
            node.add_child(self.match("-"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Addop")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.addop()
        
        return node
    
    def term(self) -> ParseNode:
        """Term → Signed-factor G"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Term")
        node.add_child(self.signed_factor())
        node.add_child(self.g())
        return node
    
    def term_prime(self) -> ParseNode:
        """Term-prime → Factor-prime G"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Term-prime")
        node.add_child(self.factor_prime())
        node.add_child(self.g())
        return node
    
    def term_zegond(self) -> ParseNode:
        """Term-zegond → Signed-factor-zegond G"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Term-zegond")
        node.add_child(self.signed_factor_zegond())
        node.add_child(self.g())
        return node
    
    def g(self) -> ParseNode:
        """G → * Signed-factor G | / Signed-factor G | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("G")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("G", lookahead)
        
        if prod_num == 59:  # * Signed-factor G
            node.add_child(self.match("*"))
            node.add_child(self.signed_factor())
            node.add_child(self.g())
        elif prod_num == 60:  # / Signed-factor G
            node.add_child(self.match("/"))
            node.add_child(self.signed_factor())
            node.add_child(self.g())
        elif prod_num == 61:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("G")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.g()
        
        return node
    
    def signed_factor(self) -> ParseNode:
        """Signed-factor → + Factor | - Factor | Factor"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Signed-factor")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Signed-factor", lookahead)
        
        if prod_num == 65:  # + Factor
            node.add_child(self.match("+"))
            node.add_child(self.factor())
        elif prod_num == 66:  # - Factor
            node.add_child(self.match("-"))
            node.add_child(self.factor())
        elif prod_num == 64:  # Factor
            node.add_child(self.factor())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Signed-factor")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.signed_factor()
        
        return node
    
    def signed_factor_zegond(self) -> ParseNode:
        """Signed-factor-zegond → + Factor | - Factor | Factor-zegond"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Signed-factor-zegond")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Signed-factor-zegond", lookahead)
        
        if prod_num == 63:  # + Factor
            node.add_child(self.match("+"))
            node.add_child(self.factor())
        elif prod_num == 62:  # - Factor
            node.add_child(self.match("-"))
            node.add_child(self.factor())
        elif prod_num == 67:  # Factor-zegond
            node.add_child(self.factor_zegond())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Signed-factor-zegond")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.signed_factor_zegond()
        
        return node
    
    def factor(self) -> ParseNode:
        """Factor → ( Expression ) | ID Var-call-prime | NUM"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Factor")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Factor", lookahead)
        
        if prod_num == 68:  # ( Expression )
            node.add_child(self.match("("))
            node.add_child(self.expression())
            node.add_child(self.match(")"))
        elif prod_num == 69:  # ID Var-call-prime
            node.add_child(self.match("ID"))
            node.add_child(self.var_call_prime())
        elif prod_num == 70:  # NUM
            node.add_child(self.match("NUM"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Factor")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.factor()
        
        return node
    
    def var_call_prime(self) -> ParseNode:
        """Var-call-prime → ( Args ) | Var-prime"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Var-call-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Var-call-prime", lookahead)
        
        if prod_num == 71:  # ( Args )
            node.add_child(self.match("("))
            node.add_child(self.args())
            node.add_child(self.match(")"))
        elif prod_num == 72:  # Var-prime
            node.add_child(self.var_prime())
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Var-call-prime")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.var_call_prime()
        
        return node
    
    def var_prime(self) -> ParseNode:
        """Var-prime → [ Expression ] | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Var-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Var-prime", lookahead)
        
        if prod_num == 73:  # [ Expression ]
            node.add_child(self.match("["))
            node.add_child(self.expression())
            node.add_child(self.match("]"))
        elif prod_num == 74:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Var-prime")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.var_prime()
        
        return node
    
    def factor_prime(self) -> ParseNode:
        """Factor-prime → ( Args ) | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Factor-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Factor-prime", lookahead)
        
        if prod_num == 75:  # ( Args )
            node.add_child(self.match("("))
            node.add_child(self.args())
            node.add_child(self.match(")"))
        elif prod_num == 76:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Factor-prime")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.factor_prime()
        
        return node
    
    def factor_zegond(self) -> ParseNode:
        """Factor-zegond → ( Expression ) | NUM"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Factor-zegond")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Factor-zegond", lookahead)
        
        if prod_num == 77:  # ( Expression )
            node.add_child(self.match("("))
            node.add_child(self.expression())
            node.add_child(self.match(")"))
        elif prod_num == 78:  # NUM
            node.add_child(self.match("NUM"))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Factor-zegond")
            if result == 'skip':
                return None
            else:  # result == 'discard'
                return self.factor_zegond()
        
        return node
    
    def args(self) -> ParseNode:
        """Args → Arg-list | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Args")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Args", lookahead)
        
        if prod_num == 79:  # Arg-list
            node.add_child(self.arg_list())
        elif prod_num == 80:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Args")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.args()
        
        return node
    
    def arg_list(self) -> ParseNode:
        """Arg-list → Expression Arg-list-prime"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Arg-list")
        node.add_child(self.expression())
        node.add_child(self.arg_list_prime())
        return node
    
    def arg_list_prime(self) -> ParseNode:
        """Arg-list-prime → , Expression Arg-list-prime | ε"""
        if self.unexpected_eof:
            return None
        node = ParseNode("Arg-list-prime")
        lookahead = self._get_token_string(self.current_token)
        
        prod_num = self._get_predict_production("Arg-list-prime", lookahead)
        
        if prod_num == 82:  # , Expression Arg-list-prime
            node.add_child(self.match(","))
            node.add_child(self.expression())
            node.add_child(self.arg_list_prime())
        elif prod_num == 83:  # ε
            node.add_child(ParseNode("epsilon", is_terminal=True))
        else:
            # No valid production - Panic Mode
            result = self._check_first_follow("Arg-list-prime")
            if result == 'skip':
                if self.unexpected_eof:
                    return None
                node.add_child(ParseNode("epsilon", is_terminal=True))
            else:  # result == 'discard'
                return self.arg_list_prime()
        
        return node
