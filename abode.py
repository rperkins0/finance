import numpy as np
import logging
from rate import Rate

log = logging.Logger(__name__, level=logging.DEBUG)
if not log.handlers:
    log.addHandler(logging.StreamHandler())


def round(func):
    """
    Decorator used so the the numpy array returned by functions is rounded (for prettier printing... no need to
    display 13 decimal places).
    """
    def newFunc(*args):
        array = func(*args)
        return array.round()
    return newFunc


class Abode:

    # default values to use
    INFLATION = Rate(rate=2.5)
    default_pmi_rate = Rate(rate=1.2)
    STD_DEDUCTION = 24800
    MARKET = Rate(rate=7.0, variance=5.0)
    CAPITAL_GAIN = 0.85                     # proceeds after capital gain tax (15%)

    marketReturnYearly, marketReturnCompounded = MARKET.cumulative(30)
    inflationYearly, inflationCompounded = INFLATION.cumulative(30)

    @classmethod
    def rerollMarket(cls):
        cls.marketReturnYearly, cls.marketReturnCompounded = cls.MARKET.cumulative(30)

    @classmethod
    def rerollInflation(cls):
        cls.inflationYearly, cls.inflationCompounded = cls.INFLATION.cumulative(30)

    @classmethod
    def reroll(cls):
        cls.rerollInflation()
        cls.rerollMarket()

    def oop(self) -> np.array:
        raise NotImplementedError()

    @round
    def opportunityCost(self,  oop=None):
        # array to hold opportunity cost each year
        oppCost = np.zeros(31)
        # cumulative out-of-pocket expenses
        if oop is None:
            oopCum = self.oop().cumsum()
        else:
            oopCum = oop.cumsum()
        for i in range(1, 31):
            oppCost[i] = (oopCum[i-1] + oppCost[0:i].sum()) * self.marketReturnYearly[i-1]
        return oppCost

    @round
    def opportunityCostRealized(self):
        return self.opportunityCost().cumsum() * self.CAPITAL_GAIN

    @round
    def oopInvested(self):
        return self.oop().cumsum() + self.opportunityCostRealized()
