"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

import numbers
import csv
from pprint import pformat


class CSV:
    def __init__(self, arg, delimiter=None):
        '''
        A class to store the information of CSV files

        arg: either a CSV object (in which case the init function makes a duplicate) or a file path that the CSV object should load its data from
        '''

        if isinstance(arg, CSV):
            self.csv = [row[:] for row in arg.csv] # copy the list
            if delimiter is None:
                self.delimiter = arg.delimiter
        else:
            if delimiter is None:
                delimiter = ";"
            self.delimiter = delimiter

            if isinstance(arg, list):
                self.csv = [row[:] for row in arg] # copy the list
            elif isinstance(arg, str):
                with open(arg, "r") as csv_file:
                    reader = csv.reader(csv_file, delimiter=self.delimiter)
                    output = []
                    for input_row in reader:
                        output_row = []
                        for input_column in input_row:
                            output_row.append(input_column)
                        output.append(output_row)
                    self.csv = output
            else:
                raise TypeError("Incorrect parameter type '{}' for CSV class initialization: must be list or string".format(type(arg)))

        # self.csv is a row-major array
        # how many rows there are in the CSV
        self.height = len(self.csv)
        self.width = len(self.csv[0])

        # check to make sure the array is a perfect rectangle; all rows must have the same amount of entries
        for row_index in range(1, self.height):
            if len(self.csv[row_index]) != self.width:
                raise ValueError("CSV object did not have the same amount of entries in each row")

        self.dims = (self.height, self.width)


    def write(self, filename):
        '''Saves the CSV data into a .csv file'''
        with open(filename, "w") as f:
            for row in self.csv:
                f.write(self.delimiter.join([str(val) for val in row]) + "\n")


    def __eq__(self, other):
        '''Equality operator "==" '''
        if isinstance(other, CSV):
            return self.csv == other.csv
        else:
            raise NotImplementedError("Equality operator between CSV object and object of type '{}' is not supported".format(type(other)))


    def __add__(self, other):
        '''Addition operator "+" '''

        if isinstance(other, CSV):
            dims = self.dims # cache
            if dims != other.dims:
                raise ValueError("CSVs with dimensions {} and {} cannot be added together".format(self.dims, other.dims))
            height, width = dims
            ans = []
            for row_index in range(height):
                ans_row = []
                for column_index in range(width):
                    self_val = self.csv[row_index][column_index]
                    other_val = other.csv[row_index][column_index]
                    ans_row.append(self._add_values(self_val, other_val))
                ans.append(ans_row)
            return CSV(ans)
        else:
            raise NotImplementedError("Addition between CVS objects and objects of type '{}' is not supported".format(type(other)))


    def __truediv__(self, other):
        '''Division operator "/" '''
        if isinstance(other, numbers.Number):
            # divide each number in the CSV by the given number (keep the strings the same)
            ans = []
            for row in self.csv:
                ans_row = []
                for val in row:
                    ans_row.append(str(self._div_value(val, other)))
                ans.append(ans_row)
            return CSV(ans)
        else:
            raise NotImplementedError("Division of a CVS object by an object of type '{}' is not supported".format(type(other)))


    def __str__(self):
        '''Gives back string form of the CSV object'''
        return pformat(self.csv)


    def _div_value(self, val1, val2):
        '''
        If the first parameter is a number, divides the first parameter by the second parameter and returns the results .
        If the first parameter is a string, returns the string.
        (The second parameter should always be a number.)
        '''
        try:
            float_val = float(val1)
            return self._int_if_possible(float_val / val2)
        except (ValueError, TypeError):
            return val1


    def _add_values(self, val1, val2):
        '''
        If given two numbers, returns the sum.
        If given two strings, checks to see that they're the same and then returns one of them.
        If given two strings that are not the same, raises a ValueError.
        '''
        try:
            add_val1 = float(val1)
            add_val2 = float(val2)
            return self._int_if_possible(add_val1 + add_val2)
        except (ValueError, TypeError): # they must be strings
            if val1 != val2:
                raise ValueError("Cannot add together the strings '{}' and '{}' because they are different strings".format(val1, val2))
            return val1


    def _int_if_possible(self, num):
        '''Takes a float, returns an integer if the float represents an integer (i.e. "2.0"->"2"), otherwise returns back the float.'''
        int_num = int(num) # cache
        if int_num == num:
            return int_num
        else:
            return num

if __name__ == "__main__":
    # just testing
    x = CSV("Sample CSV Files/bas0-test.csv")
    print(x)
    x.write("testing.csv")
    k = CSV("testing.csv")
    print("k")
    print(k)
    j = (k+k)/2
    print("j")
    print(j)
    print("j==k")
    print(j==k)
