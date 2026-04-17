import time
from decimal import Decimal
from datetime import datetime
import xml.etree.ElementTree as ET

import requests
from django.conf import settings


class IBKRClient:
    def fetch_all_executions(self) -> list[dict]:
        xml_text = self.fetch_flex_statement_xml()
        return self.parse_flex_xml(xml_text)

    def fetch_flex_statement_xml(self) -> str:
        token = settings.IBKR_FLEX_TOKEN
        query_id = settings.IBKR_FLEX_QUERY_ID

        if not token or not query_id:
            raise ValueError(
                "IBKR_FLEX_TOKEN or IBKR_FLEX_QUERY_ID is missing. "
                "Please set them in backend/.env or your run configuration."
            )

        send_resp = requests.get(
            settings.IBKR_FLEX_SEND_REQUEST_URL,
            params={"t": token, "q": query_id, "v": "3"},
            timeout=60,
        )
        send_resp.raise_for_status()

        reference_code = self.parse_reference_code(send_resp.text)
        if not reference_code:
            raise ValueError(f"Could not get Flex reference code: {send_resp.text}")

        for _ in range(15):
            get_resp = requests.get(
                settings.IBKR_FLEX_GET_STATEMENT_URL,
                params={"t": token, "q": reference_code, "v": "3"},
                timeout=60,
            )
            get_resp.raise_for_status()

            xml_text = get_resp.text
            if "<FlexStatement" in xml_text and "<Trades>" in xml_text:
                return xml_text

            time.sleep(2)

        raise TimeoutError("Timed out waiting for Flex statement.")

    def parse_reference_code(self, xml_text: str) -> str | None:
        root = ET.fromstring(xml_text)
        elem = root.find(".//ReferenceCode")
        return elem.text if elem is not None else None

    def parse_flex_xml(self, xml_text: str) -> list[dict]:
        root = ET.fromstring(xml_text)
        rows: list[dict] = []

        for trade in root.findall(".//Trades/Trade"):
            data = trade.attrib
            row = self.map_trade_node(data)
            rows.append(row)

        return rows

    def map_trade_node(self, data: dict) -> dict:
        side_raw = (data.get("buySell") or "").upper().strip()
        if side_raw not in {"BUY", "SELL", "BOT", "SLD"}:
            raise ValueError(f"Unexpected buySell value: {side_raw}")

        side = "BUY" if side_raw in {"BUY", "BOT"} else "SELL"

        qty = self.to_decimal(data.get("quantity", "0"))
        qty_abs = abs(qty)

        return {
            "execution_id": data.get("ibExecID") or data.get("tradeID"),
            "perm_id": data.get("ibOrderID") or data.get("orderReference"),
            "order_id": data.get("ibOrderID"),
            "client_id": None,
            "account": data.get("accountId"),
            "symbol": data.get("symbol"),
            "local_symbol": data.get("description") or data.get("underlyingSymbol"),
            "conid": data.get("conid"),
            "sec_type": data.get("assetCategory"),
            "currency": data.get("currency"),
            "exchange": data.get("exchange") or data.get("listingExchange"),
            "side": side,
            "quantity": qty_abs,
            "price": self.to_decimal(data.get("tradePrice", "0")),
            "commission": abs(self.to_decimal(data.get("ibCommission", "0"))),
            "realized_pnl": self.to_decimal(data.get("fifoPnlRealized", "0")),
            "executed_at": self.parse_ibkr_datetime(data.get("dateTime")),
            "extra_open_close": data.get("openCloseIndicator"),
            "extra_multiplier": self.to_decimal(data.get("multiplier", "1")),
            "extra_trade_id": data.get("tradeID"),
            "extra_order_type": data.get("orderType"),
            "extra_proceeds": self.to_decimal(data.get("proceeds", "0")),
            "extra_net_cash": self.to_decimal(data.get("netCash", "0")),
            "raw_payload": data,
        }

    def parse_ibkr_datetime(self, value: str) -> datetime:
        if not value:
            raise ValueError("Missing dateTime in Flex XML.")
        return datetime.strptime(value, "%Y%m%d;%H%M%S")

    def to_decimal(self, value) -> Decimal:
        if value in [None, ""]:
            return Decimal("0")
        return Decimal(str(value).replace(",", ""))
