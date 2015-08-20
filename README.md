# 2nfa

This is a rudimentary reference implementation of the three algorithms for converting two-way automata into one-way automata using regular expressions, as documented in the paper:

Hulden, M. (2015). From Two-Way to One-Way Finite Automata - Three Regular Expression-Based Methods. In Drewes, F., editor, *Implementation and Application of Automata, 20th International Conference, CIAA 2015, Umeå, Sweden*. Volume 9223 of Lecture Notes in Computer Science, pages 176-187. Springer-Verlag.[_[link]_](http://link.springer.com/chapter/10.1007%2F978-3-319-22360-5_15)

## Usage

The script reads from STDIN and outputs a foma/xfst script to STDOUT. The -a flag controls which algorithm to use: 1, 2, or 3 (see paper). Algorithm 1 handles only 2DFA but is the most efficient conversion while algorithms 2 and 3 handle 2NFA as well.

For example:

```
python 2nfa2foma.py < example1.att > example1.foma
```

produces a regular expression script from the file `example1.att` after which the resulting script can be compiled with [foma](http://foma.googlecode.com) (or [xfst](http://www.fsmbook.com)), e.g.:

```
foma -l example1.foma
```

which then produces the equivalent minimized 1DFA.


## Input file format

The 2DFA/2NFA specification is a modified AT&T format, where each transition is on a single line with whitespace-separate fields:

```
SOURCE_STATE TARGET_STATE SYMBOL DIRECTION
```

`DIRECTION` is one of L,R,S (left, right, stay). Lines with only one number identify final states.

State numbering is assumed to start from 0 and be consecutive. The symbol alphabet needs to be disjoint from the state alphabet - i.e. symbols such as `0` cannot be used.

For example:

```
0       0       a       R
0       1       b       R
1       1       a       R
1       2       b       L
2       0       a       R
2       2       b       L
0
1
2
```

Describes the two-way automaton:

![Example 1](https://github.com/mhulden/2nfa/blob/master/example1.png "")
