# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

# Given empirical data from perf_measure.py, calculate the coefficients of the
# polynomials for file, call, and line operation counts.
#
# Written by Kyle Altendorf.

import attr
import itertools
import numpy
import scipy.optimize
import sys


def f(*args, simplify=False):
    p = ((),)
    for l in range(len(args)):
        l += 1
        p = itertools.chain(p, itertools.product(*(args,), repeat=l))

    if simplify:
        p = {tuple(sorted(set(x))) for x in p}
        p = sorted(p, key=lambda x: (len(x), x))

    return p

def m(*args):
    if len(args) == 0:
        return 0

    r = 1
    for arg in args:
        r *= arg

    return r


class Poly:
    def __init__(self, *names):
        self.names = names

        self.terms = f(*self.names, simplify=True)

    def calculate(self, coefficients, **name_values):
        for name in name_values:
            if name not in self.names:
                raise Exception('bad parameter')

        substituted_terms = []
        for term in self.terms:
            substituted_terms.append(tuple(name_values[name] for name in term))

        c_tuples = ((c,) for c in coefficients)

        terms = tuple(a + b for a, b in zip(c_tuples, substituted_terms))

        multiplied = tuple(m(*t) for t in terms)
        total = sum(multiplied)

        return total


poly = Poly('f', 'c', 'l')

#print('\n'.join(str(t) for t in poly.terms))

@attr.s
class FCL:
    f = attr.ib()
    c = attr.ib()
    l = attr.ib()

INPUT = """\
1,1,1,18,242,1119
1,1,2,18,242,1121
1,1,3,18,242,1123
1,1,4,18,242,1125
1,1,5,18,242,1127
1,2,1,18,243,1124
1,2,2,18,243,1128
1,2,3,18,243,1132
1,2,4,18,243,1136
1,2,5,18,243,1140
1,3,1,18,244,1129
1,3,2,18,244,1135
1,3,3,18,244,1141
1,3,4,18,244,1147
1,3,5,18,244,1153
1,4,1,18,245,1134
1,4,2,18,245,1142
1,4,3,18,245,1150
1,4,4,18,245,1158
1,4,5,18,245,1166
1,5,1,18,246,1139
1,5,2,18,246,1149
1,5,3,18,246,1159
1,5,4,18,246,1169
1,5,5,18,246,1179
2,1,1,19,399,1893
2,1,2,19,399,1897
2,1,3,19,399,1901
2,1,4,19,399,1905
2,1,5,19,399,1909
2,2,1,19,401,1903
2,2,2,19,401,1911
2,2,3,19,401,1919
2,2,4,19,401,1927
2,2,5,19,401,1935
2,3,1,19,403,1913
2,3,2,19,403,1925
2,3,3,19,403,1937
2,3,4,19,403,1949
2,3,5,19,403,1961
2,4,1,19,405,1923
2,4,2,19,405,1939
2,4,3,19,405,1955
2,4,4,19,405,1971
2,4,5,19,405,1987
2,5,1,19,407,1933
2,5,2,19,407,1953
2,5,3,19,407,1973
2,5,4,19,407,1993
2,5,5,19,407,2013
3,1,1,20,556,2667
3,1,2,20,556,2673
3,1,3,20,556,2679
3,1,4,20,556,2685
3,1,5,20,556,2691
3,2,1,20,559,2682
3,2,2,20,559,2694
3,2,3,20,559,2706
3,2,4,20,559,2718
3,2,5,20,559,2730
3,3,1,20,562,2697
3,3,2,20,562,2715
3,3,3,20,562,2733
3,3,4,20,562,2751
3,3,5,20,562,2769
3,4,1,20,565,2712
3,4,2,20,565,2736
3,4,3,20,565,2760
3,4,4,20,565,2784
3,4,5,20,565,2808
3,5,1,20,568,2727
3,5,2,20,568,2757
3,5,3,20,568,2787
3,5,4,20,568,2817
3,5,5,20,568,2847
4,1,1,21,713,3441
4,1,2,21,713,3449
4,1,3,21,713,3457
4,1,4,21,713,3465
4,1,5,21,713,3473
4,2,1,21,717,3461
4,2,2,21,717,3477
4,2,3,21,717,3493
4,2,4,21,717,3509
4,2,5,21,717,3525
4,3,1,21,721,3481
4,3,2,21,721,3505
4,3,3,21,721,3529
4,3,4,21,721,3553
4,3,5,21,721,3577
4,4,1,21,725,3501
4,4,2,21,725,3533
4,4,3,21,725,3565
4,4,4,21,725,3597
4,4,5,21,725,3629
4,5,1,21,729,3521
4,5,2,21,729,3561
4,5,3,21,729,3601
4,5,4,21,729,3641
4,5,5,21,729,3681
5,1,1,22,870,4215
5,1,2,22,870,4225
5,1,3,22,870,4235
5,1,4,22,870,4245
5,1,5,22,870,4255
5,2,1,22,875,4240
5,2,2,22,875,4260
5,2,3,22,875,4280
5,2,4,22,875,4300
5,2,5,22,875,4320
5,3,1,22,880,4265
5,3,2,22,880,4295
5,3,3,22,880,4325
5,3,4,22,880,4355
5,3,5,22,880,4385
5,4,1,22,885,4290
5,4,2,22,885,4330
5,4,3,22,885,4370
5,4,4,22,885,4410
5,4,5,22,885,4450
5,5,1,22,890,4315
5,5,2,22,890,4365
5,5,3,22,890,4415
5,5,4,22,890,4465
5,5,5,22,890,4515
"""

inputs_outputs = {}
for row in INPUT.splitlines():
    row = [int(v) for v in row.split(",")]
    inputs_outputs[FCL(*row[:3])] = FCL(*row[3:])

#print('\n'.join(str(t) for t in inputs_outputs.items()))

def calc_poly_coeff(poly, coefficients):
    c_tuples = list(((c,) for c in coefficients))
    poly = list(f(*poly))
    poly = list(a + b for a, b in zip(c_tuples, poly))
    multiplied = list(m(*t) for t in poly)
    total = sum(multiplied)
    return total

def calc_error(inputs, output, coefficients):
    result = poly.calculate(coefficients, **inputs)
    return result - output


def calc_total_error(inputs_outputs, coefficients, name):
    total_error = 0
    for inputs, outputs in inputs_outputs.items():
        total_error += abs(calc_error(attr.asdict(inputs), attr.asdict(outputs)[name], coefficients))

    return total_error

coefficient_count = len(poly.terms)
#print('count: {}'.format(coefficient_count))
x0 = numpy.array((0,) * coefficient_count)

#print(x0)

with open('results', 'w') as f:
    for name in sorted(attr.asdict(FCL(0,0,0))):
        c = scipy.optimize.minimize(
            fun=lambda c: calc_total_error(inputs_outputs, c, name),
            x0=x0
        )

        coefficients = [int(round(x)) for x in c.x]
        terms = [''.join(t) for t in poly.terms]
        message = "{}' = ".format(name)
        message += ' + '.join("{}{}".format(coeff if coeff != 1 else '', term) for coeff, term in reversed(list(zip(coefficients, terms))) if coeff != 0)
        print(message)
        f.write(message)
