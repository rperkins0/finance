"""
Use DataFrame to read/analyze/plot CSV files from bank accounts.

Objectives:
- month-to-month income and expense plotting
- search
-
"""
import pandas as pd

class repository(object):
    """
    Abstract base class to read statements from a given bank/institute.
    """

    directory = '/home/rory/finance/'

    def __init__(self):
        pass

    def get_files(self):
        raise NotImplementedError()

    def read_csv(self, files):
        raise NotImplementedError()

    def build_dataframe(self, filelist):
        #NEED TO DISTINGUISH CHECKING FROM SAVINGS
        df = self.read_csv(filelist[0])
        for file in filelist[1:]:
            df = df.append(self.read_csv(file),
                           ignore_index=True)
        return df.sort_values(by='date')

    def format(self, dataframe):
        raise NotImplementedError()

    def execute(self):
        filelist = self.get_files()
        dataframe = self.build_dataframe(filelist)
        #self.format(dataframe)
        return dataframe

class repository_mit(repository):

    def get_files(self):
        import subprocess
        ls = subprocess.run('ls '+repository.directory+'X_x2o_Pseudo*csv',
                            stdout=subprocess.PIPE,
                            shell=True)
        paths = ls.stdout.decode('utf-8').split('\n')
        #NOTE: 'paths' has an empty string at end
        return paths[:-1]

    def read_csv(self, path):
        print(path)
        file = open(path, 'r')
        try:
            _ = file.readline()
            df = pd.read_csv(file)
            df.columns = ['date', 'type', 'delta', 'balance']
        finally:
            file.close()
        return df

    @staticmethod
    def money_string_parser(s):
        if type(s) == str:
            split = s.split('$')
            if len(split) != 2:
                raise ValueError('Argument is not formatted as currency with single: '+s)
            if split[0].strip() == '-':
                sign = -1
            elif split[0].strip() == '+' or split[0].strip() == '':
                sign = 1
            else:
                raise ValueError('String not formatted properly; cannot determine sign: '+s)
            return sign*float(split[1])
        else:
            return s

    def format(self, dataframe):
        dataframe.delta = dataframe['delta'].map(repository_mit.money_string_parser)
        dataframe.balance = dataframe['balance'].map(repository_mit.money_string_parser)

class statement(pd.DataFrame):
    """
    Extend a DataFrame with methods specialized to bank statements.

    my_statement = statement(file="bank_statement2019.csv")
    my_statement.barplot(2019)
    my_statement.credit_card_monthly()
    my_statement.income()
    """
    _metadata = ['name',
                 'subname',
                 'file'
                 ]

    def __init__(self,
                 data=None,
                 file=''
                 ):
        """
        Conveniently initiate by passing file path. HOWEVER, needs to
        have option of passing the all-encompassing "data" argument
        for built-in panda functions to work properly (avoid
        BlockManager errors).
        """
        if data is None:
            (name, subname, temp) = self.fileload(file)
            super().__init__(data=temp)
            self.name = name
            self.subname = subname
            self.file = file
        else:
            super().__init__(data=data)

    # per https://pandas.pydata.org/pandas-docs/stable/development/extending.html#extending-subclassing-pandas
    # this makes built-in panda methods return 'fund' class, not 'DataFrame' class
    @property
    def _constructor(self):
        return fund

    def fileload(self, path):
        """
        Given a path to a formatted csv, open csv, parse header, and return body as a panda.
        :param path: path to csv file
        :return:
        name -- name of investment account
        subname -- further categorization of investment account
        path -- path to file, stored for future use
        """
        file = open(path, mode='r')

        name, subname= self._mitfcu_header_read(file)

        temp = pd.read_csv(file, parse_dates=['Date'])
        # column 'date' imported as datetime object
        # convert to date object
        temp['Date'] = temp['Date'].dt.date

        file.close()
        return (name, subname, temp)

    def _mitfcu_header_read(self, file):
        subname = file.readline().split(':')[1].strip()
        _ = file.readline() #ignore account number
        _ = file.readline() #ignore date range
        return 'MIT FCU', subname

    def income(self, year=2019):
        """
        Return all incomes for the specified year.
        :param year:
        :return:
        """
        pass

    def barplot(self, year=2019, quantity='' ):
        """
        Generate a bar plot of the quantity of interest.
        :param year:
        :return:
        """
        pass

    def stackedbarplot(self, year=2019):
        """
        Make a stacked bar plot comparing saved money versus spent money.
        :param year:
        :return:
        """
        pass
