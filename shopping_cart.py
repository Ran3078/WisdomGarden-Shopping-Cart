"""虛擬購物車結算程式。

依促銷折扣與優惠券，計算購物車最終應付金額。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

PRODUCT_CATEGORIES: dict[str, str] = {
    # 電子
    "ipad": "電子",
    "iphone": "電子",
    "顯示器": "電子",
    "筆記型電腦": "電子",
    "鍵盤": "電子",
    # 食品
    "麵包": "食品",
    "餅乾": "食品",
    "蛋糕": "食品",
    "牛肉": "食品",
    "魚": "食品",
    "蔬菜": "食品",
    # 日用品
    "餐巾紙": "日用品",
    "收納箱": "日用品",
    "咖啡杯": "日用品",
    "雨傘": "日用品",
    # 酒類
    "啤酒": "酒類",
    "白酒": "酒類",
    "伏特加": "酒類",
}


@dataclass(frozen=True)
class Promotion:
    date: str
    discount: Decimal
    category: str


@dataclass(frozen=True)
class CartItem:
    quantity: int
    name: str
    unit_price: Decimal

    @property
    def category(self) -> str:
        try:
            return PRODUCT_CATEGORIES[self.name]
        except KeyError as exc:
            raise ValueError(f"未知商品: {self.name}") from exc


@dataclass(frozen=True)
class Coupon:
    expiry_date: str
    threshold: Decimal
    discount_amount: Decimal


@dataclass(frozen=True)
class SettlementInput:
    promotions: list[Promotion]
    items: list[CartItem]
    settlement_date: str
    coupon: Coupon | None


def parse_date(raw: str) -> str:
    """正規化日期為 YYYY.M.D 可比對字串（以 tuple 比較）。"""
    parts = raw.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"無效日期: {raw}")
    year, month, day = (int(p) for p in parts)
    return f"{year}.{month}.{day}"


def date_tuple(raw: str) -> tuple[int, int, int]:
    year, month, day = (int(p) for p in parse_date(raw).split("."))
    return year, month, day


def parse_promotion(line: str) -> Promotion:
    date_raw, discount_raw, category = (part.strip() for part in line.split("|"))
    return Promotion(
        date=parse_date(date_raw),
        discount=Decimal(discount_raw),
        category=category,
    )


def parse_cart_item(line: str) -> CartItem:
    quantity_raw, rest = line.split("*", 1)
    name, price_raw = rest.split(":", 1)
    return CartItem(
        quantity=int(quantity_raw.strip()),
        name=name.strip(),
        unit_price=Decimal(price_raw.strip()),
    )


def parse_coupon(line: str) -> Coupon:
    parts = line.split()
    if len(parts) != 3:
        raise ValueError(f"無效優惠券: {line}")
    return Coupon(
        expiry_date=parse_date(parts[0]),
        threshold=Decimal(parts[1]),
        discount_amount=Decimal(parts[2]),
    )


def parse_input(text: str) -> SettlementInput:
    """解析輸入文字為結算資料。

    支援以空行分段的完整格式，也支援省略空促銷/優惠券區塊的精簡格式。
    """
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]

    promotions: list[Promotion] = []
    items: list[CartItem] = []
    settlement_date: str | None = None
    coupon: Coupon | None = None

    for line in lines:
        if not line:
            continue
        if "|" in line:
            promotions.append(parse_promotion(line))
        elif "*" in line and ":" in line:
            items.append(parse_cart_item(line))
        elif " " in line and line[0].isdigit():
            # 優惠券：日期 + 門檻 + 折抵
            coupon = parse_coupon(line)
        elif line[0].isdigit() and "." in line:
            settlement_date = parse_date(line)
        else:
            raise ValueError(f"無法解析的輸入行: {line}")

    if not items:
        raise ValueError("購物車不可為空")
    if settlement_date is None:
        raise ValueError("缺少結算日期")

    return SettlementInput(
        promotions=promotions,
        items=items,
        settlement_date=settlement_date,
        coupon=coupon,
    )


def find_category_discount(
    promotions: Iterable[Promotion],
    settlement_date: str,
    category: str,
) -> Decimal:
    for promo in promotions:
        if (
            date_tuple(promo.date) == date_tuple(settlement_date)
            and promo.category == category
        ):
            return promo.discount
    return Decimal("1")


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_total(data: SettlementInput) -> Decimal:
    """計算結算金額：先依品類折扣，再套用（最多一張）有效優惠券。"""
    subtotal = Decimal("0")

    for item in data.items:
        discount = find_category_discount(
            data.promotions, data.settlement_date, item.category
        )
        line_total = item.unit_price * item.quantity * discount
        subtotal += line_total

    total = subtotal

    if data.coupon is not None:
        coupon = data.coupon
        if (
            date_tuple(data.settlement_date) <= date_tuple(coupon.expiry_date)
            and total >= coupon.threshold
        ):
            total -= coupon.discount_amount

    return money(total)


def settle(text: str) -> str:
    """從輸入文字計算結算金額，回傳兩位小數字串。"""
    data = parse_input(text)
    return f"{calculate_total(data):.2f}"


def _is_settlement_date_line(line: str) -> bool:
    """判斷是否為純結算日期列（非優惠券）。"""
    stripped = line.strip()
    if not stripped or " " in stripped or "|" in stripped:
        return False
    if "*" in stripped or ":" in stripped:
        return False
    try:
        parse_date(stripped)
        return True
    except ValueError:
        return False


def _read_interactive() -> str:
    """互動讀取：看到結算日期後再讀一行（優惠券或空行）即結束。"""
    import sys

    print(
        "請貼上輸入。格式：促銷 → 空行 → 商品 → 空行 → 結算日期 → 優惠券(可空)。",
        file=sys.stderr,
    )
    print(
        "輸入結算日期後，再輸入優惠券（或直接 Enter），即可計算。",
        file=sys.stderr,
    )

    lines: list[str] = []
    saw_product = False

    while True:
        try:
            line = input()
        except EOFError:
            break

        lines.append(line)
        stripped = line.strip()

        if "*" in stripped and ":" in stripped:
            saw_product = True
            continue

        if saw_product and _is_settlement_date_line(stripped):
            try:
                coupon_or_blank = input()
                lines.append(coupon_or_blank)
            except EOFError:
                pass
            break

    return "\n".join(lines)


def main() -> None:
    import sys

    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as handle:
            text = handle.read()
    elif sys.stdin.isatty():
        text = _read_interactive()
    else:
        text = sys.stdin.read()

    print()
    print(settle(text))


if __name__ == "__main__":
    main()
