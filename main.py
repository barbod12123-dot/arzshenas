"""
============================================================================
 Arzshenas | ارزش‌شناس
 اپلیکیشن کراس‌پلتفرم (Android / iOS) رصد لحظه‌ای بازار طلا، ارز و ارز دیجیتال
 ساخته‌شده با Python + Flet
============================================================================

اجرا در حالت توسعه (دسکتاپ):
    flet run main.py

اجرا روی شبیه‌ساز/دستگاه اندروید:
    flet run main.py --android

اجرا روی شبیه‌ساز/دستگاه iOS (فقط macOS):
    flet run main.py --ios

ساخت نسخه‌ی نهایی برای انتشار:
    flet build apk        # اندروید
    flet build ipa        # iOS (فقط macOS + حساب توسعه‌دهنده اپل)

پیش‌نیاز: پوشه‌ی assets/fonts باید کنار همین فایل باشد (فونت فارسی Vazirmatn).

نکته‌ی مهم درباره‌ی داده‌ی طلا/ارز ایران:
    برای نمایش قیمت واقعی طلا، سکه و دلار آزاد به تومان، برنامه از سه منبع استفاده می‌کند:
    1. اولویت اول: دانلود از GitHub (Navasan-API)
    2. در صورت عدم موفقیت: BRSAPI
    3. در نهایت: داده‌ی نمونه
============================================================================
"""

import asyncio
import json
import time
import os
import requests

import flet as ft
import httpx


APP_NAME = "Arzshenas"
APP_NAME_FA = "ارزش‌شناس"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# پالت رنگی: طلایی + مشکی، مینیمال
# ---------------------------------------------------------------------------
GOLD = "#D4AF37"
GOLD_BRIGHT = "#FFD700"
GOLD_SOFT = "#E8C766"
BLACK = "#1A1A1A"
BLACK_SOFT = "#242424"
BLACK_CARD_DARK = "#2A2A28"
WHITE = "#FFFFFF"
CREAM = "#FAF7F0"
GREY_LIGHT = "#F2EFE8"
GREEN_UP = "#2FB870"
RED_DOWN = "#E5484D"
TEXT_MUTED_DARK = "#B8B2A2"
TEXT_MUTED_LIGHT = "#8A8577"

FONT_FAMILY = "Vazirmatn"

# ---------------------------------------------------------------------------
# ارزهای پایه‌ی جهانی که در تب «ارزها» نمایش داده می‌شوند
# کد ISO : (نام فارسی, نام انگلیسی, ایموجی/کد پرچم)
# ---------------------------------------------------------------------------
WORLD_CURRENCIES = [
    ("USD", "دلار آمریکا", "US Dollar", "🇺🇸"),
    ("EUR", "یورو", "Euro", "🇪🇺"),
    ("GBP", "پوند انگلیس", "British Pound", "🇬🇧"),
    ("AED", "درهم امارات", "UAE Dirham", "🇦🇪"),
    ("TRY", "لیر ترکیه", "Turkish Lira", "🇹🇷"),
    ("CNY", "یوان چین", "Chinese Yuan", "🇨🇳"),
    ("JPY", "ین ژاپن", "Japanese Yen", "🇯🇵"),
    ("CAD", "دلار کانادا", "Canadian Dollar", "🇨🇦"),
    ("AUD", "دلار استرالیا", "Australian Dollar", "🇦🇺"),
    ("CHF", "فرانک سوئیس", "Swiss Franc", "🇨🇭"),
    ("SEK", "کرون سوئد", "Swedish Krona", "🇸🇪"),
    ("RUB", "روبل روسیه", "Russian Ruble", "🇷🇺"),
    ("INR", "روپیه هند", "Indian Rupee", "🇮🇳"),
    ("KWD", "دینار کویت", "Kuwaiti Dinar", "🇰🇼"),
    ("SAR", "ریال عربستان", "Saudi Riyal", "🇸🇦"),
    ("IQD", "دینار عراق", "Iraqi Dinar", "🇮🇶"),
    ("QAR", "ریال قطر", "Qatari Riyal", "🇶🇦"),
    ("OMR", "ریال عمان", "Omani Rial", "🇴🇲"),
]

# ---------------------------------------------------------------------------
# اقلام طلا و سکه که در تب «طلا» نمایش داده می‌شوند
# کلید : (نام فارسی, نام انگلیسی)
# ---------------------------------------------------------------------------
GOLD_ITEMS = [
    ("gold_18", "طلای ۱۸ عیار (هر گرم)", "18K Gold (per gram)"),
    ("gold_24", "طلای ۲۴ عیار (هر گرم)", "24K Gold (per gram)"),
    ("gold_ounce", "انس جهانی طلا", "Gold Ounce (Global)"),
    ("coin_emami", "سکه امامی", "Emami Coin"),
    ("coin_half", "نیم سکه", "Half Coin"),
    ("coin_quarter", "ربع سکه", "Quarter Coin"),
]

# ---------------------------------------------------------------------------
# متن‌های دوزبانه‌ی رابط کاربری
# ---------------------------------------------------------------------------
TR = {
    "fa": {
        "app_title": "ارزش‌شناس",
        "tab_crypto": "کریپتو",
        "tab_gold": "طلا",
        "tab_currency": "ارزها",
        "tab_settings": "تنظیمات",
        "tab_home": "خانه",
        "search_hint": "جست‌وجو...",
        "loading": "در حال دریافت اطلاعات...",
        "offline_notice": "اتصال اینترنت برقرار نیست — آخرین اطلاعات ذخیره‌شده نمایش داده می‌شود",
        "last_update": "آخرین به‌روزرسانی",
        "refresh": "به‌روزرسانی",
        "market_cap": "ارزش بازار",
        "change_24h": "تغییر ۲۴ ساعته",
        "settings_title": "تنظیمات",
        "language": "زبان برنامه",
        "theme": "پوسته برنامه",
        "theme_light": "روشن",
        "theme_dark": "تاریک",
        "base_currency": "واحد پول پایه",
        "toman": "تومان",
        "dollar": "دلار",
        "about": "درباره برنامه",
        "about_text": "ارزش‌شناس، دستیار همراه شما برای رصد لحظه‌ای بازار طلا، ارز و ارزهای دیجیتال. ساخته شده توسط SIRBARBOD",
        "version": "نسخه",
        "no_results": "نتیجه‌ای یافت نشد",
        "home_summary": "خلاصه بازار",
        "home_gold": "طلای ۱۸ عیار",
        "home_dollar": "دلار آزاد",
        "home_bitcoin": "بیت‌کوین",
        "view_all": "مشاهده همه",
        "close": "بستن",
        "notif_title": "اعلان تغییر قیمت",
        "world_currencies": "ارزهای جهانی",
        "gold_and_coin": "طلا و سکه",
        "cryptocurrencies": "ارزهای دیجیتال برتر",
        "rank": "رتبه",
        "unit_toman": "تومان",
        "unit_usd": "دلار",
        "per_gram": "هر گرم",
        "pull_refresh_hint": "برای به‌روزرسانی، پایین بکشید",
    },
    "en": {
        "app_title": "Arzshenas",
        "tab_crypto": "Crypto",
        "tab_gold": "Gold",
        "tab_currency": "Currencies",
        "tab_settings": "Settings",
        "tab_home": "Home",
        "search_hint": "Search...",
        "loading": "Fetching latest data...",
        "offline_notice": "No internet connection — showing last saved data",
        "last_update": "Last update",
        "refresh": "Refresh",
        "market_cap": "Market Cap",
        "change_24h": "24h Change",
        "settings_title": "Settings",
        "language": "App Language",
        "theme": "App Theme",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "base_currency": "Base Currency",
        "toman": "Toman",
        "dollar": "Dollar",
        "about": "About",
        "about_text": "Arzshenas, your companion for real-time monitoring of gold, currency, and cryptocurrency markets. Developed by SIRBARBOD.",
        "version": "Version",
        "no_results": "No results found",
        "home_summary": "Market Summary",
        "home_gold": "18K Gold",
        "home_dollar": "USD (Free Market)",
        "home_bitcoin": "Bitcoin",
        "view_all": "View All",
        "close": "Close",
        "notif_title": "Price Change Alert",
        "world_currencies": "World Currencies",
        "gold_and_coin": "Gold & Coins",
        "cryptocurrencies": "Top Cryptocurrencies",
        "rank": "Rank",
        "unit_toman": "Toman",
        "unit_usd": "USD",
        "per_gram": "per gram",
        "pull_refresh_hint": "Pull down to refresh",
    },
}


def t(lang: str, key: str) -> str:
    """برگرداندن متن ترجمه‌شده بر اساس زبان و کلید"""
    return TR.get(lang, TR["fa"]).get(key, key)



# ---------------------------------------------------------------------------
# پیکربندی سرویس‌ها
# ---------------------------------------------------------------------------
COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=50&page=1"
    "&sparkline=false&price_change_percentage=24h"
)
EXCHANGE_RATE_URL = "https://api.exchangerate-api.com/v4/latest/USD"

# کلید رایگان BRSAPI را از https://brsapi.ir ثبت‌نام کرده و اینجا قرار دهید.
# تا زمانی که کلید تنظیم نشود، برنامه به‌صورت خودکار از داده‌ی نمونه
# (که در پایین این فایل آمده) برای طلا/سکه/دلار تومانی استفاده می‌کند
# و اپلیکیشن کاملاً کار می‌کند — فقط اعداد واقعی لحظه‌ای نخواهند بود.
BRSAPI_KEY = "BXS3v9Q4Yja7KNGY8CfQYadTcTYdahcz"  # TODO: کلید رایگان خودتان را اینجا قرار دهید
BRSAPI_GOLD_URL = f"https://Api.BrsApi.ir/Market/Gold_Currency.php?key={BRSAPI_KEY}"

REQUEST_TIMEOUT = 12.0

# ---------------------------------------------------------------------------
# داده‌ی نمونه برای اولین اجرا / نبود کلید / قطعی کامل شبکه
# (تا رابط کاربری همیشه چیزی برای نمایش داشته باشد)
# ---------------------------------------------------------------------------
FALLBACK_GOLD = {
    "gold_18": 38500000,
    "gold_24": 51300000,
    "gold_ounce": 2650,  # دلار
    "coin_emami": 385000000,
    "coin_half": 195000000,
    "coin_quarter": 110000000,
    "usd_irr_free": 1085000,  # نرخ آزاد دلار به ریال (تومان = تقسیم بر ۱۰)
}


# ============================================================================
# بخش Navasan-GitHub - جدید (بدون Selenium)
# ============================================================================

# لینک‌های GitHub برای دانلود داده
GITHUB_FIAT_URL = "https://raw.githubusercontent.com/HosseinOdd/Navasan-API/refs/heads/main/data/fiat.json"
GITHUB_GOLD_URL = "https://raw.githubusercontent.com/HosseinOdd/Navasan-API/refs/heads/main/data/gold.json"

# مسیرهای ذخیره داده در برنامه
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
FIAT_PATH = os.path.join(DATA_DIR, 'fiat.json')
GOLD_PATH = os.path.join(DATA_DIR, 'gold.json')

def download_from_github(url, save_path):
    """دانلود فایل از GitHub و ذخیره در مسیر مشخص"""
    try:
        print(f"📥 دانلود از: {url}")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"✅ ذخیره شد: {save_path}")
            return True
        else:
            print(f"❌ خطا در دانلود: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False

def fetch_from_github():
    """دریافت قیمت‌ها از GitHub و ذخیره در فایل"""
    print("🔄 دریافت قیمت‌ها از GitHub (Navasan-API)...")
    
    success_fiat = download_from_github(GITHUB_FIAT_URL, FIAT_PATH)
    success_gold = download_from_github(GITHUB_GOLD_URL, GOLD_PATH)
    
    return success_fiat or success_gold

def load_navasan_data():
    """بارگذاری داده‌های ذخیره شده از GitHub (ساختار Navasan-API)"""
    result = {}
    
    # بارگذاری ارزها (fiat.json)
    try:
        if os.path.exists(FIAT_PATH):
            with open(FIAT_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, value in data.items():
                    if key == "usd":
                        # همون عددی که تو فایل هست، بدون تغییر
                        result['usd_irr_free'] = float(value.get('value', 0))
                        print(f"✅ دلار: {result['usd_irr_free']:,} تومان")
    except Exception as e:
        print(f"⚠️ خطا در خواندن ارزها: {e}")
    
    # بارگذاری طلا (gold.json)
    try:
        if os.path.exists(GOLD_PATH):
            with open(GOLD_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                mapping = {
                    "18ayar": "gold_18",
                    "sekkeh": "coin_emami",
                    "nim": "coin_half",
                    "rob": "coin_quarter",
                }
                for navasan_key, program_key in mapping.items():
                    if navasan_key in data:
                        value = data[navasan_key].get('value')
                        if value is not None:
                            result[program_key] = float(value)
                            print(f"✅ {program_key}: {result[program_key]:,} تومان")
                        
                if 'gold_18' in result and 'gold_24' not in result:
                    result['gold_24'] = result['gold_18'] * 1.333
                
                if "xau" in data:
                    value = data["xau"].get('value')
                    if value is not None:
                        result['gold_ounce'] = float(value)
                        print(f"✅ gold_ounce: {result['gold_ounce']} دلار")
                    
    except Exception as e:
        print(f"⚠️ خطا در خواندن طلا: {e}")
    
    return result

class DataService:
    """
    مسئول ارتباط با APIهای بیرونی + مدیریت کش داخل SharedPreferences صفحه
    """

    def __init__(self, page, prefs: "ft.SharedPreferences"):
        self.page = page
        self.prefs = prefs
        self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        self.last_download_time = 0  # ← این رو اضافه کن

    async def close(self):
        await self._client.aclose()

    # ------------------------------------------------------------------
    # کش‌سازی عمومی
    # ------------------------------------------------------------------
    async def _save_cache(self, key: str, data) -> None:
        try:
            payload = json.dumps({"ts": time.time(), "data": data}, ensure_ascii=False)
            await self.prefs.set(f"arzshenas.cache.{key}", payload)
        except Exception:
            pass

    async def _load_cache(self, key: str):
        try:
            raw = await self.prefs.get(f"arzshenas.cache.{key}")
            if raw:
                obj = json.loads(raw)
                return obj.get("data"), obj.get("ts")
        except Exception:
            pass
        return None, None

    # ------------------------------------------------------------------
    # کریپتو — CoinGecko
    # ------------------------------------------------------------------
    async def get_crypto(self):
        try:
            resp = await self._client.get(COINGECKO_URL)
            resp.raise_for_status()
            raw = resp.json()
            coins = [
                {
                    "rank": c.get("market_cap_rank"),
                    "id": c.get("id"),
                    "symbol": (c.get("symbol") or "").upper(),
                    "name": c.get("name"),
                    "image": c.get("image"),
                    "price_usd": c.get("current_price"),
                    "change_24h": c.get("price_change_percentage_24h"),
                    "market_cap": c.get("market_cap"),
                }
                for c in raw
            ]
            await self._save_cache("crypto", coins)
            return coins, True
        except Exception:
            cached, _ = await self._load_cache("crypto")
            return (cached or []), False

    # ------------------------------------------------------------------
    # ارزهای جهانی — exchangerate-api
    # ------------------------------------------------------------------
    async def get_world_rates(self):
        try:
            resp = await self._client.get(EXCHANGE_RATE_URL)
            resp.raise_for_status()
            raw = resp.json()
            rates = raw.get("rates", {})
            await self._save_cache("world_rates", rates)
            return rates, True
        except Exception:
            cached, _ = await self._load_cache("world_rates")
            return (cached or {}), False

    # ------------------------------------------------------------------
    # طلا، سکه و دلار آزاد ایران — اولویت: GitHub > BRSAPI > داده نمونه
    # ------------------------------------------------------------------
    async def get_iran_gold_currency(self):
        out = dict(FALLBACK_GOLD)
        
        # ============================================================
        # اولویت 1: دریافت از GitHub (Navasan-API)
        # ============================================================
        try:
            current_time = time.time()
            
            # هر ۵ دقیقه یک بار دانلود کن (یا اگر فایل وجود نداشت)
            if current_time - self.last_download_time > 300 or not os.path.exists(FIAT_PATH) or not os.path.exists(GOLD_PATH):
                print("📡 دریافت داده از GitHub...")
                fetch_from_github()
                self.last_download_time = current_time
            
            # بارگذاری داده‌ها
            navasan_data = load_navasan_data()
            
            # به‌روزرسانی با داده‌های navasan
            if navasan_data:
                for key in out:
                    if key in navasan_data and navasan_data[key]:
                        out[key] = navasan_data[key]
                print("✅ داده‌ها از GitHub بارگذاری شد")
                return out, True
                
        except Exception as e:
            print(f"⚠️ خطا در دریافت از GitHub: {e}")
        
        # ============================================================
        # اولویت 2: BRSAPI (اگر GitHub موفق نبود)
        # ============================================================
        if not BRSAPI_KEY:
            cached, _ = await self._load_cache("iran_gold")
            return (cached or FALLBACK_GOLD), False

        try:
            resp = await self._client.get(BRSAPI_GOLD_URL)
            resp.raise_for_status()
            raw = resp.json()
            parsed = self._parse_brsapi(raw)
            if parsed:
                await self._save_cache("iran_gold", parsed)
                return parsed, True
            raise ValueError("empty parse result")
        except Exception:
            cached, _ = await self._load_cache("iran_gold")
            return (cached or FALLBACK_GOLD), False

    @staticmethod
    def _parse_brsapi(raw) -> dict:
        """
        تبدیل پاسخ BRSAPI به ساختار داخلی برنامه.
        """
        out = dict(FALLBACK_GOLD)
        try:
            items = []
            if isinstance(raw, dict):
                items = raw.get("gold", []) + raw.get("currency", [])
            elif isinstance(raw, list):
                items = raw

            key_map = {
                "geram18": "gold_18",
                "gold_gram18": "gold_18",
                "geram24": "gold_24",
                "gold_gram24": "gold_24",
                "ons": "gold_ounce",
                "gold_ounce": "gold_ounce",
                "sekee": "coin_emami",
                "emami": "coin_emami",
                "nim": "coin_half",
                "rob": "coin_quarter",
                "usd": "usd_irr_free",
                "dollar": "usd_irr_free",
            }
            for item in items:
                if not isinstance(item, dict):
                    continue
                symbol = str(item.get("symbol") or item.get("name") or "").lower()
                price = item.get("price") or item.get("value")
                for src_key, dst_key in key_map.items():
                    if src_key in symbol and price:
                        out[dst_key] = float(str(price).replace(",", ""))
            return out
        except Exception:
            return FALLBACK_GOLD

AUTO_REFRESH_SECONDS = 300  # ← تغییر به ۵ دقیقه (300 ثانیه)
PRICE_ALERT_THRESHOLD_PCT = 1.5  # درصد تغییر لازم برای نمایش اعلان درون‌برنامه‌ای


def fmt_int(n) -> str:
    """جداکننده‌ی هزارگان برای اعداد صحیح"""
    try:
        return f"{int(round(float(n))):,}"
    except Exception:
        return "—"


def fmt_price(n, decimals=2) -> str:
    try:
        v = float(n)
        if v >= 1000:
            return f"{v:,.0f}"
        return f"{v:,.{decimals}f}"
    except Exception:
        return "—"


class ArzshenasApp:
    def __init__(self, page: ft.Page):
        self.page = page
        # سرویس ذخیره‌سازی محلی (جایگزین غیرمنسوخ page.shared_preferences)
        self.prefs = ft.SharedPreferences()
        self.data = DataService(page, self.prefs)

        # ---- وضعیت برنامه (State) ----
        self.lang = "fa"
        self.theme_mode = "dark"
        self.base_currency = "toman"  # یا "usd"
        self.online = True
        self.last_update_ts = None

        self.crypto_items = []
        self.world_rates = {}
        self.iran_gold = {}

        self.crypto_search = ""
        self.currency_search = ""

        self.nav_index = 0
        self._refresh_task = None

        # کنترل‌های ارجاعی که در چند جا به‌روزرسانی می‌شوند
        self.body_container = ft.Container(expand=True)
        self.offline_banner = ft.Container(visible=False)
        self.nav_bar = None

    # =====================================================================
    # مقداردهی اولیه
    # =====================================================================
    async def init(self):
        await self._load_prefs()
        self._setup_page_theme()
        self._build_shell()
        
        # وقتی برنامه باز میشه، یه بار به‌روزرسانی کن
        await self.refresh_all(initial=True)
        
        # هر ۵ دقیقه یک بار به‌روزرسانی خودکار
        self._refresh_task = self.page.run_task(self._auto_refresh_loop)

    async def _load_prefs(self):
        try:
            lang = await self.prefs.get("arzshenas.lang")
            theme = await self.prefs.get("arzshenas.theme")
            currency = await self.prefs.get("arzshenas.currency")
            if lang:
                self.lang = lang
            if theme:
                self.theme_mode = theme
            if currency:
                self.base_currency = currency
        except Exception:
            pass

    async def _save_prefs(self):
        try:
            await self.prefs.set("arzshenas.lang", self.lang)
            await self.prefs.set("arzshenas.theme", self.theme_mode)
            await self.prefs.set("arzshenas.currency", self.base_currency)
        except Exception:
            pass

    def _setup_page_theme(self):
        page = self.page
        page.title = "Arzshenas | ارزش‌شناس"
        page.fonts = {
            "Vazirmatn": "fonts/Vazirmatn-Regular.ttf",
            "Vazirmatn-Medium": "fonts/Vazirmatn-Medium.ttf",
            "Vazirmatn-Bold": "fonts/Vazirmatn-Bold.ttf",
        }
        page.rtl = self.lang == "fa"
        page.theme_mode = ft.ThemeMode.DARK if self.theme_mode == "dark" else ft.ThemeMode.LIGHT
        page.theme = ft.Theme(
            font_family=FONT_FAMILY,
            color_scheme_seed=GOLD,
            use_material3=True,
        )
        page.dark_theme = ft.Theme(
            font_family=FONT_FAMILY,
            color_scheme_seed=GOLD,
            use_material3=True,
        )
        page.bgcolor = BLACK if self.theme_mode == "dark" else CREAM
        page.padding = 0
        page.window.width = 420
        page.window.height = 860

    # -- رنگ‌های وابسته به تم فعلی --
    @property
    def bg_color(self):
        return BLACK if self.theme_mode == "dark" else CREAM

    @property
    def card_color(self):
        return BLACK_CARD_DARK if self.theme_mode == "dark" else WHITE

    @property
    def text_color(self):
        return WHITE if self.theme_mode == "dark" else BLACK

    @property
    def muted_color(self):
        return TEXT_MUTED_DARK if self.theme_mode == "dark" else TEXT_MUTED_LIGHT

    def tr(self, key: str) -> str:
        return t(self.lang, key)

    # =====================================================================
    # اسکلت اصلی برنامه: هدر ثابت + بدنه + نوار پایین
    # =====================================================================
    def _build_shell(self):
        page = self.page
        page.controls.clear()

        self.offline_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CLOUD_OFF_ROUNDED, size=16, color=BLACK),
                    ft.Text(self.tr("offline_notice"), size=12, color=BLACK,
                             font_family=FONT_FAMILY, expand=True),
                ],
                spacing=6,
            ),
            bgcolor=GOLD_SOFT,
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            visible=False,
        )

        self.nav_bar = ft.NavigationBar(
            selected_index=self.nav_index,
            on_change=self._on_nav_change,
            bgcolor=self.card_color,
            indicator_color=GOLD,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icon(ft.CupertinoIcons.HOUSE),
                    selected_icon=ft.Icon(ft.CupertinoIcons.HOUSE_FILL, color=BLACK),
                    label=self.tr("tab_home"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icon(ft.CupertinoIcons.BITCOIN),
                    selected_icon=ft.Icon(ft.CupertinoIcons.BITCOIN, color=BLACK),
                    label=self.tr("tab_crypto"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icon(ft.CupertinoIcons.CIRCLE_GRID_HEX),
                    selected_icon=ft.Icon(ft.CupertinoIcons.CIRCLE_GRID_HEX_FILL, color=BLACK),
                    label=self.tr("tab_gold"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icon(ft.CupertinoIcons.MONEY_DOLLAR),
                    selected_icon=ft.Icon(ft.CupertinoIcons.MONEY_DOLLAR, color=BLACK),
                    label=self.tr("tab_currency"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icon(ft.CupertinoIcons.SETTINGS),
                    selected_icon=ft.Icon(ft.CupertinoIcons.SETTINGS_SOLID, color=BLACK),
                    label=self.tr("tab_settings"),
                ),
            ],
        )

        self.body_container = ft.Container(
            expand=True,
            content=ft.Container(),  # با انیمیشن fade در render_body پر می‌شود
            animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
            opacity=0,
        )

        page.add(
            ft.Column(
                [
                    self.offline_banner,
                    self.body_container,
                    self.nav_bar,
                ],
                spacing=0,
                expand=True,
            )
        )
        self._render_body()
        page.update()

    def _on_nav_change(self, e):
        self.nav_index = e.control.selected_index
        self._render_body()
        self.page.update()

    def _go_to_tab(self, index: int):
        self.nav_index = index
        self.nav_bar.selected_index = index
        self._render_body()
        self.page.update()

    # =====================================================================
    # رندر بدنه بر اساس تب انتخاب‌شده + انیمیشن fade-in ملایم
    # =====================================================================
    def _render_body(self):
        builders = [
            self._build_home_tab,
            self._build_crypto_tab,
            self._build_gold_tab,
            self._build_currency_tab,
            self._build_settings_tab,
        ]
        self.body_container.content = builders[self.nav_index]()
        self.body_container.opacity = 0
        self.page.update()
        self.body_container.opacity = 1
        self.page.update()

    # =====================================================================
    # عنصرهای مشترک UI
    # =====================================================================
    def _header(self, title: str, show_search=False, on_search=None, on_refresh=None):
        controls = [
            ft.Text(title, size=22, weight=ft.FontWeight.BOLD,
                     font_family="Vazirmatn-Bold", color=GOLD),
        ]
        row_children = [
            ft.Column(controls, spacing=0, expand=True),
        ]
        if on_refresh:
            row_children.append(
                ft.IconButton(
                    icon=ft.CupertinoIcons.REFRESH,
                    icon_color=GOLD,
                    tooltip=self.tr("refresh"),
                    on_click=on_refresh,
                )
            )
        header = ft.Column(
            [
                ft.Row(row_children, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=10,
        )
        if show_search:
            header.controls.append(
                ft.TextField(
                    hint_text=self.tr("search_hint"),
                    prefix_icon=ft.CupertinoIcons.SEARCH,
                    border_radius=14,
                    filled=True,
                    bgcolor=self.card_color,
                    border_color="transparent",
                    height=46,
                    content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    on_change=on_search,
                )
            )
        return ft.Container(
            content=header,
            padding=ft.Padding.only(left=20, right=20, top=18, bottom=10),
        )

    def _last_update_text(self):
        if not self.last_update_ts:
            return ""
        dt = time.strftime("%H:%M:%S", time.localtime(self.last_update_ts))
        return f"{self.tr('last_update')}: {dt}"

    def _empty_state(self, text):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.CupertinoIcons.SEARCH, size=40, color=self.muted_color),
                    ft.Text(text, color=self.muted_color, font_family=FONT_FAMILY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
            padding=40,
        )

    # =====================================================================
    # تب خانه
    # =====================================================================
    def _build_home_tab(self):
        gold_18 = self.iran_gold.get("gold_18")
        usd_irr = self.iran_gold.get("usd_irr_free")
        btc = next((c for c in self.crypto_items if c.get("symbol") == "BTC"), None)

        def summary_card(icon, title, value, sub, color):
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(icon, color=BLACK, size=22),
                            bgcolor=color,
                            width=44, height=44,
                            border_radius=22,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(title, size=13, color=self.muted_color, font_family=FONT_FAMILY),
                                ft.Text(value, size=18, weight=ft.FontWeight.BOLD,
                                        font_family="Vazirmatn-Bold", color=self.text_color),
                            ],
                            spacing=2, expand=True,
                        ),
                        ft.Text(sub, size=13, font_family=FONT_FAMILY,
                                color=GREEN_UP if sub.startswith("+") else RED_DOWN),
                    ],
                    spacing=14,
                ),
                bgcolor=self.card_color,
                border_radius=18,
                padding=16,
            )

        cards = [
            summary_card(
                ft.CupertinoIcons.CIRCLE_GRID_HEX,
                self.tr("home_gold"),
                f"{fmt_int(gold_18)} {self.tr('unit_toman')}" if gold_18 else "—",
                "+0.0%",
                GOLD,
            ),
            summary_card(
                ft.CupertinoIcons.MONEY_DOLLAR,
                self.tr("home_dollar"),
                f"{fmt_int(usd_irr or 0)} {self.tr('unit_toman')}" if usd_irr else "—",
                "+0.0%",
                GOLD_SOFT,
            ),
        ]
        if btc:
            change = btc.get("change_24h") or 0
            cards.append(
                summary_card(
                    ft.CupertinoIcons.BITCOIN,
                    self.tr("home_bitcoin"),
                    f"${fmt_price(btc.get('price_usd'))}",
                    f"{'+' if change >= 0 else ''}{change:.2f}%",
                    GOLD_BRIGHT,
                )
            )

        quick_links = ft.Row(
            [
                ft.OutlinedButton(
                    content=ft.Text(self.tr("tab_crypto"), font_family=FONT_FAMILY),
                    icon=ft.CupertinoIcons.BITCOIN,
                    on_click=lambda e: self._go_to_tab(1),
                ),
                ft.OutlinedButton(
                    content=ft.Text(self.tr("tab_gold"), font_family=FONT_FAMILY),
                    icon=ft.CupertinoIcons.CIRCLE_GRID_HEX,
                    on_click=lambda e: self._go_to_tab(2),
                ),
                ft.OutlinedButton(
                    content=ft.Text(self.tr("tab_currency"), font_family=FONT_FAMILY),
                    icon=ft.CupertinoIcons.MONEY_DOLLAR,
                    on_click=lambda e: self._go_to_tab(3),
                ),
            ],
            wrap=True,
            spacing=8,
        )

        return ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(APP_NAME_FA, size=28, weight=ft.FontWeight.BOLD,
                                     font_family="Vazirmatn-Bold", color=GOLD),
                            ft.Text(self.tr("home_summary"), size=14, color=self.muted_color,
                                     font_family=FONT_FAMILY),
                        ],
                        spacing=4,
                    ),
                    padding=ft.Padding.only(left=20, right=20, top=24, bottom=16),
                ),
                ft.Container(
                    content=ft.Column(cards, spacing=12),
                    padding=ft.Padding.symmetric(horizontal=20),
                ),
                ft.Container(
                    content=quick_links,
                    padding=ft.Padding.only(left=20, right=20, top=20),
                ),
                ft.Container(
                    content=ft.Text(self._last_update_text(), size=11, color=self.muted_color,
                                     font_family=FONT_FAMILY),
                    padding=ft.Padding.only(left=20, top=16),
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================================
    # تب کریپتو
    # =====================================================================
    def _build_crypto_tab(self):
        items = self.crypto_items
        query = self.crypto_search.strip().lower()
        if query:
            items = [
                c for c in items
                if query in (c.get("name") or "").lower()
                or query in (c.get("symbol") or "").lower()
            ]

        def row_item(c):
            change = c.get("change_24h") or 0
            up = change >= 0
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Text(str(c.get("rank") or ""), size=12, color=self.muted_color, width=24,
                                 font_family=FONT_FAMILY),
                        ft.Image(src=c.get("image"), width=32, height=32, border_radius=16,
                                  error_content=ft.Icon(ft.CupertinoIcons.BITCOIN, color=GOLD)),
                        ft.Column(
                            [
                                ft.Text(c.get("name"), size=14, weight=ft.FontWeight.W_600,
                                         font_family="Vazirmatn-Medium", color=self.text_color),
                                ft.Text(c.get("symbol"), size=12, color=self.muted_color,
                                         font_family=FONT_FAMILY),
                            ],
                            spacing=1, expand=True,
                        ),
                        ft.Column(
                            [
                                ft.Text(f"${fmt_price(c.get('price_usd'))}", size=14,
                                         weight=ft.FontWeight.W_600, font_family="Vazirmatn-Medium",
                                         color=self.text_color),
                                ft.Container(
                                    content=ft.Text(f"{'+' if up else ''}{change:.2f}%", size=12,
                                                      color=WHITE, font_family=FONT_FAMILY),
                                    bgcolor=GREEN_UP if up else RED_DOWN,
                                    border_radius=8,
                                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                                ),
                            ],
                            spacing=3, horizontal_alignment=ft.CrossAxisAlignment.END,
                        ),
                    ],
                    spacing=10,
                ),
                bgcolor=self.card_color,
                border_radius=14,
                padding=12,
                margin=ft.Margin.only(bottom=8),
            )

        list_view = ft.ListView(
            controls=[row_item(c) for c in items] if items else [],
            spacing=0,
            padding=ft.Padding.only(left=20, right=20, bottom=90),
            expand=True,
        )

        body_content = list_view if items else self._empty_state(self.tr("no_results"))

        return ft.Column(
            [
                self._header(self.tr("cryptocurrencies"), show_search=True,
                              on_search=self._on_crypto_search, on_refresh=self._on_manual_refresh),
                ft.Container(content=body_content, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    def _on_crypto_search(self, e):
        self.crypto_search = e.control.value or ""
        self._render_body()
        self.page.update()

    # =====================================================================
    # تب طلا
    # =====================================================================
    def _build_gold_tab(self):
        def row_item(key, name_fa, name_en):
            raw_value = self.iran_gold.get(key)
            is_ounce = key == "gold_ounce"
            
            if raw_value is None:
                display = "—"
            elif is_ounce:
                display = f"${fmt_price(raw_value)}"
            elif self.base_currency == "usd":
                usd_irr = self.iran_gold.get("usd_irr_free") or 1
                display = f"${fmt_price((raw_value * 10) / usd_irr)}"
            else:
                display = f"{fmt_int(raw_value)} {self.tr('unit_toman')}"

            label = name_fa if self.lang == "fa" else name_en
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(ft.CupertinoIcons.CIRCLE_GRID_HEX, color=BLACK, size=20),
                            bgcolor=GOLD,
                            width=40, height=40, border_radius=20,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Text(label, size=14, weight=ft.FontWeight.W_600,
                                 font_family="Vazirmatn-Medium", color=self.text_color, expand=True),
                        ft.Text(display, size=15, weight=ft.FontWeight.BOLD,
                                 font_family="Vazirmatn-Bold", color=GOLD),
                    ],
                    spacing=12,
                ),
                bgcolor=self.card_color,
                border_radius=14,
                padding=14,
                margin=ft.Margin.only(bottom=8),
            )

        list_view = ft.ListView(
            controls=[row_item(k, fa, en) for k, fa, en in GOLD_ITEMS],
            spacing=0,
            padding=ft.Padding.only(left=20, right=20, bottom=90),
            expand=True,
        )

        return ft.Column(
            [
                self._header(self.tr("gold_and_coin"), on_refresh=self._on_manual_refresh),
                ft.Container(content=list_view, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    # =====================================================================
    # تب ارزها
    # =====================================================================
    def _build_currency_tab(self):
        query = self.currency_search.strip().lower()
        currencies = WORLD_CURRENCIES
        if query:
            currencies = [
                c for c in currencies
                if query in c[0].lower() or query in c[1].lower() or query in c[2].lower()
            ]

        usd_irr = self.iran_gold.get("usd_irr_free")

        def row_item(code, name_fa, name_en, flag):
            rate_to_usd = self.world_rates.get(code)  # چند واحد از این ارز = ۱ دلار
            if not rate_to_usd or not usd_irr:
                display = "—"
            elif self.base_currency == "usd":
                display = f"${fmt_price(1 / rate_to_usd)}"
            else:
                toman_per_usd = usd_irr
                toman_value = toman_per_usd / rate_to_usd
                display = f"{fmt_int(toman_value)} {self.tr('unit_toman')}"

            label = name_fa if self.lang == "fa" else name_en
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Text(flag, size=24),
                        ft.Column(
                            [
                                ft.Text(label, size=14, weight=ft.FontWeight.W_600,
                                         font_family="Vazirmatn-Medium", color=self.text_color),
                                ft.Text(code, size=12, color=self.muted_color, font_family=FONT_FAMILY),
                            ],
                            spacing=1, expand=True,
                        ),
                        ft.Text(display, size=15, weight=ft.FontWeight.BOLD,
                                 font_family="Vazirmatn-Bold", color=GOLD),
                    ],
                    spacing=12,
                ),
                bgcolor=self.card_color,
                border_radius=14,
                padding=14,
                margin=ft.Margin.only(bottom=8),
            )

        items = [row_item(*c) for c in currencies]
        body_content = ft.ListView(
            controls=items, spacing=0,
            padding=ft.Padding.only(left=20, right=20, bottom=90),
            expand=True,
        ) if items else self._empty_state(self.tr("no_results"))

        return ft.Column(
            [
                self._header(self.tr("world_currencies"), show_search=True,
                              on_search=self._on_currency_search, on_refresh=self._on_manual_refresh),
                ft.Container(content=body_content, expand=True),
            ],
            spacing=0,
            expand=True,
        )

    def _on_currency_search(self, e):
        self.currency_search = e.control.value or ""
        self._render_body()
        self.page.update()

    # =====================================================================
    # تب تنظیمات
    # =====================================================================
    def _build_settings_tab(self):
        def setting_row(icon, title, control):
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, color=GOLD, size=20),
                        ft.Text(title, size=14, font_family="Vazirmatn-Medium",
                                 color=self.text_color, expand=True),
                        control,
                    ],
                    spacing=12,
                ),
                bgcolor=self.card_color,
                border_radius=14,
                padding=14,
                margin=ft.Margin.only(bottom=8),
            )

        lang_toggle = ft.CupertinoSlidingSegmentedButton(
            selected_index=0 if self.lang == "fa" else 1,
            controls=[ft.Text("فارسی"), ft.Text("English")],
            thumb_color=GOLD,
            on_change=self._on_lang_change,
        )
        theme_toggle = ft.CupertinoSlidingSegmentedButton(
            selected_index=0 if self.theme_mode == "dark" else 1,
            controls=[ft.Text(self.tr("theme_dark")), ft.Text(self.tr("theme_light"))],
            thumb_color=GOLD,
            on_change=self._on_theme_change,
        )
        currency_toggle = ft.CupertinoSlidingSegmentedButton(
            selected_index=0 if self.base_currency == "toman" else 1,
            controls=[ft.Text(self.tr("toman")), ft.Text(self.tr("dollar"))],
            thumb_color=GOLD,
            on_change=self._on_currency_change,
        )

        about_btn = ft.TextButton(
            content=ft.Row(
                [ft.Icon(ft.CupertinoIcons.INFO, color=GOLD, size=18),
                 ft.Text(self.tr("about"), color=GOLD, font_family="Vazirmatn-Medium")],
                spacing=8,
            ),
            on_click=self._show_about_dialog,
        )

        return ft.Column(
            [
                self._header(self.tr("settings_title")),
                ft.Container(
                    content=ft.Column(
                        [
                            setting_row(ft.CupertinoIcons.GLOBE, self.tr("language"), lang_toggle),
                            setting_row(ft.CupertinoIcons.MOON_STARS, self.tr("theme"), theme_toggle),
                            setting_row(ft.CupertinoIcons.MONEY_DOLLAR, self.tr("base_currency"), currency_toggle),
                            ft.Container(content=about_btn, padding=ft.Padding.only(top=10, left=6)),
                        ],
                        spacing=0,
                    ),
                    padding=ft.Padding.symmetric(horizontal=20),
                ),
            ],
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def _show_about_dialog(self, e):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(APP_NAME_FA if self.lang == "fa" else "Arzshenas",
                            font_family="Vazirmatn-Bold", color=GOLD),
            content=ft.Text(
                f"{self.tr('about_text')}\n\n{self.tr('version')}: {APP_VERSION}",
                font_family=FONT_FAMILY,
            ),
            actions=[ft.TextButton(
                content=ft.Text(self.tr("close"), font_family=FONT_FAMILY),
                on_click=lambda e: self.page.pop_dialog(),
            )],
        )
        self.page.show_dialog(dlg)

    async def _on_lang_change(self, e):
        self.lang = "fa" if e.control.selected_index == 0 else "en"
        self.page.rtl = self.lang == "fa"
        await self._save_prefs()
        self._build_shell()

    async def _on_theme_change(self, e):
        self.theme_mode = "dark" if e.control.selected_index == 0 else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if self.theme_mode == "dark" else ft.ThemeMode.LIGHT
        self.page.bgcolor = self.bg_color
        await self._save_prefs()
        self._build_shell()

    async def _on_currency_change(self, e):
        self.base_currency = "toman" if e.control.selected_index == 0 else "usd"
        await self._save_prefs()
        self._render_body()
        self.page.update()

    # =====================================================================
    # به‌روزرسانی داده‌ها
    # =====================================================================
    async def _on_manual_refresh(self, e):
        await self.refresh_all()

    async def refresh_all(self, initial=False):
        prev_gold = self.iran_gold.get("gold_18")
        prev_usd = self.iran_gold.get("usd_irr_free")

        crypto, ok1 = await self.data.get_crypto()
        rates, ok2 = await self.data.get_world_rates()
        gold, ok3 = await self.data.get_iran_gold_currency()

        self.crypto_items = crypto
        self.world_rates = rates
        self.iran_gold = gold
        self.online = ok1 or ok2 or ok3
        self.last_update_ts = time.time()

        self.offline_banner.visible = not self.online
        self._render_body()
        self.page.update()

        if not initial:
            self._maybe_notify_price_change(prev_gold, gold.get("gold_18"), self.tr("home_gold"))
            self._maybe_notify_price_change(prev_usd, gold.get("usd_irr_free"), self.tr("home_dollar"))

    def _maybe_notify_price_change(self, old_val, new_val, label):
        try:
            if not old_val or not new_val:
                return
            pct = abs(new_val - old_val) / old_val * 100
            if pct >= PRICE_ALERT_THRESHOLD_PCT:
                direction = "↑" if new_val > old_val else "↓"
                self.page.show_dialog(
                    ft.SnackBar(
                        content=ft.Text(
                            f"{self.tr('notif_title')}: {label} {direction} {pct:.1f}%",
                            font_family=FONT_FAMILY,
                        ),
                        bgcolor=GOLD,
                    )
                )
        except Exception:
            pass

    async def _auto_refresh_loop(self):
        while True:
            await asyncio.sleep(AUTO_REFRESH_SECONDS)  # 300 ثانیه = ۵ دقیقه
            try:
                await self.refresh_all()
            except Exception:
                pass


# ============================================================================
# نقطه‌ی ورود برنامه
# ============================================================================
async def main(page: ft.Page):
    try:
        app = ArzshenasApp(page)
        await app.init()
    except Exception as ex:
        # اگر خطایی در راه‌اندازی برنامه رخ دهد، به‌جای بسته‌شدن خاموش، پیام آن
        # را هم در کنسول چاپ می‌کنیم و هم روی خود صفحه نمایش می‌دهیم تا قابل مشاهده باشد
        import traceback
        traceback.print_exc()
        page.add(
            ft.Text(
                f"خطا در راه‌اندازی برنامه:\n{ex}",
                color="red",
                selectable=True,
            )
        )
        page.update()


if __name__ == "__main__":
    ft.run(main)
