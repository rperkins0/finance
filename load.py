import investment_types
import investment
import allocation

v = investment.Account(file='../vanguard.csv')
td_i = investment.Account(file='../ameritrade_i.csv')
td_r = investment.Account(file='../ameritrade_r.csv')
td_b = investment.Account(file='../ameritrade_b.csv')
mit401 = investment.Account(file='../fidelity_401.csv')
juni = investment.Account(file='../fidelity_529.csv')
# hsa = investment.account(file='../healthhub.csv')
tiaa = investment.Account(file='../tiaa.csv')

my_alloc = allocation.Allocation([allocation.AllocationEntry(investment_types.Stock(), 0.25, []),
                                  allocation.AllocationEntry(investment_types.Bond(), 0.25, []),
                                  allocation.AllocationEntry(investment_types.StockInt(), 0.25, []),
                                  allocation.AllocationEntry(investment_types.RealEstate(), 0.25, []),
                                  ])

td  = investment.Portfolio(accounts=[td_i,td_r, td_b],
                           alloc=my_alloc)