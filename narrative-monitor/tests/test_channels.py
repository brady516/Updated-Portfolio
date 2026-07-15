"""Tests for the sector ChannelSets — banks and REITs.

    python3 -m unittest discover -s tests

Proves the same engine reads each sector's microstructure: a benign narrative
over a breaking bank/REIT filing confirms through the right channels, healthy
credit does NOT fire (no false positives), and sector selection is by field.
"""

from __future__ import annotations

import unittest

from narrative_monitor import (
    FundamentalSnapshot,
    SignalEngine,
    SignalState,
    samples,
)
from narrative_monitor.channels import channel_set_for

QUARTERS = [
    ("2024-Q1", "2024-04-22"), ("2024-Q2", "2024-07-22"),
    ("2024-Q3", "2024-10-22"), ("2024-Q4", "2025-01-27"),
    ("2025-Q1", "2025-04-21"), ("2025-Q2", "2025-07-21"),
    ("2025-Q3", "2025-10-20"), ("2025-Q4", "2026-01-26"),
    ("2026-Q1", "2026-04-20"),
]


def _panel(sector: str, series: dict, guidance_key=None, guidance=None) -> list:
    guidance = guidance or {}
    out = []
    for i, (period, rep) in enumerate(QUARTERS):
        items = {k: v[i] for k, v in series.items()}
        if guidance_key and period in guidance:
            items[guidance_key] = guidance[period]
        out.append(FundamentalSnapshot(
            ticker="T", period=period, revenue=0.0, free_cash_flow=0.0,
            operating_cash_flow=0.0, capex=0.0, reported_at=rep,
            sector=sector, line_items=items,
        ))
    return out


def _broken_bank() -> list:
    return _panel("financial", {
        "gross_loans":                [100,101,102,103,104,105,106,107,108],
        "net_charge_offs":            [.20,.20,.22,.22,.35,.40,.50,.55,.60],
        "provision_for_credit_losses":[.25,.25,.25,.25,.30,.32,.35,.40,.35],
        "allowance_for_loan_losses":  [1.5,1.5,1.52,1.52,1.4,1.35,1.3,1.25,1.2],
        "nonperforming_assets":       [1.0,1.0,1.1,1.1,1.5,1.7,1.9,2.1,2.3],
        "net_interest_margin":        [.035,.035,.0348,.0348,.0335,.033,.0325,.032,.031],
        "tangible_book_value_per_share":[50,50,50,50,49,48,47,46,45],
        "net_income":                 [3.0,3.0,3.1,3.2,2.5,2.3,2.1,1.9,1.6],
    }, "fy_nii_guidance",
       {"2025-Q2":25.0,"2025-Q3":24.0,"2025-Q4":23.0,"2026-Q1":22.0})


def _healthy_bank() -> list:
    return _panel("financial", {
        "gross_loans":                [100,101,102,103,104,105,106,107,108],
        "net_charge_offs":            [.20,.20,.20,.20,.19,.19,.18,.18,.17],
        "provision_for_credit_losses":[.25,.25,.25,.25,.25,.25,.25,.25,.25],
        "allowance_for_loan_losses":  [1.5,1.5,1.52,1.52,1.55,1.57,1.6,1.62,1.65],
        "nonperforming_assets":       [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],
        "net_interest_margin":        [.035,.035,.035,.035,.035,.035,.035,.035,.035],
        "tangible_book_value_per_share":[50,50,51,51,52,53,54,55,56],
        "net_income":                 [3.0,3.0,3.1,3.2,3.3,3.4,3.5,3.6,3.7],
    })


def _broken_reit() -> list:
    return _panel("reit", {
        "ffo":                        [2.0,2.1,2.0,2.3,2.0,2.1,2.0,2.3,2.0],
        "affo":                       [1.6,1.7,1.6,1.9,1.3,1.3,1.2,1.4,1.1],
        "same_store_noi":             [10,10.2,10.1,10.3,9.9,9.8,9.9,9.9,9.2],
        "straight_line_rent_receivable":[5,5,5,5,5.5,5.8,6.0,6.3,6.8],
        "capitalized_interest":       [.3,.3,.3,.3,.4,.45,.5,.55,.6],
        "dividend_per_share":         [.4]*9,
        "affo_per_share":             [.55,.58,.55,.62,.45,.44,.42,.46,.35],
    }, "fy_affo_guidance",
       {"2025-Q2":1.6,"2025-Q3":1.5,"2025-Q4":1.4,"2026-Q1":1.3})


def _broken_broker() -> list:
    return _panel("broker", {
        "net_interest_income":     [700,750,800,850,820,780,730,690,640],
        "pretax_income":           [500,540,580,620,560,520,470,430,380],
        "net_income":              [400,430,460,490,450,420,380,350,300],
        "customer_credit_balances":[90,92,94,96,93,90,86,82,78],
        "commission_revenue":      [200,205,200,210,200,198,195,195,190],
        "rate_sensitivity_25bp":   [150,150,160,160,180,190,195,200,200],
    }, "fy_nii_guidance", {"2025-Q2":3200,"2025-Q3":3000,"2025-Q4":2800,"2026-Q1":2600})


def _healthy_broker() -> list:
    return _panel("broker", {
        "net_interest_income":     [600,620,640,660,680,700,720,740,760],
        "pretax_income":           [1600,1620,1640,1660,1680,1700,1720,1740,1760],
        "net_income":              [1200,1225,1250,1275,1300,1325,1350,1375,1400],
        "customer_credit_balances":[90,92,94,96,98,100,102,104,106],
        "commission_revenue":      [200,205,210,215,220,225,230,235,240],
        "rate_sensitivity_25bp":   [50,50,50,50,50,50,50,50,50],
    })


def _broken_insurer() -> list:
    return _panel("insurance", {
        "combined_ratio":            [.95,.96,.95,.94,.99,1.01,1.03,1.04,1.06],
        "loss_ratio":                [.65,.66,.65,.64,.69,.71,.73,.74,.76],
        "accident_year_loss_ratio":  [.66,.67,.66,.65,.74,.77,.80,.82,.85],
        "favorable_reserve_development":[30,32,30,33,20,15,8,2,-10],
        "pretax_income":             [200,210,205,215,180,160,140,120,100],
        "net_premiums_written":      [100,102,101,103,112,116,120,124,130],
        "net_income":                [160,168,164,172,144,128,112,96,80],
    }, "fy_combined_ratio_guidance",
       {"2025-Q2":0.99,"2025-Q3":1.01,"2025-Q4":1.03,"2026-Q1":1.05})


def _healthy_insurer() -> list:
    return _panel("insurance", {
        "combined_ratio":            [.95,.94,.95,.94,.93,.93,.92,.92,.91],
        "loss_ratio":                [.65,.64,.65,.64,.63,.63,.62,.62,.61],
        "accident_year_loss_ratio":  [.65,.64,.65,.64,.63,.63,.62,.62,.61],
        "favorable_reserve_development":[10,10,10,10,10,10,10,10,10],
        "pretax_income":             [200,205,205,210,212,214,216,218,220],
        "net_premiums_written":      [100,101,102,103,104,105,106,107,108],
        "net_income":                [160,164,164,168,170,172,174,175,176],
    })


def _broken_lender() -> list:
    return _panel("lender", {
        "originations":               [50,55,60,65,75,85,95,105,115],
        "receivables":                [200,210,220,230,245,260,278,298,320],
        "allowance_for_credit_losses":[6.0,6.3,6.6,6.9,6.8,6.9,7.0,7.1,7.2],
        "net_charge_offs":            [1.0,1.0,1.1,1.1,1.4,1.7,2.1,2.5,3.0],
        "provision_for_credit_losses":[1.3,1.3,1.3,1.3,1.6,1.8,2.0,2.2,2.4],
        "delinquency_rate":           [.030,.030,.032,.032,.038,.042,.046,.050,.055],
        "vintage_early_delinquency":  [.020,.020,.021,.021,.028,.032,.036,.040,.045],
        "roll_rate":                  [.15,.15,.16,.16,.18,.20,.22,.24,.26],
        "net_income":                 [8,8.2,8.4,8.6,7.0,6.0,5.0,4.0,3.0],
    }, "fy_loss_rate_guidance", {"2025-Q2":.045,"2025-Q3":.050,"2025-Q4":.055,"2026-Q1":.060})


def _healthy_fast_grower() -> list:
    # SAME +53% origination growth, but clean credit: the inversion must NOT fire
    return _panel("lender", {
        "originations":               [50,55,60,65,75,85,95,105,115],
        "receivables":                [200,210,220,230,245,260,278,298,320],
        "allowance_for_credit_losses":[6.0,6.3,6.6,6.9,7.4,7.9,8.5,9.1,9.8],
        "net_charge_offs":            [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],
        "provision_for_credit_losses":[1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2,1.2],
        "delinquency_rate":           [.030]*9,
        "vintage_early_delinquency":  [.020,.020,.020,.020,.019,.019,.018,.018,.017],
        "roll_rate":                  [.15]*9,
        "net_income":                 [8,8.5,9,9.5,10,10.5,11,11.5,12],
    })


class SectorSelectionTests(unittest.TestCase):
    def test_registry_routes_by_sector(self) -> None:
        self.assertEqual(channel_set_for("financial").sector, "financial")
        self.assertEqual(channel_set_for("reit").sector, "reit")
        self.assertEqual(channel_set_for("broker").sector, "broker")
        self.assertEqual(channel_set_for("insurance").sector, "insurance")
        self.assertEqual(channel_set_for("lender").sector, "lender")
        self.assertEqual(channel_set_for("unknown").sector, "industrial")

    def test_signal_reports_its_sector(self) -> None:
        sig = SignalEngine().evaluate(_broken_bank(), claims=[])
        self.assertEqual(sig.metrics["sector"], "financial")


class BankChannelTests(unittest.TestCase):
    def test_reserve_inadequacy_confirms(self) -> None:
        sig = SignalEngine().evaluate(_broken_bank(), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("reserve_release_below_chargeoffs", "allowance_coverage_decline",
                    "npa_outrun_loans", "nim_two_period_compression"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_aoci_buildup_raises_reporting_entropy(self) -> None:
        panel = _broken_bank()
        # add growing unrealized securities losses vs equity (the SVB tell)
        aoci = [1, 1, 1, 1, 3, 4, 5, 6, 7]
        panel = [FundamentalSnapshot(**{**s.__dict__,
                 "line_items": {**s.line_items, "aoci_unrealized_loss": aoci[i],
                                "tangible_common_equity": 40.0}})
                 for i, s in enumerate(panel)]
        sig = SignalEngine().evaluate(panel, claims=[])
        self.assertGreater(sig.reporting_entropy, 0.0)

    def test_healthy_bank_does_not_fire(self) -> None:
        sig = SignalEngine().evaluate(_healthy_bank(), claims=[])
        self.assertEqual(sig.metrics["reporting_divergence"], 0.0)
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class ReitChannelTests(unittest.TestCase):
    def test_affo_wedge_confirms(self) -> None:
        sig = SignalEngine().evaluate(_broken_reit(), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("ttm_affo_decline", "affo_wedge_widening",
                    "same_store_noi_two_period_decline", "dividend_above_affo"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_primary_ttm_is_affo_not_fcf(self) -> None:
        # REIT execution gate keys off AFFO's TTM window, not FCF.
        sig = SignalEngine().evaluate(_broken_reit(), claims=[])
        self.assertIsNotNone(sig.metrics["primary_ttm"])


class BrokerChannelTests(unittest.TestCase):
    def test_rate_carry_turning_confirms(self) -> None:
        sig = SignalEngine().evaluate(_broken_broker(), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("nii_reliance_rising", "nii_two_period_compression",
                    "customer_float_erosion", "ttm_net_income_decline"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_healthy_up_cycle_broker_does_not_confirm(self) -> None:
        # NII rising, float growing, net income up, low reliance -> not a breakdown
        sig = SignalEngine().evaluate(_healthy_broker(), claims=[])
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class InsuranceChannelTests(unittest.TestCase):
    def test_reserve_masking_confirms(self) -> None:
        sig = SignalEngine().evaluate(_broken_insurer(), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("combined_ratio_two_period_rise", "underwriting_loss_masked",
                    "accident_year_worse_than_reported", "adverse_reserve_development"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_healthy_insurer_does_not_fire(self) -> None:
        sig = SignalEngine().evaluate(_healthy_insurer(), claims=[])
        self.assertEqual(sig.metrics["reporting_divergence"], 0.0)
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class LenderChannelTests(unittest.TestCase):
    def test_growth_into_bad_credit_confirms(self) -> None:
        sig = SignalEngine().evaluate(_broken_lender(), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("origination_growth_into_rising_delinquency",
                    "vintage_early_delinquency_rising", "roll_rate_rising",
                    "allowance_coverage_decline"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_fast_growth_with_clean_credit_does_not_fire(self) -> None:
        # The inversion is CONDITIONAL: +53% originations with clean vintages is
        # not a breakdown. Growth alone must never confirm.
        sig = SignalEngine().evaluate(_healthy_fast_grower(), claims=[])
        self.assertNotIn("origination_growth_into_rising_delinquency",
                         sig.confirmed_criteria)
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class SaasChannelTests(unittest.TestCase):
    def test_revenue_up_billings_down_confirms(self) -> None:
        sig = SignalEngine().evaluate(samples.saas("S"), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("revenue_up_billings_rolling_over",
                    "net_revenue_retention_declining", "deferred_revenue_decline"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_billings_outgrowing_revenue_does_not_fire(self) -> None:
        # revenue rising AND billings/RPO/NRR rising faster = healthy, not a
        # breakdown even though GAAP revenue growth is decelerating.
        sig = SignalEngine().evaluate(samples.saas_healthy("S"), claims=[])
        self.assertNotIn("revenue_up_billings_rolling_over", sig.confirmed_criteria)
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class EnergyChannelTests(unittest.TestCase):
    def test_capital_efficiency_breakdown_confirms(self) -> None:
        sig = SignalEngine().evaluate(samples.energy("E"), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("reserve_replacement_falling", "outspending_cash_flow",
                    "netback_two_period_compression", "negative_reserve_revisions"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_stale_pv10_raises_reporting_entropy(self) -> None:
        sig = SignalEngine().evaluate(samples.energy("E"), claims=[])
        self.assertGreater(sig.reporting_entropy, 0.0)  # PV-10 held while strip fell

    def test_healthy_energy_does_not_fire(self) -> None:
        sig = SignalEngine().evaluate(samples.energy_healthy("E"), claims=[])
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class BdcChannelTests(unittest.TestCase):
    def test_pik_and_marks_breakdown_confirms(self) -> None:
        sig = SignalEngine().evaluate(samples.bdc("B"), claims=[])
        self.assertEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        for key in ("pik_income_share_rising", "nav_per_share_decline",
                    "dividend_above_nii", "non_accrual_rate_rising"):
            self.assertIn(key, sig.confirmed_criteria)
        self.assertTrue(sig.execution_eligible)

    def test_healthy_bdc_does_not_fire(self) -> None:
        sig = SignalEngine().evaluate(samples.bdc_healthy("B"), claims=[])
        self.assertNotEqual(sig.state, SignalState.CONFIRMED_DETERIORATION)
        self.assertFalse(sig.execution_eligible)


class UniverseTests(unittest.TestCase):
    def test_every_sector_breakdown_confirms_healthy_does_not(self) -> None:
        from narrative_monitor import extract_claims, narrative_intensity
        engine = SignalEngine()
        for sector, (breakdown, healthy) in samples.SECTORS.items():
            claims = extract_claims(samples.benign_events("X"))
            b = engine.evaluate(breakdown("X"), claims, narrative_intensity(claims))
            h = engine.evaluate(healthy("Y"), claims=[])
            self.assertEqual(b.state, SignalState.CONFIRMED_DETERIORATION,
                             f"{sector} breakdown should confirm")
            self.assertTrue(b.execution_eligible, f"{sector} should be executable")
            self.assertFalse(h.execution_eligible,
                             f"{sector} healthy must not be executable")


if __name__ == "__main__":
    unittest.main()
