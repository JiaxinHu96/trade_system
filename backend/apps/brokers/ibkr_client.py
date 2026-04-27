import time
from decimal import Decimal
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.utils import timezone


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
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ValueError(f"Invalid XML from IBKR Flex send request: {exc}") from exc
        elem = root.find(".//ReferenceCode")
        return elem.text if elem is not None else None

    def parse_flex_xml(self, xml_text: str) -> list[dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ValueError(f"Invalid XML from IBKR Flex statement: {exc}") from exc
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
        parsed = datetime.strptime(value, "%Y%m%d;%H%M%S")
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

    def to_decimal(self, value) -> Decimal:
        if value in [None, ""]:
            return Decimal("0")
        return Decimal(str(value).replace(",", ""))

    def search_contracts(self, query: str, sec_type: str | None = None, limit: int = 100) -> list[dict]:
        base_url = (settings.IBKR_CLIENT_PORTAL_BASE_URL or "").strip()
        if not base_url:
            raise ValueError("IBKR_CLIENT_PORTAL_BASE_URL is not configured.")
        symbol = (query or "").strip()
        if not symbol:
            return []

        url = urljoin(base_url.rstrip('/') + '/', 'iserver/secdef/search')
        headers = {}
        auth_token = (settings.IBKR_CLIENT_PORTAL_AUTH_TOKEN or "").strip()
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        params = {"symbol": symbol}
        if sec_type:
            params["secType"] = sec_type

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=20,
            verify=settings.IBKR_CLIENT_PORTAL_VERIFY_SSL,
        )
        response.raise_for_status()
        payload = response.json() if response.content else []
        if not isinstance(payload, list):
            return []

        rows = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            rows.append({
                "symbol": (item.get("symbol") or "").strip(),
                "asset_class": (item.get("secType") or "").strip().upper(),
                "display_name": (item.get("description") or item.get("name") or "").strip(),
                "exchange": (item.get("listingExchange") or item.get("exchange") or "").strip(),
                "conid": item.get("conid"),
            })
            if len(rows) >= max(1, int(limit)):
                break
        return [row for row in rows if row["symbol"]]
