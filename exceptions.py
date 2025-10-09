# Exceptions

class HighRiskError(Exception):
    pass

class HighMarketRiskError(Exception):
    pass

class HighAccountRiskError(Exception):
    pass

class UnsuitableAccountValueError(Exception):
    pass

class ShortOnStockError(Exception):
    pass

# 该class目前未检查到引用情形，保留代码以备不时之需
class EntryPointBug(Exception):
    pass

# 该class目前未检查到引用情形，保留代码以备不时之需
class BuyBullEntryBug(Exception):
    pass
# 该class目前未检查到引用情形，保留代码以备不时之需
class SellBullEntryBug(Exception):
    pass

# 该class目前未检查到引用情形，保留代码以备不时之需
class BuyBearEntryBug(Exception):
    pass
# 该class目前未检查到引用情形，保留代码以备不时之需
class SellBearEntryBug(Exception):
    pass

class NoEntryPointError(Exception):
    pass

class NoBuyEntryError(NoEntryPointError):
    pass

class NoSellEntryError(NoEntryPointError):
    pass

class PositionFullError(HighAccountRiskError):
    pass

class NeitherPositionNorFundError(HighAccountRiskError):
    pass

class NoOptionContractFoundError(HighMarketRiskError):
    pass

class NoPutContractError(NoOptionContractFoundError):
    pass
class NoCallContractError(NoOptionContractFoundError):
    pass

class NoCoveredCallContractError(NoCallContractError):
    pass

class NoCoveredPutContractError(NoPutContractError):
    pass


class BuyInRealAccountError(HighAccountRiskError):
    pass

class NoGreeksFoundError(HighMarketRiskError):
    """Custom exception for when option greeks are not found."""
    pass

class PriceNotAvailableError(HighMarketRiskError):
    """Custom exception for when a price cannot be obtained."""
    pass

class ContractQualificationError(Exception):
    """Custom exception for failures during contract qualification."""
    pass

class OrderFailedError(Exception):
    """Custom exception for when an order placement fails for various reasons."""
    pass