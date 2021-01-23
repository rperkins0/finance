"""
Classes representing investment types.
"""


class InvestmentType(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Stock(InvestmentType):
    def __init__(self, name='Stock'):
        super().__init__(name=name)


class StockInt(Stock):
    def __init__(self, name='StockInt'):
        super().__init__(name=name)


class Bond(InvestmentType):
    def __init__(self, name='Bond'):
        super().__init__(name=name)


class RealEstate(InvestmentType):
    def __init__(self, name='RealEstate'):
        super().__init__(name=name)


class Cash(InvestmentType):
    def __init__(self, name='Cash'):
        super().__init__(name=name)


class TargetDate(InvestmentType):
    def __init__(self, name='TargetDate'):
        super().__init__(name=name)


stock = Stock()
stockInt = StockInt()
bond = Bond()
targetDate = TargetDate()
realEstate = RealEstate()

# Fidelity funds
MAXFSTMX6 = Stock(name='MAXFSTMX6')  # total US market
MAFSMKX94 = Stock(name='MAFSMKX94')  # S&P 500 index
MAXFIIX92 = StockInt(name='MAXFIIX92')
MAXITI900 = Bond(name='MAXFIIX92')  # treasury index
