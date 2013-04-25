import parsley
def calculate(start, pairs):
    print 'start={} pairs={}'.format(start, pairs)
    result = start
    for op, value in pairs:
        # value is now a tuple. [0] is the magnitude, [1] is the unit
        # add and substract must have same units, else error.
        if type(result) != tuple:
            result = (result, '')
        if type(value) != tuple:
            value = (value, '')

        u1 = result[1]
        u2 = value[1]
        if op == '+':
            assert u1==u2, "Units don't match: {} and {}".format(u1, u2)
            result = (result[0] + value[0], u1)
        elif op == '-':
            assert u1==u2, "Units don't match: {} and {}".format(u1, u2)
            result = (result[0] - value[0], u1)
        elif op == '*':
            result = (result[0] * value[0], u1 + '*' + u2)
        elif op == '/':
            result = (result[0] / value[0], u1 + '/(' + u2 + ')')
    if result[1]=='':
        result = result[0]
    print result
    return result
x = parsley.makeGrammar("""
ws = ' '*
digit = :x ?(x in '0123456789') -> x
digits = <digit*>
digit1_9 = :x ?(x in '123456789') -> x

intPart = (digit1_9:first digits:rest -> first + rest) | digit
floatPart :sign :ds = <('.' digits exponent?) | exponent>:tail
                     -> float(sign + ds + tail)
exponent = ('e' | 'E') ('+' | '-')? digits
number = spaces ('-' | -> ''):sign (intPart:ds (floatPart(sign ds)
                                               | -> int(sign + ds)))

unit = <letter*>
units = <unit (ws ('='|'={') ws unit)*>

parens = '(' ws expr:e ws ')' -> e
value = (number:e ws units:u | parens:e ws units:u) ws -> (e, u)

add = '+' ws expr2:n -> ('+', n)
sub = '-' ws expr2:n -> ('-', n)
mul = '*' ws value:n -> ('*', n)
div = '/' ws value:n -> ('/', n)

addsub = ws (add | sub)
muldiv = ws (mul | div)

expr = expr2:left addsub*:right -> calculate(left, right)
expr2 = value:left muldiv*:right -> calculate(left, right)


""", {"calculate": calculate})

if __name__ == '__main__':
    print 'Try some operations (q to end):'
    while True:
        expr = raw_input()
        if expr.lower() == 'q':
            print 'Exiting...'
            break
        print x(expr).expr()
    #print x("17+34").expr()
    #print x("18").expr()