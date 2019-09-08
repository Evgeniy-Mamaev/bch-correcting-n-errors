import csv

import yaml
from itertools import combinations


def get_primitive_polynomial(n, k):
    """
    Retrieves a table of primitive
    polynomials from the given in
    the config file, and returns a
    corresponding to the
    parameters polynomial.
    :param n: length of a code.
    :param k: param in the table
    corresponds to the size of the
    polynomial. Maps 1 -> 3,
    2 -> 5, 3 -> 7
    :return: a primitive polynomial
    in a binary representation.
    """
    if n < 1 | n > 51:
        raise ValueError('The parameter n should be 1 <= n <= 51, '
                         'n is {0}'.
                         format(n))
    if k < 1 | k > 3:
        raise ValueError('The parameter k should be 1 <= k <= 3, '
                         'k is {0}'.
                         format(k))
    config = yaml.safe_load(open("config.yml"))
    dictionary = {1: 1, 2: 2, 3: 5, 4: 10}
    with open(config['primitive-polynomials'], newline='') as csvfile:
        primitive_polynomials = csv.reader(csvfile, delimiter=',')
        for row in primitive_polynomials:
            ints = list(map(lambda x: 0 if x == '' else int(x), row))
            if ints[0] == n:
                polynomial_powers = ints[dictionary[k]:dictionary[k + 1]]
                polynomial_binary = 1 << n
                polynomial_binary |= 1
                for i in polynomial_powers:
                    polynomial_binary |= 1 << i
                return polynomial_binary


def build_logarithmic_table(n, primitive_polynomial):
    """
    Builds a logarithmic table where a
    logarithm is mapped to the binary
    representation of the corresponding
    polynomial.
    The field is generated by the
    :param primitive_polynomial.
    :param n: the power in size of the
              n
    field GF(2 ).
    :return: the logarithmic table of
    the field.
    """
    if len(bin(primitive_polynomial)) - 3 != n:
        raise ValueError('The primitive polynomial {0:b} '
                         'is not of the specified power n = {1}'.
                         format(primitive_polynomial, n))
    logarithmic_table = {-1: 0}
    for i in range(n):
        logarithmic_table[i] = 1 << i
    logarithmic_table[n] = trim_polynomial(primitive_polynomial, n)
    for i in range(n + 1, 2 ** n - 1):
        multiplied_by_x_polynomial = logarithmic_table[i - 1] << 1
        if multiplied_by_x_polynomial & (2 ** n):
            multiplied_by_x_polynomial ^= logarithmic_table[n]
        logarithmic_table[i] = trim_polynomial(multiplied_by_x_polynomial, n)
    return logarithmic_table


def multiply_polynomials(polynomial1, polynomial2):
    result = 0
    for i in range(len(bin(polynomial2)) - 2):
        if polynomial2 & (1 << i):
            result ^= polynomial1 << i
    return result


def divide_polynomials(polynomial1, polynomial2):
    """
    quotient:
            11101000111
           _________________
    11001 | 100100100000001
            110010000000000
            ________________
             10110100000001
             11001000000000
             _______________
              1111100000001
              1100100000000
              ______________
                11000000001
                11001000000
                ____________
                    1000001
                    1100100
                    ________
                     100101
                     110010
                     _______
                      10111
                      11001
                      ______
            reminder:  1110

    :param polynomial1:
    :param polynomial2:
    :return:
    """
    quotient = 0
    reminder = polynomial1
    while len(bin(reminder)) >= len(bin(polynomial2)):
        shift = len(bin(reminder)) - len(bin(polynomial2))
        reminder ^= polynomial2 << shift
        quotient ^= 1 << shift
    return quotient, reminder


def polynomial_of_argument_to_power(polynomial, power):
    length = len(bin(polynomial)) - 2
    result = 0
    for i in range(length):
        if polynomial >> i & 1 == 1:
            result |= 1 << i * power
    return result


def get_cyclotomic_cosets(n):
    """
    Fills a list of cyclotomic cosets.
                     4
    For GF(16) = GF(2 ) based on the
                4
    polynomial x  + x + 1 with the
    primitive root α=x+0 cyclotomic
    cosets are:
                                     4
    m1(x) = m2(x) = m4(x) = m8(x) = x  + x + 1,
                                      4    3    2
    m3(x) = m6(x) = m9(x) = m12(x) = x  + x  + x  + x + 1,
                      2
    m5(x) = m10(x) = x  + x + 1,
                                        4    3
    m7(x) = m11(x) = m13(x) = m14(x) = x  + x  + 1.
    :param n: the power in size of the
              n
    field GF(2 ).
    :return: a list of cyclotomic cosets
    in the binary representation.
    """
    cyclotomic_cosets = []
    all_cyclotomic_members = 1
    i = 0
    while all_cyclotomic_members < 2 ** (2 ** n - 2) - 1:
        cyclotomic_cosets.append(0)
        k = 0
        while True:
            if not 1 & (all_cyclotomic_members >> k):
                break
            k += 1
        while True:
            k = k % (2 ** n - 1)
            if 1 & (cyclotomic_cosets[i] >> k):
                break
            cyclotomic_cosets[i] ^= 1 << k
            k *= 2
        all_cyclotomic_members ^= cyclotomic_cosets[i]
        i += 1
    return cyclotomic_cosets


def get_polynomial_from_roots(roots, n, logarithmic_table):
    """
    Performs multiplication of a
    polynomial represented by its
    roots in form:
          k1        k2           kn
    (x - a  )*(x - a  )...*(x - a  ).
    :param roots: a binary vector
    of roots, where positions of
    1s mean the power a primitive
    element a of the field.
    :param n: the power in size of
                  n
    the field GF(2 ).
    :param logarithmic_table:
    a table which maps logarithms
    to polynomials - members of
    the field.
    :return: a binary vector
    represents a polynomial in
             l1    l2        lr
    form of x   + x   ... + x   + 1
    """
    if roots == 0:
        return 0
    number_of_field_elements = 2 ** n - 1
    root_array = get_positions_of_binary_ones(roots)
    polynomial = 1 << len(root_array)
    for i in range(len(root_array)):
        coefficient = 0
        for combination in combinations(root_array, i + 1):
            coefficient ^= logarithmic_table[sum(combination) % number_of_field_elements]
        addition = coefficient << len(root_array) - i - 1
        polynomial ^= addition
    return polynomial


def get_positions_of_binary_ones(number):
    length = len(bin(number)) - 2
    result = []
    for i in range(0, length):
        if 1 & (number >> i):
            result.append(i)
    return result


def trim_polynomial(polynomial, length):
    return polynomial & ((2 ** length) - 1)
