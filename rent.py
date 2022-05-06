import numpy as np
import pandas as pd
import logging
from rate import Rate
from abode import Abode
from abode import round

log = logging.Logger(__name__, level=logging.DEBUG)
if not log.handlers:
    log.addHandler(logging.StreamHandler())


class Rent(Abode):
    def __init__(self, rentMonthly):
        self.rentMonthly = rentMonthly
        self.rentYearly = rentMonthly * 12

    @round
    def rentPrices(self):
        return self.rentYearly * self.inflationCompounded[:-1]

    @round
    def oop(self, nYears=30):
        """
        Array of out-of-pocket expenses for each years.
        Length = nYears + 1, the 0th index being upfront expenses (typically 0 for renting)
        """
        oop = np.zeros(nYears+1)
        oop[1:] = self.rentPrices()
        return oop

    def pandaize(self) -> pd.DataFrame:
        data = {}
        data['Market'] = np.insert(self.marketReturnYearly, 0, np.nan).round(3) * 100
        data['Inflation'] = np.insert(self.inflationYearly, 0, np.nan).round(3) * 100
        data['Rent'] = self.rentPrices()
        data['OOP'] = self.oop()
        data['OppCostR'] = self.opportunityCostRealized()
        data['OOP_Invest'] = self.oopInvested()
        df = pd.DataFrame(data=data)
        return df

    def writeCsv(self, filename=None):
        if filename is None:
            filename = 'default.csv'
        df = self.pandaize()
        df.to_csv(filename)
