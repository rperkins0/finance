import csv
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd
from typing import List

import allocation
import investment_types


class Account(pd.DataFrame):
    _metadata = ['name',
                 'subname',
                 'funds',
                 'alloc',
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
            (name, subname, path, funds, alloc, temp) = self.fileload(file)
            super().__init__(data=temp)
            self.name = name
            self.subname = subname
            self.file = path
            self.funds = funds
            self.alloc = alloc
        else:
            super().__init__(data=data)

    # per https://pandas.pydata.org/pandas-docs/stable/development/extending.html#extending-subclassing-pandas
    # this makes built-in panda methods return 'fund' class, not 'DataFrame' class
    @property
    def _constructor(self):
        return Account

    @staticmethod
    def fileload(path):
        """
        Given a path to a formatted csv, open csv, parse header, and return body as a panda.
        :param path: path to csv file
        :return:
        name -- name of investment account
        subname -- further categorization of investment account
        path -- path to file, stored for future use
        funds -- a list of strings of fund names
        alloc -- custom structure: a list of 2-tuples, first item is target percentage of total in this category,
        second is a set of fund names
        """
        with open(path, mode='r') as file:

            # read first line and extract name
            name = file.readline().strip()
            # read second line and extract subname
            subname = file.readline().strip()
            # read third line and extract list of funds
            funds = file.readline().strip().split(',')
            # read allocations
            percentage = 0.
            alloc = allocation.Allocation()
            while percentage < 1.0:
                line = file.readline().strip()  # remove \n at end!
                # parse line to get (itype, percent, fundlist)
                construction_parameters = allocation.AllocationEntry.parse_csv_str(line)
                alloc.append(allocation.AllocationEntry(*construction_parameters))
                percentage += construction_parameters[1]
            alloc.check_percentages()  # raise Exception if percents do not total 1.0
            # read rest of file as a DataFrame
            temp = pd.read_csv(file, parse_dates=['date'])
            # column 'date' imported as datetime object
            # convert to date object
            temp['date'] = temp['date'].dt.date

        return (name, subname, path, funds, alloc, temp)

    @staticmethod
    def date_converter(date_representation=None):
        """
        Convert a datetime.datetime object or string to a datetime.datetime.date object.  By default (if given no
        argument) returns today's date.
        :param date_representation: String or datetime.datetime object to convert.  Defaults to None
        :return: datetime.datetime.date object
        """
        if not date_representation:
            this_date = datetime.datetime.date(datetime.datetime.now())
        else:
            if isinstance(date_representation, str):
                try:
                    this_date = datetime.datetime.date(pd.to_datetime(date_representation))
                except ValueError as err:
                    raise ValueError("Date string %s not formatted properly; exiting" % date_representation) from err

            else:
                try:
                    this_date = datetime.datetime.date(date_representation)
                except TypeError as err:
                    x = str(type(date_representation))
                    raise TypeError('date argument is of invalid type %s' % x) from err
        return this_date

    def status(self, date=None):
        """
        Add a 'status' line to the DataFrame.
        :param date: optional argument to pass a date.  Can either be string, datetime object, or pandas Timestamp.  Defaults to today.
        :return:
        """
        formatted_date = self.date_converter(date_representation=date)
        current = {}
        current['type'] = 'status'
        current['date'] = formatted_date
        for f in self.funds:
            fund_status_string = input("Current value of " + f + ": ")
            current[f] = int(fund_status_string)

        New_DataFrame_toAppend = pd.DataFrame(current, index=[0])
        self.append_dataframe(New_DataFrame_toAppend)

    def append_dataframe(self, df):
        # can't believe this works, but it does and retains metadata!
        super().__init__(data=self.append(df,
                                          sort=False,
                                          ignore_index=True
                                          )
                         )

    @property
    def total(self):
        """
        Get current amount of $$ in account, summed over funds in
        latest status line.
        """
        current = self._laststatus()
        return current[self.funds].sum()

    def _laststatus(self):
        """
        Get the latest 'status' line from DataFrame

        :return: DataFrame of length one
        """
        status_df = self.loc[self['type'] == 'status']
        return status_df.sort_index().iloc[-1]

    def service_allocations(self) -> List[int]:
        """
        For each AllocationEntry, sum the amount in each fund
        :return: a list of int's
        """
        latest = self._laststatus()
        return [sum(latest[a.fundlist]) for a in self.alloc]

    def service_investment_type(self, it: investment_types.InvestmentType):
        type_matches = [a for a in self.alloc if type(a.itype) == type(it)]
        subtotals = [sum(self._laststatus()[a.fundlist]) for a in type_matches]
        return sum(subtotals)


    def rebalance(self, new_money=0):
        """
        Calculate how much of each fund to sell/buy in order to
        rebalance portfolio.  This does not actually update
        the DataFrame.

        Input: new_money -- additional funds to invest
        """
        self.alloc.rebalance(self.service_allocations(), new_funds=new_money)

    def transact(self,
                 amounts=False,
                 date=None
                 ):
        """
        Commit money to each fund.  Adds two new lines: an 'invest'
        line and a status line.  Either input a tuple of funds to add,
        OR run with no argument and enter interactively

        Input: amount -- an n-tuple of money invested/withdrawn
        """
        # interactive method of entering funding amounts
        if not amounts:
            amounts = [int(input('Investment in ' + f + ': ')) for f in self.funds]
        else:
            if len(amounts) != len(self.funds):
                raise ValueError('Incorrect number of elements in amounts')

        current = {'type': 'transact'}
        current['date'] = self.date_converter(date_representation=date)
        for each_fund, amount in zip(self.funds, amounts):
            try:
                current[each_fund] = int(amount)
            except ValueError as error:
                raise ValueError('Cannot convert ' + str(amount) + ' into an int') from error

        New_DataFrame_toAppend = pd.DataFrame(current, index=[0])
        self.append_dataframe(New_DataFrame_toAppend)

        # update 2021-02-07
        # last_status = self._laststatus()
        last_status = self[self['date'] <= current['date']]._laststatus()
        for (each_fund, amount) in zip(self.funds, amounts):
            current[each_fund] += last_status[each_fund]
            print(current[each_fund])
        current['type'] = 'status'
        self.append_dataframe(pd.DataFrame(current, index=[0]))
        self._mysort()

    def _mysort(self):
        """
        Sort the DataFrame by date and then index, e.g. sort by date, but for all status and
        transaction lines with the same date, preserve their original order
        """
        # we will use the sort_values method of DataFrame, which cannot operate
        # on both columns and rows (indices).  So make a column duplicating index.
        self['indexer'] = self.index
        self.sort_values(by=['date', 'indexer'],  # sort first by date, then index
                         inplace=True)
        self.drop('indexer',  # remove auxiliary column; it served its purpose
                  axis=1,  # tell drop to remove a column, not index
                  inplace=True)

    def filewrite(self, trial=False):
        """
        Overwrite the existing csv with the updated version.  By default,
        saves existing version in the backup folder.

        INPUTS:
        trial: True or False, debug option to write to "trial" file
        (e.g. does not overwrite original file)
        """
        filesplit = self.file.split('/')
        base, extension = filesplit[-1].split('.')
        # return path terminated with '/', or empty string (in
        # case user is operating out of /home/rory/finance/
        # e.g. location of file, in which case you don't want leading
        # '/' in path)
        path = '/'.join(filesplit[:-1]) + ('/'.join(filesplit[:-1]) and '/')
        trial_string = '_trial' if trial else ''

        new_file = open(path + base + trial_string + '.' + extension,
                        mode='w'
                        )
        print('Writing to ' + path + base + trial_string + '.' + extension)
        x = [self.name, self.subname, ','.join(self.funds)]
        for entry in x:
            new_file.write(entry + '\n')

        # write the allocation dictionary
        for alloc in self.alloc:
            new_file.write(alloc.csv_str()+'\n')

        self.to_csv(new_file, index=False)
        new_file.close()

    def backup(self):
        """
        Copy existing csv file into the backup folder.
        """
        import subprocess

        filename = self.file.split('/')[-1]
        # assume no . in filename
        filename_root, filename_extension = filename.split('.')

        today = datetime.date.today()
        today_string = today.strftime('%Y-%m-%d')

        save_path = '/home/rory/finance/backup/'
        save_file = filename_root + today_string + '.' + filename_extension

        print('Making backup copy of %s to %s' % (self.file,
                                                  save_path + save_file)
              )

        subprocess.run(['cp', self.file, save_path + save_file])

    def performance(self):
        """
        Evaluate performance of each fund based on last two status lines.
        :return:
        """
        status_lines = self[self['type'] == 'status']
        dtime = status_lines.iloc[-1].date - status_lines.iloc[-2].date
        years = np.abs(dtime.days) / 365
        justfunds = status_lines[self.funds]
        change = justfunds.iloc[-1] / justfunds.iloc[-2]
        return (2.72 ** (np.log(change) / years) - 1) * 100

    def add_fund(self, name: str):
        """
        Add a new fund to account:
        - add new column (of zeros) to DataFrame
        - append name to self.funds
        - add new entry to self.alloc
        - invoke self.alloc_change() to set new allocations
        """
        if name in self:
            raise ValueError(("Trying to add fund {0} to account {1}: "
                              "fund already exists account."
                              ).format(name, self.name)
                             )

        print("Adding new fund {0} to account {1}:{2}.".format(name,
                                                               self.name,
                                                               self.subname)
              )
        self[name] = 0
        self.funds.append(name)

        print("Existing allocations:")
        self.alloc.print()

        try:
            key = input("Enter allocation: either one from above, or new: ")
            if key in [a.itype.name for a in self.alloc]:
                print("Appending to existing AllocationEntry")
                for a in self.alloc:
                    if key == a.itype.name:
                        a.fundlist.append(name)
            else:
                self.alloc.append(allocation.AllocationEntry(investment_types.__dict__[key],
                                                             0.0,
                                                             [name]))
            self.alloc.alloc_change()
        except:
            print("Adding fund to Allocation failed; removing fund from Account.")
            del self[name]
            self.funds.pop(-1)


class Portfolio(object):
    def __init__(self, accounts: List[Account], alloc: allocation.Allocation):
        for a in accounts:
            if not isinstance(a, Account):
                raise ValueError(('Porfolio.__init__: accounts parameter must be of type'
                                  ' Account; got {0}').format(type(a))
                                 )
        self.accounts = accounts
        if not isinstance(alloc, allocation.Allocation):
            raise ValueError(('Porfolio.__init__: alloc parameter must be of type'
                              ' Allocation; got {0}').format(type(alloc))
                             )
        self.alloc = alloc

    @property
    def total(self):
        subtotals = [a.total for a in self.accounts]
        return sum(subtotals)

    def service_allocations(self):
        x = [sum([acc.service_investment_type(a.itype) for acc in self.accounts]) for a in self.alloc]
        return x

    def rebalance(self):
        self.alloc.rebalance(self.service_allocations())
