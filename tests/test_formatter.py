import unittest

from models import PriceEstimate, TradeListing
from services.formatter import format_price_estimate


class FormatterTest(unittest.TestCase):
    def test_formats_price_estimate_in_chinese(self):
        estimate = PriceEstimate(
            item_name="水井之心 (鑽石)",
            league="Runes of Aldur",
            median=24,
            low=20,
            high=28,
            currency="exalted",
            confidence="中",
            valid_count=6,
            total_count=8,
            source="trade2",
            trade_url="https://www.pathofexile.com/trade2/search/poe2/Runes%20of%20Aldur/abc123",
            reference_listings=[
                TradeListing(amount=20, currency="exalted", account="seller1"),
                TradeListing(amount=24, currency="exalted", account="seller2"),
            ],
        )

        text = format_price_estimate(estimate)

        self.assertIn("水井之心 (鑽石)", text)
        self.assertIn("联盟：Runes of Aldur", text)
        self.assertIn("估价：20 - 28 exalted", text)
        self.assertIn("中位数：24 exalted", text)
        self.assertIn("置信度：中", text)
        self.assertIn("有效样本：6/8", text)
        self.assertIn("参考挂售", text)
        self.assertIn("官方链接：https://www.pathofexile.com/trade2/search/poe2/Runes%20of%20Aldur/abc123", text)

    def test_formats_warning_for_sparse_samples(self):
        estimate = PriceEstimate(
            item_name="水井之心",
            league="Runes of Aldur",
            median=20,
            low=20,
            high=24,
            currency="exalted",
            confidence="低",
            valid_count=2,
            total_count=2,
            source="trade2",
            warnings=["样本不足"],
        )

        text = format_price_estimate(estimate)

        self.assertIn("样本不足，仅供参考", text)


if __name__ == "__main__":
    unittest.main()
