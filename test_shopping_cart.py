"""購物車結算自動化測試。

直接執行本檔即可看到每項測試的通過／失敗：
  .\\.venv\\Scripts\\python.exe test_shopping_cart.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from textwrap import dedent

import pytest

from shopping_cart import (
    CartItem,
    Coupon,
    Promotion,
    SettlementInput,
    calculate_total,
    parse_input,
    settle,
)


CASE_A = dedent(
    """\
    2015.11.11|0.7|電子

    1*ipad:2399.00
    1*顯示器:1799.00
    12*啤酒:25.00
    5*麵包:9.00

    2015.11.11
    2016.3.2 1000 200
    """
)

CASE_B = dedent(
    """\
    3*蔬菜:5.98
    8*餐巾紙:3.20
    2015.01.01
    """
)


def test_case_a():
    """題目 Case A：電子 7 折 + 優惠券 => 3083.60"""
    assert settle(CASE_A) == "3083.60"


def test_case_b():
    """題目 Case B：無促銷無優惠券 => 43.54"""
    assert settle(CASE_B) == "43.54"


def test_case_b_with_empty_sections():
    """Case B 完整空行格式 => 43.54"""
    text = dedent(
        """\

        3*蔬菜:5.98
        8*餐巾紙:3.20

        2015.01.01

        """
    )
    assert settle(text) == "43.54"


def test_promotion_only_applies_on_matching_date():
    """促銷日期不符時不打折 => 2399.00"""
    text = dedent(
        """\
        2015.11.11|0.7|電子

        1*ipad:2399.00

        2015.11.12
        """
    )
    assert settle(text) == "2399.00"


def test_promotion_only_applies_to_matching_category():
    """促銷只套用對應品類 => 2406.00"""
    text = dedent(
        """\
        2015.11.11|0.7|食品

        1*ipad:2399.00
        1*麵包:10.00

        2015.11.11
        """
    )
    assert settle(text) == "2406.00"


def test_coupon_not_applied_when_below_threshold():
    """未滿優惠券門檻不折抵 => 9.00"""
    text = dedent(
        """\
        1*麵包:9.00

        2015.01.01
        2016.3.2 1000 200
        """
    )
    assert settle(text) == "9.00"


def test_coupon_not_applied_when_expired():
    """優惠券過期不可用 => 2399.00"""
    text = dedent(
        """\
        1*ipad:2399.00

        2016.3.3
        2016.3.2 1000 200
        """
    )
    assert settle(text) == "2399.00"


def test_coupon_applied_on_expiry_date():
    """到期當日仍可使用優惠券 => 2199.00"""
    text = dedent(
        """\
        1*ipad:2399.00

        2016.3.2
        2016.3.2 1000 200
        """
    )
    assert settle(text) == "2199.00"


def test_multiple_promotions_different_categories():
    """多品類促銷同時生效 => 81.00"""
    text = dedent(
        """\
        2015.09.27|0.8|食品
        2015.09.27|0.9|日用品

        2*麵包:10.00
        1*雨傘:50.00
        1*啤酒:20.00

        2015.09.27
        """
    )
    assert settle(text) == "81.00"


def test_discount_then_coupon_order():
    """先算品類折扣再判斷優惠券門檻 => 750.00"""
    data = SettlementInput(
        promotions=[Promotion("2015.11.11", Decimal("0.5"), "電子")],
        items=[CartItem(1, "ipad", Decimal("1500.00"))],
        settlement_date="2015.11.11",
        coupon=Coupon("2016.1.1", Decimal("1000"), Decimal("200")),
    )
    assert calculate_total(data) == Decimal("750.00")


def test_rounding_half_up():
    """金額四捨五入到小數點 2 位 => 0.81"""
    text = dedent(
        """\
        2015.01.01|0.7|食品

        1*蔬菜:1.15

        2015.01.01
        """
    )
    assert settle(text) == "0.81"


def test_unknown_product_on_calculate():
    """未知商品應拋出錯誤"""
    data = parse_input("1*未知商品:10.00\n2015.01.01\n")
    with pytest.raises(ValueError, match="未知商品"):
        calculate_total(data)


def test_all_product_categories_recognized():
    """產品目錄品類對應正確"""
    catalog = [
        ("ipad", "電子"),
        ("iphone", "電子"),
        ("顯示器", "電子"),
        ("筆記型電腦", "電子"),
        ("鍵盤", "電子"),
        ("麵包", "食品"),
        ("餅乾", "食品"),
        ("蛋糕", "食品"),
        ("牛肉", "食品"),
        ("魚", "食品"),
        ("蔬菜", "食品"),
        ("餐巾紙", "日用品"),
        ("收納箱", "日用品"),
        ("咖啡杯", "日用品"),
        ("雨傘", "日用品"),
        ("啤酒", "酒類"),
        ("白酒", "酒類"),
        ("伏特加", "酒類"),
    ]
    for name, category in catalog:
        assert CartItem(1, name, Decimal("1")).category == category


def _iter_tests():
    """收集本模組中所有 test_* 函式與其中文說明。"""
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            title = (func.__doc__ or name).strip().splitlines()[0]
            yield title, func


def _run_with_chinese_report() -> int:
    print("購物車結算測試")
    print("=" * 50)

    passed = 0
    failed = 0

    for title, func in _iter_tests():
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - 彙總顯示給使用者
            failed += 1
            print(f"[失敗] {title}")
            print(f"       原因: {exc}")
        else:
            passed += 1
            print(f"[通過] {title}")

    total = passed + failed
    print("=" * 50)
    print(f"合計 {total} 項：通過 {passed}，失敗 {failed}")
    if failed == 0:
        print("結果：全部測試通過")
        return 0

    print("結果：有測試失敗")
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(_run_with_chinese_report())
