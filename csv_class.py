import numbers
import csv
from pprint import pformat

class InvalidDimensions(RuntimeError):
    pass


class CSV:
    def __init__(self, arg, delimiter=";"):
        self.delimiter = delimiter
        if isinstance(arg, list):
            self.csv = arg
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
            raise ValueError("Incorrect parameter type '{}' for CSV class initialization: must be list or string".format(type(arg)))

    def write(self, filename):
        with open(filename, "w") as f:
            for row in self.csv:
                f.write(self.delimiter.join([str(val) for val in row]) + "\n")



    @property
    def height(self):
        return len(self.csv)

    @property
    def width(self):
        return len(self.csv[0])

    @property
    def dims(self):
        return (self.height, self.width)


    def __add__(self, other):
        if isinstance(other, CSV):
            dims = self.dims # cache
            if dims != other.dims:
                raise InvalidDimensions("CSVs with dimensions {} and {} are incompatible".format(self.dims, other.dims))
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
            raise NotImplementedError("Addition between CVS and {} is not supported".format(type(other)))


    def __truediv__(self, other):
        if isinstance(other, numbers.Number):
            # divide each number in the CSV by the given number (keep the strings the same)
            for row in self.csv:
                for column_index, val in enumerate(row):
                    row[column_index] = self._div_value(val, other)
        else:
            raise NotImplementedError("Division of CVS by object of type '{}' is not supported".formt(type(other)))


    def __str__(self):
        return pformat(self.csv)


    def _div_value(self, val1, val2):
        '''
        Divides the first parameter by the second parameter if the first parameter is a number.
        If the first parameter is a string, returns the string.
        (The second parameter should always be a number.)
        '''
        try:
            float_val = float(val1)
            return self._int_if_possible(float_val / val2)
        except ValueError:
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
        except ValueError: # they must be strings
            if val1 != val2:
                raise ValueError("Cannot add together the strings '{}' and '{}'".format(val1, val2))
            return val1


    def _int_if_possible(self, num):
        int_num = int(num) # cache
        if int_num == num:
            return int_num

if __name__ == "__main__":
    x = CSV("Sample CSV Files/bas0-test.csv")
    print(x)
    x.write("testing.csv")
    k = CSV("testing.csv")
    print(k)
