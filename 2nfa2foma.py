# -*- coding: utf-8 -*-

## Convert a 2DFA/2NFA in (modified) AT&T format into a sequence
## of foma/xfst -compatible regular expressions, which can be compiled
## into a minimized 1DFA.

## Usage:
## Reads from STDIN and outputs a foma/xfst script to stdout
## the -a flag controls which algorithm to use (1,2, or 3).
## 1 handles only 2DFA but is the most efficient conversion while
## 2,3 handle 2NFA as well.

## See: Hulden, M. (2015). From Two-Way to One-Way Finite Automata - Three Regular Expression-Based Methods. In Drewes, F., editor, Implementation and Application of Automata, 20th International Conference, CIAA 2015, Umeå, Sweden. Volume 9223 of Lecture Notes in Computer Science, pages 176-187. Springer-Verlag, 2015.

## It is always assumed that states are numbered from 0 onwards
## and that 0 is the only initial state.

## Input file format example:
## 0       0       a       R
## 0       1       b       R
## 1       1       a       R
## 1       2       b       L
## 2       0       a       R
## 2       2       b       L
## 0
## 1
## 2

## Columns are SOURCE TARGET SYMBOL DIRECTION(L,R,S)
## Lines with only one number identify final states.

## Example usage: python 2nfa2foma.py < example1.att > example1.foma
## After which the script can be compiled with foma -l example1.foma (or xfst)

## -MH20150424

import fileinput, getopt, sys

options, remainder = getopt.gnu_getopt(sys.argv[1:], 'a:', ['algorithm'])

algorithm = 1
for opt, arg in options:
    if opt in ('-a', '--algorithm'):
        algorithm = int(arg)


lines = [line.strip() for line in iter(lambda: sys.stdin.readline().decode('utf-8'), '')]

# Read input in AT&T format #

states = set()
symbols = set()
trans = {}
finals = set()
for l in lines:
    if len(l.split()) == 4:
        source, target, symbol, direction = l.split()
        source = int(source)
        target = int(target)
        states.add(source)
        states.add(target)
        symbols.add(symbol)
        if source not in trans:
            trans[source] = {}
        if symbol not in trans[source]:
            trans[source][symbol] = [(target, direction)]
        else:
            trans[source][symbol].append((target, direction))
    elif len(l.split()) == 1:
        final = int(l.strip())
        finals.add(final)

statelist = sorted(list(states))
symbollist = sorted(list(symbols))

if algorithm == 1:
    for s in statelist:
        if s in trans:
            for sym in symbollist:
                if sym in trans[s]:
                    if len(trans[s][sym]) > 1:
                        sys.stderr.write('***WARNING: Input two-way automaton must be deterministic with algorithm 1 to guarantee correct result!\n')

for s in statelist:
    if s not in trans:
        trans[s] = {}

def esc(s):
    return s.replace('0', '%0');

output = u''

output += 'def A  [' + '|'.join(esc(str(s)) for s in symbollist) + '] ; # Alphabet\n'
output += 'def Q  [' + '|'.join(esc(str(s)) for s in statelist) + '] ;  # States\n'
output += 'def h(X)  [X .o. \A -> 0].2;           # The homomorphism\n'

# Transitions #

for sym in symbollist:
    output += 'def T' + sym + '  '
    if algorithm == 1:
        output += '|'.join('{0} {1} {2}'.format(esc(str(state)), esc(str(source)), esc(str(target))) for state in statelist for source, target in trans[state].get(sym, [])) + ' '
    elif algorithm == 3:
        output += ' '.join('({0} {1} {2})'.format(esc(str(state)), esc(str(source)), esc(str(target))) for state in statelist for source, target in trans[state].get(sym, [])) + ' '
    else:
        for state in statelist:
            if state in trans:
                if sym in trans[state]:
                    output += "(" + ' '.join('{0} {1} {2}'.format(esc(str(state)), esc(str(source)), esc(str(target))) for source, target in trans[state][sym]) + ") "
                else:
                    output += "({0} {0} C) ".format(esc(str(state)))
            else:
                output += "({0} {0} C) ".format(esc(str(state)))
    output += ";\n"

# Ending #
output += "def Tend "
if algorithm == 1:
    output += '[' + '|'.join('{0} {0}'.format(esc(str(q))) for q in finals) + '];\n'
if algorithm == 2:
    output += '[' + ' '.join('({0} {0} C)'.format(esc(str(q))) for q in set(statelist) - set(finals)) + '];\n'
if algorithm == 3:
    output += '[' + ' '.join('({0} {0})'.format(esc(str(q))) for q in finals) + '];\n'

# L_base (the basic structure) #
if algorithm == 1:
    output += 'def Lbase [' + '|'.join('T{0}+ {0}'.format(str(s)) for s in symbollist) + ']* Tend;\n'
else:
    output += 'def Lbase [' + '|'.join('T{0} {0}'.format(str(s)) for s in symbollist) + ']* (Tend) & [%0 ?*];\n'


# L_license (constraints on moves) #
output += "def L  Lbase & "
slist = []
for s in statelist:
    if algorithm == 1:
        if s == 0:
            slist.append("[ {0} Q => _ $.A {0} L , {0} R $.A _ , _ \A* {0} S , {0} S \A* _ , .#. _ ]".format(esc(str(s))))
        else:
            slist.append("[ {0} Q => _ $.A {0} L , {0} R $.A _ , _ \A* {0} S , {0} S \A* _ ]".format(esc(str(s))))
    if algorithm == 2:
        slist.append(" [ {0} R => _ $.A {0} Q ] ".format(esc(str(s))))
        slist.append(" [ {0} L => {0} Q $.A _ , .#. \A* _ ] ".format(esc(str(s))))
    if algorithm == 3:
        slist.append(" [ {0} R => _ $.A {0} Q ] ".format(esc(str(s))))
        slist.append(" [ {0} L => {0} Q $.A _ ] ".format(esc(str(s))))

output += " & ".join(slist) + ";\n"


if algorithm == 1:
    output += 'regex h(L);\n'
if algorithm == 2:
    output += 'regex A* - h(L);\n'
if algorithm == 3:
    output += 'def Insert(Z) [Z .o. [?* [0:\A]+ ?*]+ .o. Lbase].2;\n'
    output += 'regex h([L - Insert(L)] & [?* Q Q]);\n'

print output.encode('utf-8'),
