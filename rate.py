"""
Define the Rate class, a base class which can cover: interest rates, rate of return on investment, mortgages, ect.

Rates can be static (fixed), or a variance can be specified.

Rates can generate returns over a fixed number of years.
"""
import numpy as np
import logging

log = logging.Logger(__name__, level=logging.DEBUG)
if not log.handlers:
    log.addHandler(logging.StreamHandler())


class Rate:
    def __init__(self, rate: float, variance: float = 0):
        """
        :param rate: enter as a percentage (e.g. "5" not "0.05")
        :param variance: optional  give the yearly variance (as percentage)
        """
        self.rate = rate
        self.variance = variance

    def generate(self, n) -> np.array:
        """
        Return a numpy array of the rate over n time intervals (e.g. years)
        """
        return np.random.normal(loc = self.rate/100,
                                scale = self.variance/100,
                                size = n)

    def cumulative(self, nYears):
        """
        Cascade the yearly returns (via generate() above) to get cumulative return each year.
        Returns an array that is nYears + 1 long, with the first entry being 1.0.
        In other words, the nth index is the accumulation after n years.
        """
        ratesYearly = self.generate(nYears)

        cumu = np.insert(ratesYearly.copy(),    # copy rate array
                         0,                     # insert at 0th index
                         1.0)                   # insert 1.0

        for n in range(1, len(cumu)):
            cumu[n] += 1.0
            cumu[n] *= cumu[n-1]
        return ratesYearly, cumu
