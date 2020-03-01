import csv
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd


class fund(pd.DataFrame):
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
        if data == None:
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
        return fund

    def fileload(self, path):
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
        file = open(path, mode='r')

        # because DataFrame.to_csv() method writes extraneous commas,
        # must do some string juggling while parsing header

        # read first line and extract name
        name = file.readline().strip().split(',')[0]
        # read second line and extract subname
        subname = file.readline().strip().split(',')[0]
        # read third line and extract list of funds
        funds = file.readline().strip().split(',')
        while '' in funds: funds.remove('')
        # read allocations
        percentage = 0.
        alloc = {}
        while percentage < 1.0:
            line = file.readline().strip().split(',')
            while '' in line: line.remove('')
            key = line.pop(0)
            percent = float(line.pop(0))
            alloc[key] = (percent, set(line))
            percentage += percent

        temp = pd.read_csv(file, parse_dates=['date'])
        # column 'date' imported as datetime object
        # convert it to just a date object
        temp['date'] = temp['date'].dt.date

        file.close()
        return (name, subname, path, funds, alloc, temp)

    def status(self):
        """
        Add a 'status' line to the DataFrame.
        """
        today = datetime.datetime.date(datetime.datetime.now())
        current = {}
        current['type'] = 'status'
        current['date'] = today
        for f in self.funds:
            fund_status_string = input("Current value of " + f)
            current[f] = int(fund_status_string)

        New_DataFrame_toAppend = pd.DataFrame(current, index=[0])

        # can't believe this works, but it does and retains metadata!
        super().__init__(data=self.append(New_DataFrame_toAppend,
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

    def rebalance(self, new_money=0):
        """
        Calculate how much of each fund to sell/buy in order to
        rebalance portfolio.  This does not actually update
        the DataFrame.

        Input: new_money -- additional funds to invest
        """
        latest = self._laststatus()

        total = self.total + new_money

        for key, val in self.alloc.items():
            value = sum([latest[fund] for fund in val[1]])
            print(key,
                  "$%d" % (value),
                  '%1.3f' % (value / total),
                  '%1.3f' % val[0],
                  'SELL' if value / total > val[0] else 'BUY',
                  int(val[0] * total - value),
                  sep='\t'
                  )

    def transact(self,
                 amounts=False,
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

        today = datetime.datetime.date(datetime.datetime.now())

        current = {'type': 'transact'}
        current['date'] = today
        for each_fund, amount in zip(self.funds, amounts):
            current[each_fund] = amount
        New_DataFrame_toAppend = pd.DataFrame(current, index=[today])
        super().__init__(data=self.append(New_DataFrame_toAppend,
                                          sort=False,
                                          ignore_index=True
                                          )
                         )

    def filewrite(self,
                  trial=False,
                  ):
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
        trial_string = 'trial_' if trial else ''

        new_file = open(path + base + trial_string + '.' + extension,
                        mode='w'
                        )
        print('Writing to ' + path + base + trial_string + '.' + extension)
        x = [self.name, self.subname, ','.join(self.funds)]
        for entry in x:
            new_file.write(entry + '\n')

        # write the allocation dictionary
        for (key, value) in self.alloc.items():
            new_file.write(','.join([key,
                                     str(value[0]),
                                     *value[1]
                                     ])
                           )
            new_file.write('\n')

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
        status_lines = self._obj.loc(self._obj['type' == 'status'])

    def alloc_change(self):
        """
        Interactively change the allocation levels.

        Checks that entries are valid number and total to 1.0.
        """
        tally = 0.0
        new_alloc_dict = {}
        for key,val in self.alloc.items():
            try:
                new_alloc = input('New allocation for'+key+': ') or val[0]
                new_alloc = float(new_alloc)
                new_alloc_dict[key] = (new_alloc,val[1])
                tally += new_alloc
            except ValueError:
                print("Must enter a number")
                return
        if tally != 1.0:
            print('Entries must total 1.0')
            return
        else:
            self.alloc = new_alloc_dict
