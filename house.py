import numpy as np
import logging

log = logging.Logger(__name__, level=logging.DEBUG)
if not log.handlers:
    log.addHandler(logging.StreamHandler())

class Rate:
    def __init__(self, rate: float, variance: float = 0):
        self.rate = rate
        self.variance = variance

    def generate(self, n):
        """
        Return an instance of the rate over n time intervals (e.g. years)
        """
        return np.random.normal(loc = self.rate/100,
                                scale = self.variance/100,
                                size = n)

    def cumulative(self, n):
        """
        Like generate, but cascade the multiplications overs the years.
        The first entry is 1.0.
        In other words, the nth index is the accumulation over n years.
        """
        rates = self.generate(n)
        cumu = rates.copy()
        cumu[0] = 1.
        for n in range(1, len(cumu)):
            cumu[n] += 1.0
            cumu[n] *= cumu[n-1]
        return rates, cumu


class Mortgage:
    """
    NORMALIZED mortgage
    """
    def __init__(self, rate: float, duration: int):
        """
        Accept rate as a float and convert to Rate class.
        """
        self._rate = Rate(rate) # self._rate will be Rate class
        # but self.rate is a @property defined below
        # public facing method for getting rate quickly
        self.duration = duration
        self.payment = self.calculate_payment()

    def calculate_payment(self):
        decimal = self.rate / 100  # shorthand
        years = self.duration  # shorthand
        return decimal * (1 + decimal) ** years / \
               ( (1 + decimal) ** years -1 )

    @property
    def rate(self):
        return self._rate.rate

    @rate.setter
    def rate(self, r):
        self._rate = Rate(r)
        self.payment = self.calculate_payment() # automatically update payment

    def calculate_principle(self):
        """
        Return a numpy array with the paydown of the principle year by year.
        The nth index is the principle remaining after n years of payments.
        """
        schedule = np.zeros(self.duration)
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
        return self.calculate_principle()*self.rate



class Market:
    def __init__(self, rate, inflation):
        self.rate = rate
        self.inflation = inflation


class House:

    # default values to use
    default_inflation = Rate(rate=2.)

    def __init__(self,
                 price: int, # sale price of house
                 mortgage: Mortgage,
                 tax,  # initial yearly tax
                 inflation: Rate = None,  # inflation value that will scale everything
                 appreciation: Rate = None,  # rate of home appreciation, often set equal to inflation
                 upkeep=1., # money needed to
                 insurance=0.5, # home owners' insurance
                 down=20.,  # down payment fraction
                 closingcost=6.  # closing cost percentage
                 ):
        self.price = price
        self.mortgage = mortgage
        self.tax = tax
        self.inflation = inflation if inflation else House.default_inflation
        self.appreciation = appreciation if appreciation else self.inflation
        self.upkeep = upkeep
        self.insurance = insurance
        self.down = down
        self.closingcost = closingcost

        self.loan = price * (1-down/100)

    def value(self, years):
        """
        Return a numpy array whose values reflect the appreciation of the home values year by year
        Consider adding variance to the appreciation rate.
        """
        _, compounded = self.appreciation.cumulative(years)
        return self.price * compounded

    def equity(self):
        return ((1 - self.mortgage.calculate_principle()) * self.loan) + self.down/100 * self.price

    def pmi(self):
        pass

    def mortgage_payment(self):
        """Returns yearly mortgage payment, a fixed quantity"""
        return self.mortgage.calculate_payment() * self.loan

    def calculate_taxes(self):
        _, cumulative_appreciation = self.appreciation.cumulative(self.mortgage.duration)
        return self.tax * cumulative_appreciation

    def calculate_upkeep(self):
        _, cumulative_appreciation = self.appreciation.cumulative(self.mortgage.duration)
        return self.upkeep * cumulative_appreciation

    def oop(self):
        """Calculate out of pocket expenses"""
        # return self.calculate_taxes() + \
        #     self.calculate_upkeep() + \
        #     
        pass