"""
Sample Data Utilities

Functions to create sample risk universes for testing and demos.
"""

from datetime import date
from typing import List, Tuple

from ..models import (
    RiskFactor, YieldCurve, SpreadCurve, FXRate, EquityIndex, MacroFactor,
    Counterparty, Contract, ContractType
)


def create_sample_universe() -> Tuple[List[RiskFactor], List[Counterparty], List[Contract]]:
    """
    Create a sample universe of risk factors, counterparties, and contracts for testing.
    
    Returns:
        Tuple of (risk_factors, counterparties, contracts)
    """
    
    # Create yield curves
    chf_swap = YieldCurve(
        factor_id="CHF_SWAP",
        currency="CHF",
        description="CHF Swap Curve",
        tenors=["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y"],
        rates=[1.5, 1.6, 1.7, 1.9, 2.1, 2.5, 2.8, 3.0]
    )
    
    eur_swap = YieldCurve(
        factor_id="EUR_SWAP",
        currency="EUR",
        description="EUR Swap Curve",
        tenors=["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y"],
        rates=[3.5, 3.6, 3.7, 3.8, 3.9, 4.0, 4.1, 4.2]
    )
    
    # Create spread curves
    chf_corp_a = SpreadCurve(
        factor_id="CHF_CORP_A",
        currency="CHF",
        rating="A",
        spread_type="credit",
        description="CHF Corporate A-rated Spread Curve",
        tenors=["1Y", "2Y", "5Y", "10Y"],
        spreads=[50, 60, 80, 100]
    )
    
    chf_corp_bbb = SpreadCurve(
        factor_id="CHF_CORP_BBB",
        currency="CHF",
        rating="BBB",
        spread_type="credit",
        description="CHF Corporate BBB-rated Spread Curve",
        tenors=["1Y", "2Y", "5Y", "10Y"],
        spreads=[100, 120, 150, 180]
    )
    
    # Create FX rates
    eurchf = FXRate(
        factor_id="EURCHF",
        currency_pair="EURCHF",
        base_currency="EUR",
        quote_currency="CHF",
        spot_rate=0.95
    )
    
    usdchf = FXRate(
        factor_id="USDCHF",
        currency_pair="USDCHF",
        base_currency="USD",
        quote_currency="CHF",
        spot_rate=0.88
    )
    
    # Create equity index
    smi = EquityIndex(
        factor_id="SMI",
        index_name="Swiss Market Index",
        current_level=11500.0
    )
    
    # Create macro factors
    ch_gdp = MacroFactor(
        factor_id="CH_GDP_GROWTH",
        macro_type="GDP_GROWTH",
        current_value=1.8,
        unit="%",
        description="Switzerland GDP Growth Rate"
    )
    
    ch_unemployment = MacroFactor(
        factor_id="CH_UNEMPLOYMENT",
        macro_type="UNEMPLOYMENT",
        current_value=2.1,
        unit="%",
        description="Switzerland Unemployment Rate"
    )
    
    risk_factors = [
        chf_swap, eur_swap,
        chf_corp_a, chf_corp_bbb,
        eurchf, usdchf,
        smi,
        ch_gdp, ch_unemployment
    ]
    
    # Create counterparties
    counterparties = [
        Counterparty(
            counterparty_id="CP001",
            name="Swiss Industrial Corp",
            rating="A",
            pd=0.005,
            recovery_rate=0.50,
            sector="Industrial",
            country="CH"
        ),
        Counterparty(
            counterparty_id="CP002",
            name="Euro Retail Ltd",
            rating="BBB",
            pd=0.015,
            recovery_rate=0.40,
            sector="Retail",
            country="DE"
        ),
        Counterparty(
            counterparty_id="CP003",
            name="Tech Innovations AG",
            rating="BBB+",
            pd=0.010,
            recovery_rate=0.45,
            sector="Technology",
            country="CH"
        )
    ]
    
    # Create sample contracts
    contracts = [
        Contract(
            contract_id="LOAN001",
            contract_type=ContractType.LOAN,
            currency="CHF",
            notional=10_000_000,
            maturity_date=date(2027, 12, 31),
            linked_yield_curve="CHF_SWAP",
            linked_spread_curve="CHF_CORP_A",
            counterparty_id="CP001",
            is_asset=True,
            rate=3.5
        ),
        Contract(
            contract_id="LOAN002",
            contract_type=ContractType.LOAN,
            currency="CHF",
            notional=5_000_000,
            maturity_date=date(2029, 6, 30),
            linked_yield_curve="CHF_SWAP",
            linked_spread_curve="CHF_CORP_BBB",
            counterparty_id="CP002",
            is_asset=True,
            rate=4.2
        ),
        Contract(
            contract_id="DEP001",
            contract_type=ContractType.DEPOSIT,
            currency="CHF",
            notional=8_000_000,
            maturity_date=date(2026, 3, 31),
            linked_yield_curve="CHF_SWAP",
            is_asset=False,
            rate=2.0
        ),
        Contract(
            contract_id="BOND001",
            contract_type=ContractType.BOND,
            currency="EUR",
            notional=3_000_000,
            maturity_date=date(2030, 12, 31),
            linked_yield_curve="EUR_SWAP",
            linked_spread_curve="CHF_CORP_A",
            counterparty_id="CP003",
            is_asset=True,
            rate=4.5
        )
    ]
    
    return risk_factors, counterparties, contracts
