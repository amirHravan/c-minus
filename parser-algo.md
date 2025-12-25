

# **Slide 76 – Predictive Top-Down Parsing**

**Parser Never Backtracks**

For Example, Consider:

```
Type → Simple
     | ↑ id
     | array [ Simple ] of Type

Simple → integer
        | char
        | num dotdot num
```

Suppose input is:

```
array [ num dotdot num ] of integer
```

Parsing would begin with

```
Type → ???
```

Start symbol

---

# **Slide 77 – Predictive Parsing Example**

```
Type → Simple
     | ↑ id
     | array [ Simple ] of Type

Simple → integer
        | char
        | num dotdot num
```

Start symbol

```
array [ Simple ] of Type
Type
array [ Simple ] of Type
Type
num dotdot num
```

Input:

```
array [ num dotdot num ] of integer
```

Lookahead symbol
Type
?

---

# **Slide 78 – Predictive Parsing Example**

```
Type → Simple
     | ↑ id
     | array [ Simple ] of Type

Simple → integer
        | char
        | num dotdot num
```

Start symbol

Input:

```
array [ num dotdot num ] of integer
```

Lookahead symbol

```
array [ Simple ] of Type
Type
num dotdot num Simple
array [ Simple ] of Type
Type
num dotdot num Simple
integer
```

---

# **Slide 79 – Predictive Recursive Descent**

• Parser is implemented by **N + 1 subroutines**,
where N is the number grammar non-terminals

• There is **one subroutine for attempting to Match tokens** in the input stream

• There is also **one subroutine for each non-terminal** with two tasks:

1. Deciding on the next production to use
2. Applying the selected production

---

# **Slide 80 – Predictive Recursive Descent (Cont.)**

Procedure **“Match”** checks if the token matches the expected input

```
procedure Match ( expected_token ) ;
{
   if lookahead = expected_token then
        lookahead := get_next_token
   else error
}
```

---

# **Slide 81 – Predictive Recursive Descent (Cont.)**

• The subroutine for each non-terminal has two tasks:

1. Selecting the appropriate production
2. Applying the chosen production

• Selection is done based on the result of a number of
**if-then-else statements**

• Applying a production is implemented by calling the
**match procedure or other subroutines**, based on the rhs of the production

---

# **Slide 82 – Predictive Recursive Descent (Cont.)**

Subroutine **“Simple”** for the given example:

```
procedure Simple ;
{
   if lookahead = integer then call Match ( integer );
   else if lookahead = char then call Match ( char );
   else if lookahead = num
        then { call Match ( num );
               call Match ( dotdot );
               call Match ( num ) }
   else error
}
```

Grammar:

```
Type → Simple
     | ↑ id
     | array [ Simple ] of Type

Simple → integer
        | char
        | num dotdot num
```

---

# **Slide 83 – Predictive Recursive Descent (Cont.)**

Subroutine **“Type”** for the given example:

```
Type → Simple
     | ↑ id
     | array [ Simple ] of Type

Simple → integer
        | char
        | num dotdot num
```

```
procedure Type ;
{
   if lookahead is in { integer, char, num } then call Simple;
   else if lookahead = ‘↑’ then
        { call Match ( ‘↑’ ) ; call Match( id ) }
   else if lookahead = array
        then { call Match( array );
               call Match( ‘[‘ );
               call Simple;
               call Match( ‘]’ );
               call Match( of );
               call Type }
   else error
}
```

---
