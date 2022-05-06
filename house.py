import numpy as np
import pandas as pd
import logging
from rate import Rate
from abode import Abode
from abode import round

log = logging.Logger(__name__, level=logging.WARNING)
if not log.handlers:
    log.addHandler(logging.StreamHandler())


class Mortgage:
    """
    NORMALIZED mortgage, e.g. the principle is 1.
    """
    def __init__(self, rate: float, duration: int):
        """
        Accept rate as a float and convert to Rate class.
        Mortgages have no variance, so we se this to 0 in the
        constructed Rate instance.
        """
        self._rate = Rate(rate)  # self._rate will be Rate class
        # but self.rate is a @property defined below
        # public facing method for getting rate quickly
        self.duration = duration
        self.payment = self.calculate_payment()

    def calculate_payment(self):
        """
        Calculate the fixed yearly payment (normalized) that will pay off the loan by the end of the load duration.
        """
        decimal = self.rate / 100  # shorthand
        years = self.duration  # shorthand
        return decimal * (1 + decimal) ** years / \
               ( (1 + decimal) ** years - 1 )

    @property
    def rate(self):
        return self._rate.rate

    @rate.setter
    def rate(self, r):
        self._rate = Rate(r)
        self.payment = self.calculate_payment()  # automatically update payment

    def calculate_principle(self):
        """
        Return a numpy array with the paydown of the principle year by year.
        The nth index is the principle remaining after n years of payments.
        """
        schedule = np.zeros(self.duration + 1)
        schedule[0] = 1.0
        for index in range(1, self.duration):
            schedule[index] = (1.0 + self.rate/100) * schedule[index-1]
            schedule[index] -= self.payment
            log.debug("Year {0:02}: principle = {1:5.2f}".format(index, schedule[index]))
        return schedule

    def calculate_interest(self):
        """
        Return an array holding the normalized amount of interest payment each year.
        """
        return self.calculate_principle() * self.rate/100


def roll(func):
    """
    Decorator used in the "House" class below.
    In my current scheme, when considering payments over a 30 mortgage, we want arrays that are 31 elements long, e.g.
    with an "extra" element, the zeroth.
    However, a repeated operation is to shift the array, and fill the 0th index with 0.
    That is what this decorator does to a function that return an array of, say, 30.
    """
    def newFunc(obj):
        array = func(obj)
        rolledArray = np.roll(array, 1)
        rolledArray[0] = 0
        return rolledArray
    return newFunc


class House(Abode):

    # default values to use
    default_pmi_rate = Rate(rate=1.2)
    CLOSING_COST_BUY = 0.05
    CLOSING_COST_SELL =0.06

    def __init__(self,
                 price: int,                    # sale price of house
                 mortgage: Mortgage,
                 tax,                           # initial yearly tax
                 inflation: Rate = None,        # inflation value that will scale everything
                 appreciation: Rate = None,     # rate of home appreciation, often set equal to inflation
                 upkeep=1.,                     # money needed to maintain property (percentage)
                 insurance=0.5,                 # home owners' insurance
                 down=20.,                      # down payment fraction
                 closingCostBuy=5.,             # closing costs on purchase
                 closingCostSell=6.,            # closing cost on sale
                 rollClosingCost=False,         # roll costs into mortgage (True) or pay upfront (False)
                 pmi_rate=None
                 ):
        self.price = price
        self.mortgage = mortgage
        self.tax = tax
        self.inflation = inflation if inflation else self.INFLATION
        self.appreciation = appreciation if appreciation else self.inflation
        self.upkeep = upkeep
        self.insurance = insurance
        self.down = down
        self.closingCostBuy = closingCostBuy
        self.closingCostSell = closingCostSell
        self.rollClosingCost = rollClosingCost

        self.pmi_rate = pmi_rate if pmi_rate else House.default_pmi_rate

        self.loan = price * (1-down/100)
        if rollClosingCost:
            self.loan += price * closingCostBuy/100

    @round
    def value(self, nYears):
        """
        Return a numpy array of house values due to yearly appreciation.
        Length of array will be nYears+1, with the nth index being the value after n years,
        and the 0th index being the value at time of purchase.
        Consider adding variance to the appreciation rate.
        """
        _, compounded = self.appreciation.cumulative(nYears)
        return self.price * compounded

    @round
    def equity(self):
        """
        Return a numpy array of equity: the amount of the mortgage paid off.
        Length of array will be self.duration+1, with the nth index being the value after n years,
        and the 0th index being the value at time of purchase.
        """
        return ((1 - self.mortgage.calculate_principle()) * self.loan) + self.down/100 * self.price

    @round
    def principal(self):
        """
        Return a numpy array of principal: the amount of the mortgage remaining.
        Length of array will be self.duration+1, with the nth index being the principal after n years,
        and the 0th index being the loan amount at time of purchase.
        """
        return self.mortgage.calculate_principle() * self.loan

    @round
    def proceeds(self):
        """
        When selling a home, you must subtract closing costs from the sale, then the loan must be repaid.
        Return an array of length self.duration + 1 in which the nth index contains the proceeds of the sale if
        the house is sold after n years.
        """
        valueByYear = self.value(self.mortgage.duration)
        realizedValue = valueByYear * (1 - self.closingCostSell/100)
        net = realizedValue - self.principal()
        return net

    @round
    @roll
    def pmi(self):
        """
        You pay PMI when home equity is below 20% of home value.
        Returns a numpy array with PMI payments each year.
        Note that first index (zero) is always zero.
        """
        equity = self.equity()
        pmiYearlyPayment = self.loan * self.pmi_rate.rate/100
        # use numpy's 'where' function to identify year's when the equity is below 20%
        # and, for those years, apply the yearly PMI fee
        pmiPayments = np.where(equity < 0.2 * self.price,   # search condition
                             pmiYearlyPayment,              # for those years, apply PMI fee
                             0)                             # all other years have no PMI fee
        return pmiPayments

    def mortgagePayment(self) -> float:
        """Returns yearly mortgage payment, a fixed quantity"""
        return self.mortgage.calculate_payment() * self.loan

    @round
    @roll
    def mortgagePayments(self) -> float:
        """Returns array of yearly mortgage payment, a fixed quantity"""
        return np.ones(self.mortgage.duration + 1) * self.mortgagePayment()

    @round
    @roll
    def taxPayments(self) -> np.array:
        _, appreciationCumulative = \
            self.appreciation.cumulative(self.mortgage.duration)
        # recall appreciationCumulative will be of length nYears+1
        return self.tax * appreciationCumulative

    @round
    @roll
    def upkeepPayments(self):
        _, cumulative_appreciation = self.appreciation.cumulative(self.mortgage.duration)
        return self.upkeep/100 * cumulative_appreciation * self.price

    @round
    @roll
    def insurancePayments(self) -> np.array:
        _, appreciationCumulative = \
            self.appreciation.cumulative(self.mortgage.duration)
        # recall appreciationCumulative will be of length nYears+1
        return self.insurance / 100 * self.price * appreciationCumulative


    def mortgageDeduction(self):
        pass

    @round
    def oop(self):
        """Calculate out of pocket expenses"""
        expenses = self.upkeepPayments()
        expenses += self.taxPayments()
        expenses += self.mortgagePayments()
        expenses += self.insurancePayments()
        # expenses += self.mortgageDeduction()
        expenses[0] += self.down/100 * self.price
        if not self.rollClosingCost:
            # if the closing costs were not rolled into mortgage, they were paid out-of-pocket
            # at time of purchase, so add them to the 0th index
            expenses[0] += self.closingCostBuy/100 * self.price
        return expenses.round()

    @round
    def interest(self):
        """
        Array of interest costs due to mortgage.
        Array lenght is self.mortgage.duration+1; the nth entry is the mortgage paid on the nth year.
        The 0th entry is zero.
        """
        interestArray = self.principal() * self.mortgage.rate / 100
        return np.roll(interestArray, 1)

    def pandaize(self) -> pd.DataFrame:
        data = {}
        data['Market'] = np.insert(self.marketReturnYearly, 0, np.nan).round(3) * 100
        data['Inflation'] = np.insert(self.inflationYearly, 0, np.nan).round(3) * 100
        data['Interest'] = self.interest()
        data['Principal'] = self.principal()
        data['Value'] = self.value(self.mortgage.duration)
        data['Proceeds'] = self.proceeds()
        data['Tax'] = self.taxPayments()
        data['Upkeep'] = self.upkeepPayments()
        data['Insurance'] = self.insurancePayments()
        data['PMI'] = self.pmi()
        data['OOP'] = self.oop()
        data['OppCostR'] = self.opportunityCostRealized()
        data['OOP_Invest']  = self.oopInvested()
        data['NetLoss']  = self.oopInvested() - self.proceeds()
        df = pd.DataFrame(data=data)
        return df

    def writeCsv(self, filename=None):
        if filename is None:
            filename = 'default.csv'
        df = self.pandaize()
        df.to_csv(filename)


def example_house():
    return House(500000,
                 Mortgage(3., 30),
                 tax=5000,
                 down=10)


def exampleMD():
    return House(450000,
                 Mortgage(3., 30),
                 tax=6000,
                 down=20)


def exampleCA():
    return House(700000,
                 Mortgage(3., 30),
                 tax=5500,
                 down=20)