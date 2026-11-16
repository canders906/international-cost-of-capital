"""FINC 470 international cost of capital. Run: streamlit run app.py."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO, StringIO
import json
import math
import re
import unicodedata

import pandas as pd
import pycountry
from babel.numbers import get_territory_currencies
import requests
import streamlit as st
from bs4 import BeautifulSoup

BETA_URL = 'https://pages.stern.nyu.edu/~adamodar/pc/datasets/betas.xls'
SPREAD_URL = 'https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/ratings.html'
TAX_URL = 'https://sdmx.oecd.org/public/rest/v1/data/OECD.CTP.TPS,DSD_TAX_CIT@DF_CIT,2.0/.?startPeriod=2000&format=csvfile'
BONDS_URL = 'https://tradingeconomics.com/bonds'
DEFAULT_INDUSTRY = 'Software (System & Application)'
# Verified source snapshots, not substituted silently for live data.
SNAPSHOT = {'betas': {'data': {'Advertising': 0.930085673859911, 'Aerospace/Defense': 0.846668742124111, 'Air Transport': 0.7040501862693873, 'Apparel': 0.7579820882045375, 'Auto & Truck': 1.2690329072913427, 'Auto Parts': 1.0217137832780625, 'Bank (Money Center)': 0.3410587595479105, 'Banks (Regional)': 0.2865156418030888, 'Beverage (Alcoholic)': 0.6131715419678557, 'Beverage (Soft)': 0.5556711918551647, 'Broadcasting': 0.28636169661672445, 'Brokerage & Investment Banking': 0.5808487698048416, 'Building Materials': 0.9301623477287291, 'Business & Consumer Services': 0.7735875598670026, 'Cable TV': 0.3523921209643926, 'Chemical (Basic)': 0.5800328658623819, 'Chemical (Diversified)': 0.36655193179254153, 'Chemical (Specialty)': 0.7922271711710575, 'Coal & Related Energy': 1.0165349872490315, 'Computer Services': 0.9155102559970569, 'Computers/Peripherals': 1.3050624188250832, 'Construction Supplies': 1.0160678372067562, 'Diversified': 0.7889302024061987, 'Drugs (Biotechnology)': 1.034128692045902, 'Drugs (Pharmaceutical)': 0.8862112018778732, 'Education': 0.6601955817730791, 'Electrical Equipment': 1.1477945494288007, 'Electronics (Consumer & Office)': 0.8298525821858579, 'Electronics (General)': 0.8973653021365886, 'Engineering/Construction': 1.094912241925567, 'Entertainment': 0.7371838269272858, 'Environmental & Waste Services': 0.814469065497658, 'Farming/Agriculture': 0.8130198178522071, 'Financial Svcs. (Non-bank & Insurance)': 0.3188823716863237, 'Food Processing': 0.45741810112318915, 'Food Wholesalers': 0.6408819228030607, 'Furn/Home Furnishings': 0.6247880689027374, 'Green & Renewable Energy': 0.46330103394106914, 'Healthcare Products': 0.829063339182968, 'Healthcare Support Services': 0.6889158973179456, 'Heathcare Information and Technology': 0.9913008450033202, 'Homebuilding': 0.7849604569802948, 'Hospitals/Healthcare Facilities': 0.5517295035260499, 'Hotel/Gaming': 0.8322513645728964, 'Household Products': 0.7178159032286779, 'Information Services': 0.7371769598623608, 'Insurance (General)': 0.5636395230036526, 'Insurance (Life)': 0.4271563388858468, 'Insurance (Prop/Cas.)': 0.43565645519640217, 'Investments & Asset Management': 0.5297158729912839, 'Machinery': 0.8679764970807725, 'Metals & Mining': 0.963642813760502, 'Office Equipment & Services': 0.980603950937201, 'Oil/Gas (Integrated)': 0.2712192455295165, 'Oil/Gas (Production and Exploration)': 0.562759894026207, 'Oil/Gas Distribution': 0.4650757918129057, 'Oilfield Svcs/Equip.': 0.7430388962534321, 'Packaging & Container': 0.7230693503118022, 'Paper/Forest Products': 0.7215533176034462, 'Power': 0.31002381536217716, 'Precious Metals': 0.7932430128835662, 'Publishing & Newspapers': 0.47730712965508676, 'R.E.I.T.': 0.39290436962561487, 'Real Estate (Development)': 0.4782878873556669, 'Real Estate (General/Diversified)': 0.57785949402086, 'Real Estate (Operations & Services)': 0.8148915126864962, 'Recreation': 0.6950913817523879, 'Reinsurance': 0.43840910722706555, 'Restaurant/Dining': 0.767419655502052, 'Retail (Automotive)': 0.6984325625385885, 'Retail (Building Supply)': 1.3070143643127536, 'Retail (Distributors)': 0.7826829040437357, 'Retail (General)': 0.7599637023048608, 'Retail (Grocery and Food)': 0.804751465127235, 'Retail (REITs)': 0.4361730155949174, 'Retail (Special Lines)': 0.9487830646597303, 'Rubber& Tires': 0.14353369356004206, 'Semiconductor': 1.48925822268736, 'Semiconductor Equip': 1.3480733569303134, 'Shipbuilding & Marine': 0.644012905556584, 'Shoe': 0.9336746513867349, 'Software (Entertainment)': 1.0127806880948524, 'Software (Internet)': 1.5460643073174678, 'Software (System & Application)': 1.225391886520662, 'Steel': 0.9035142702396447, 'Telecom (Wireless)': 0.3872590553991877, 'Telecom. Equipment': 0.8634913488563035, 'Telecom. Services': 0.3654342533759909, 'Tobacco': 0.6775903166712723, 'Transportation': 0.67531101084817, 'Transportation (Railroads)': 0.8069481235657714, 'Trucking': 0.8504180575613394, 'Utility (General)': 0.14861284002770483, 'Utility (Water)': 0.281177328534438}, 'date': '2026-01-05', 'retrieved': '2026-11-16T15:52:20+00:00'}, 'spread': {'data': 0.0111, 'date': 'January 2026', 'retrieved': '2026-11-16T15:52:20+00:00'}, 'taxes': {'data': {'ABW': {'value': 0.22, 'date': '2026'}, 'AGO': {'value': 0.25, 'date': '2026'}, 'AIA': {'value': 0.0, 'date': '2026'}, 'ALB': {'value': 0.15, 'date': '2026'}, 'AND': {'value': 0.1, 'date': '2026'}, 'ARE': {'value': 0.09, 'date': '2026'}, 'ARG': {'value': 0.35, 'date': '2026'}, 'ARM': {'value': 0.18, 'date': '2026'}, 'ATG': {'value': 0.25, 'date': '2026'}, 'AUS': {'value': 0.3, 'date': '2026'}, 'AUT': {'value': 0.23, 'date': '2026'}, 'AZE': {'value': 0.2, 'date': '2026'}, 'BEL': {'value': 0.25, 'date': '2026'}, 'BEN': {'value': 0.3, 'date': '2026'}, 'BFA': {'value': 0.275, 'date': '2026'}, 'BGR': {'value': 0.1, 'date': '2026'}, 'BHR': {'value': 0.0, 'date': '2026'}, 'BHS': {'value': 0.0, 'date': '2026'}, 'BIH': {'value': 0.1, 'date': '2026'}, 'BLZ': {'value': 0.0, 'date': '2026'}, 'BMU': {'value': 0.0, 'date': '2026'}, 'BRA': {'value': 0.34, 'date': '2026'}, 'BRB': {'value': 0.09, 'date': '2026'}, 'BRN': {'value': 0.185, 'date': '2026'}, 'BWA': {'value': 0.22, 'date': '2026'}, 'CAN': {'value': 0.26, 'date': '2026'}, 'CHE': {'value': 0.19471871, 'date': '2026'}, 'CHL': {'value': 0.27, 'date': '2026'}, 'CHN': {'value': 0.25, 'date': '2026'}, 'CIV': {'value': 0.25, 'date': '2026'}, 'CMR': {'value': 0.33, 'date': '2026'}, 'COD': {'value': 0.3, 'date': '2026'}, 'COG': {'value': 0.28, 'date': '2026'}, 'COK': {'value': 0.2, 'date': '2026'}, 'COL': {'value': 0.35, 'date': '2025'}, 'CPV': {'value': 0.204, 'date': '2026'}, 'CRI': {'value': 0.3, 'date': '2026'}, 'CUW': {'value': 0.15, 'date': '2026'}, 'CYM': {'value': 0.0, 'date': '2026'}, 'CZE': {'value': 0.21, 'date': '2026'}, 'DEU': {'value': 0.30133026, 'date': '2026'}, 'DJI': {'value': 0.25, 'date': '2026'}, 'DMA': {'value': 0.25, 'date': '2026'}, 'DNK': {'value': 0.22, 'date': '2026'}, 'DOM': {'value': 0.27, 'date': '2026'}, 'EGY': {'value': 0.225, 'date': '2026'}, 'ESP': {'value': 0.25, 'date': '2026'}, 'EST': {'value': 0.22, 'date': '2026'}, 'FIN': {'value': 0.2, 'date': '2026'}, 'FJI': {'value': 0.25, 'date': '2026'}, 'FRA': {'value': 0.3613, 'date': '2026'}, 'FRO': {'value': 0.18, 'date': '2026'}, 'GAB': {'value': 0.3, 'date': '2026'}, 'GBR': {'value': 0.25, 'date': '2026'}, 'GEO': {'value': 0.15, 'date': '2026'}, 'GGY': {'value': 0.0, 'date': '2026'}, 'GIB': {'value': 0.15, 'date': '2026'}, 'GRC': {'value': 0.22, 'date': '2026'}, 'GRD': {'value': 0.28, 'date': '2026'}, 'GRL': {'value': 0.265, 'date': '2026'}, 'GTM': {'value': 0.25, 'date': '2026'}, 'HKG': {'value': 0.165, 'date': '2026'}, 'HND': {'value': 0.25, 'date': '2026'}, 'HRV': {'value': 0.18, 'date': '2026'}, 'HTI': {'value': 0.3, 'date': '2026'}, 'HUN': {'value': 0.09, 'date': '2026'}, 'IDN': {'value': 0.22, 'date': '2026'}, 'IMN': {'value': 0.0, 'date': '2026'}, 'IND': {'value': 0.25170000000000003, 'date': '2026'}, 'IRL': {'value': 0.125, 'date': '2026'}, 'ISL': {'value': 0.2, 'date': '2026'}, 'ISR': {'value': 0.23, 'date': '2025'}, 'ITA': {'value': 0.2781, 'date': '2026'}, 'JAM': {'value': 0.25, 'date': '2026'}, 'JEY': {'value': 0.0, 'date': '2026'}, 'JOR': {'value': 0.2, 'date': '2026'}, 'JPN': {'value': 0.2974, 'date': '2026'}, 'KAZ': {'value': 0.2, 'date': '2026'}, 'KEN': {'value': 0.3, 'date': '2026'}, 'KNA': {'value': 0.25, 'date': '2026'}, 'KOR': {'value': 0.275, 'date': '2026'}, 'KWT': {'value': 0.15, 'date': '2026'}, 'LBR': {'value': 0.25, 'date': '2026'}, 'LCA': {'value': 0.3, 'date': '2026'}, 'LIE': {'value': 0.125, 'date': '2026'}, 'LKA': {'value': 0.3, 'date': '2026'}, 'LTU': {'value': 0.17, 'date': '2026'}, 'LUX': {'value': 0.23870000000000002, 'date': '2026'}, 'LVA': {'value': 0.2, 'date': '2026'}, 'MAC': {'value': 0.12, 'date': '2026'}, 'MAR': {'value': 0.35, 'date': '2026'}, 'MCO': {'value': 0.25, 'date': '2026'}, 'MDA': {'value': 0.12, 'date': '2026'}, 'MDV': {'value': 0.15, 'date': '2026'}, 'MEX': {'value': 0.3, 'date': '2026'}, 'MKD': {'value': 0.1, 'date': '2026'}, 'MLT': {'value': 0.35, 'date': '2026'}, 'MNE': {'value': 0.15, 'date': '2026'}, 'MNG': {'value': 0.25, 'date': '2026'}, 'MRT': {'value': 0.25, 'date': '2026'}, 'MSR': {'value': 0.3, 'date': '2026'}, 'MUS': {'value': 0.15, 'date': '2026'}, 'MYS': {'value': 0.24, 'date': '2026'}, 'NAM': {'value': 0.32, 'date': '2026'}, 'NGA': {'value': 0.3, 'date': '2026'}, 'NLD': {'value': 0.258, 'date': '2026'}, 'NOR': {'value': 0.22, 'date': '2026'}, 'NZL': {'value': 0.28, 'date': '2026'}, 'OMN': {'value': 0.15, 'date': '2026'}, 'PAK': {'value': 0.29, 'date': '2026'}, 'PAN': {'value': 0.25, 'date': '2026'}, 'PER': {'value': 0.295, 'date': '2026'}, 'PHL': {'value': 0.25, 'date': '2026'}, 'PNG': {'value': 0.3, 'date': '2026'}, 'POL': {'value': 0.19, 'date': '2026'}, 'PRT': {'value': 0.295, 'date': '2026'}, 'PRY': {'value': 0.1, 'date': '2026'}, 'QAT': {'value': 0.1, 'date': '2026'}, 'ROU': {'value': 0.16, 'date': '2026'}, 'SAU': {'value': 0.2, 'date': '2026'}, 'SEN': {'value': 0.3, 'date': '2026'}, 'SGP': {'value': 0.17, 'date': '2026'}, 'SLE': {'value': 0.25, 'date': '2026'}, 'SMR': {'value': 0.18, 'date': '2026'}, 'SRB': {'value': 0.15, 'date': '2026'}, 'SVK': {'value': 0.24, 'date': '2026'}, 'SVN': {'value': 0.22, 'date': '2026'}, 'SWE': {'value': 0.20600000000000002, 'date': '2026'}, 'SWZ': {'value': 0.25, 'date': '2026'}, 'SYC': {'value': 0.25, 'date': '2026'}, 'TCA': {'value': 0.0, 'date': '2026'}, 'TGO': {'value': 0.27, 'date': '2026'}, 'THA': {'value': 0.2, 'date': '2026'}, 'TTO': {'value': 0.3, 'date': '2026'}, 'TUN': {'value': 0.2, 'date': '2026'}, 'TUR': {'value': 0.25, 'date': '2025'}, 'UKR': {'value': 0.18, 'date': '2026'}, 'URY': {'value': 0.25, 'date': '2026'}, 'USA': {'value': 0.255285, 'date': '2026'}, 'UZB': {'value': 0.15, 'date': '2026'}, 'VCT': {'value': 0.28, 'date': '2026'}, 'VGB': {'value': 0.0, 'date': '2026'}, 'VNM': {'value': 0.2, 'date': '2026'}, 'WSM': {'value': 0.27, 'date': '2026'}, 'ZAF': {'value': 0.27, 'date': '2026'}, 'ZMB': {'value': 0.3, 'date': '2026'}}, 'date': 'Latest observation year shown separately for each country', 'retrieved': '2026-11-16T15:52:20+00:00'}, 'bonds': {'data': {'United States': {'value': 0.0513, 'date': '2026-11-16'}}, 'date': '2026-11-16; U.S. source-page snapshot only', 'retrieved': '2026-11-16T15:52:20+00:00'}}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def fetch(url):
    r = requests.get(url, timeout=(8, 25), headers={'User-Agent': 'FINC470-CostOfCapital/1.0', 'Accept': '*/*'})
    r.raise_for_status()
    return r.content


def parse_betas(content):
    sheets = pd.read_excel(BytesIO(content), sheet_name=None, header=None)
    for frame in sheets.values():
        for i, row in frame.iterrows():
            labels = [str(v).strip().lower() for v in row]
            if 'industry name' not in labels or 'unlevered beta' not in labels:
                continue
            ni, bi = labels.index('industry name'), labels.index('unlevered beta')
            result = {}
            for _, r in frame.iloc[i + 1:].iterrows():
                name = str(r.iloc[ni]).strip()
                try:
                    beta = float(r.iloc[bi])
                    if name != 'nan' and not name.lower().startswith('total') and math.isfinite(beta):
                        result[name] = beta
                except (ValueError, TypeError):
                    pass
            dates = [v for v in frame.iloc[:i].to_numpy().flat if isinstance(v, datetime)]
            if result:
                return result, dates[0].date().isoformat() if dates else 'Source date not reported'
    raise ValueError('Industry Name / Unlevered beta columns not found; source layout may have changed.')


def parse_spread(content):
    soup = BeautifulSoup(content, 'html.parser')
    text = re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))
    if 'For large non-financial service firms' not in text:
        raise ValueError('Large non-financial firm table not identified.')
    for tr in soup.find_all('tr'):
        cells = [c.get_text(' ', strip=True) for c in tr.find_all(['td', 'th'], recursive=False)]
        # The left-hand table is the large non-financial firm table; do not use the right-hand financial column.
        for i, cell in enumerate(cells[:4]):
            if re.sub(r'\s+', '', cell) == 'Baa2/BBB' and i + 1 < len(cells):
                m = re.fullmatch(r'([\d.]+)\s*%', cells[i + 1])
                if m:
                    date = re.search(r'as of\s+([A-Za-z]+\s+20\d{2})', text, re.I)
                    return float(m.group(1)) / 100, date.group(1) if date else 'Source date not reported'
    raise ValueError('Baa2/BBB spread not found in large non-financial firm table.')


def parse_taxes(content):
    df = pd.read_csv(BytesIO(content))
    for col, value in {'MEASURE': 'CIT_C', 'TARGETING': 'ST', 'SECTOR': 'S13', 'FREQ': 'A', 'UNIT_MEASURE': 'PT_INC_TAX'}.items():
        df = df[df[col] == value]
    df['TIME_PERIOD'] = pd.to_numeric(df['TIME_PERIOD'], errors='coerce')
    df['OBS_VALUE'] = pd.to_numeric(df['OBS_VALUE'], errors='coerce')
    df = df.dropna(subset=['OBS_VALUE', 'TIME_PERIOD'])
    df = df[df.TIME_PERIOD <= datetime.now().year]
    result = {}
    for code, group in df.groupby('REF_AREA'):
        latest = group[group.TIME_PERIOD == group.TIME_PERIOD.max()]
        values = latest.OBS_VALUE.unique()
        if len(values) != 1:
            continue  # Never arbitrarily select among ambiguous series.
        rate = float(values[0]) / 100
        if 0 <= rate <= 1:
            result[code] = {'value': rate, 'date': str(int(latest.TIME_PERIOD.max()))}
    if 'USA' not in result:
        raise ValueError('OECD combined statutory U.S. rate unavailable.')
    return result, 'Latest observation year shown separately for each country'


def normalize(name):
    aliases = {'united states of america': 'United States', 'korea, republic of': 'South Korea',
               'korea': 'South Korea', 'turkey': 'Türkiye', 'czech republic': 'Czechia',
               'russian federation': 'Russia', 'viet nam': 'Vietnam', 'slovak republic': 'Slovakia'}
    return aliases.get(name.lower(), name)


def parse_bonds(content):
    soup = BeautifulSoup(content, 'html.parser')
    result = {}
    for tr in soup.select('tr'):
        link = tr.select_one('a[href*="/government-bond-yield"]')
        if not link:
            continue
        cells = tr.find_all('td', recursive=False)
        if len(cells) < 2:
            continue
        name = normalize(link.get_text(' ', strip=True))
        value_node = tr.select_one('[id="p"], [data-field="Last"]')
        value_text = (value_node or cells[1]).get_text(' ', strip=True).replace('%', '').replace(',', '')
        try:
            value = float(value_text) / 100
        except ValueError:
            continue
        if not -0.99 < value < 2:
            continue
        date_node = tr.select_one('[id="date"], time, [data-field="Date"]')
        date = date_node.get('datetime') or date_node.get_text(' ', strip=True) if date_node else 'Source timestamp not exposed'
        result[name] = {'value': value, 'date': date}
    if not result:
        raise ValueError('Trading Economics returned no readable yield rows (dynamic page or access restriction).')
    return result, 'Observation timestamps as displayed by Trading Economics'


@st.cache_data(ttl=3600, show_spinner=False)
def load_source(kind):
    urls = {'betas': BETA_URL, 'spread': SPREAD_URL, 'taxes': TAX_URL, 'bonds': BONDS_URL}
    parsers = {'betas': parse_betas, 'spread': parse_spread, 'taxes': parse_taxes, 'bonds': parse_bonds}
    url = urls[kind]
    try:
        content = fetch(url)
        if kind == 'bonds' and b'partial' in content and b'te-markets-body' in content:
            # Public table fragment requested by the source page itself; no API key.
            content = fetch(BONDS_URL + '?partial=markets')
        data, date = parsers[kind](content)
        return dict(data=data, date=date, retrieved=now(), url=url, status='Fetched', error='')
    except Exception as exc:
        snap = SNAPSHOT.get(kind)
        return dict(data=snap['data'] if snap else {}, date=snap['date'] if snap else 'Unavailable',
                    retrieved=snap['retrieved'] if snap else '', url=url,
                    status='Saved snapshot' if snap else 'Unavailable', error=str(exc), attempted=now())


def calculate(beta, tax, debt, erp, us_yield, foreign_yield, spread, foreign_spread=None):
    values = [beta, tax, debt, erp, us_yield, foreign_yield, spread]
    if foreign_spread is not None:
        values.append(foreign_spread)
    if not all(math.isfinite(x) for x in values):
        raise ValueError('All inputs must be finite.')
    if not 0 <= debt < 1 or not 0 <= tax <= 1 or min(us_yield, foreign_yield) <= -1:
        raise ValueError('Debt must be below 100%; tax must be 0–100%; yields must exceed −100%.')
    beta_e = beta * (1 + (1 - tax) * debt / (1 - debt))
    factor = (1 + foreign_yield) / (1 + us_yield)
    re_us = us_yield + beta_e * erp
    re_foreign = (1 + re_us) * factor - 1
    sf = spread * factor if foreign_spread is None else foreign_spread
    rd_us, rd_foreign = us_yield + spread, foreign_yield + sf
    return dict(beta_e=beta_e, factor=factor, foreign_spread=sf,
                equity_us=re_us, equity_foreign=re_foreign, debt_us=rd_us, debt_foreign=rd_foreign,
                after_tax_us=rd_us * (1 - tax), after_tax_foreign=rd_foreign * (1 - tax),
                wacc_us=(1 - debt) * re_us + debt * rd_us * (1 - tax),
                wacc_foreign=(1 - debt) * re_foreign + debt * rd_foreign * (1 - tax))


def country_catalog():
    return {normalize(c.name): c.alpha_3 for c in pycountry.countries}


def main():
    st.set_page_config(page_title='International Cost of Capital', page_icon='🌐', layout='wide')
    st.title('International Cost of Capital')
    st.caption('FINC 470 · Compare the same project in USD and a selected country’s currency')
    if st.button('Refresh source data', type='primary'):
        load_source.clear()
        st.rerun()
    with st.spinner('Retrieving industry betas, credit spreads, tax rates and government yields…'):
        kinds = ['betas', 'spread', 'taxes', 'bonds']
        with ThreadPoolExecutor(max_workers=4) as pool:
            sources = dict(zip(kinds, pool.map(load_source, kinds)))
    for kind, source in sources.items():
        if source['error']:
            st.warning(f"{kind.title()}: {source['status']}. Refresh failed: {source['error']}. "
                       'Review the dated source values below or enable a manual override.')
    betas = sources['betas']['data']
    if not betas:
        st.error('Industry data unavailable. Refresh later; the industry comparison requires verified beta data.')
        st.stop()
    countries = country_catalog()
    with st.sidebar:
        st.header('Project inputs')
        industry_names = sorted(betas)
        industry = st.selectbox('Industry', industry_names, index=industry_names.index(DEFAULT_INDUSTRY))
        country_names = sorted(countries)
        country = st.selectbox('Target country', country_names, index=country_names.index('United States'))
        code = countries[country]
        territory = pycountry.countries.get(alpha_3=code).alpha_2
        currency_codes = get_territory_currencies(territory)
        currency = st.text_input('Target currency label', value='/'.join(currency_codes) or f'{country} local currency', key=f'currency_{code}')
        if code == 'USA':
            currency = 'USD (selected country)'
        erp = st.number_input('Equity risk premium (%)', 0.0, 50.0, 6.5, 0.1) / 100
        debt = st.slider('Target debt financing (%)', 0, 99, 30) / 100
        st.caption('Debt share is D/(D+E). A 100% debt share is excluded because D/E would be undefined.')
        tax_choice = st.radio('Project corporate tax rate', ['U.S. tax rate', 'Selected-country tax rate'], horizontal=False)

    provenance = []
    missing = []

    def override(label, source_kind, auto, date, key, percent=True, lo=0.0, hi=100.0):
        scale = 100 if percent else 1
        unit = '%' if percent else ''
        manual = st.toggle(f'Override {label}', key=f'override_{key}')
        if auto is None and not manual:
            st.error(f'{label}: no source value available. Enable the override and enter a verified value.')
            missing.append(label)
        if manual:
            value = st.number_input(f'{label} ({unit})' if unit else label, min_value=lo, max_value=hi,
                                    value=float(auto * scale) if auto is not None else None,
                                    step=0.01, format='%.6f', key=f'value_{key}')
            if value is None:
                missing.append(label)
            else:
                value /= scale
            note = st.text_input('Manual source / observation date (optional)', key=f'note_{key}')
            status, used_date, url = 'Manual override', note or 'Not supplied', ''
        else:
            value = auto
            st.caption(f'{label}: {auto * scale:.6f}{unit} · {date}' if auto is not None else 'Unavailable')
            status, used_date, url = sources[source_kind]['status'], date, sources[source_kind]['url']
        provenance.append(dict(input=label, value=value, unit='decimal rate' if percent else 'beta',
                               mode=status, observation_date=used_date, source=url,
                               retrieved_utc=sources[source_kind]['retrieved']))
        return value

    st.subheader('Source values and manual overrides')
    left, right = st.columns(2)
    taxes = sources['taxes']['data']
    tax_code = 'USA' if tax_choice == 'U.S. tax rate' else code
    tax_obs = taxes.get(tax_code, {})
    with left:
        beta = override('Unlevered beta', 'betas', betas[industry], sources['betas']['date'], f'beta_{industry}', False, -10, 20)
        tax = override(f'Project tax rate ({tax_code})', 'taxes', tax_obs.get('value'), tax_obs.get('date', ''), f'tax_{tax_code}')
        spread = override('USD BBB borrowing spread', 'spread', sources['spread']['data'] if isinstance(sources['spread']['data'], (float, int)) else None,
                          sources['spread']['date'], 'spread')
    yields = sources['bonds']['data']
    us = yields.get('United States', {})
    foreign = yields.get(country, {})
    with right:
        us_y = override('U.S. 10-year government yield', 'bonds', us.get('value'), us.get('date', ''), 'us_yield', lo=-99.0)
        foreign_y = override('Selected-country 10-year government yield', 'bonds', foreign.get('value'), foreign.get('date', ''), f'foreign_yield_{code}', lo=-99.0)
        sf_manual = st.toggle('Override foreign-currency BBB spread')
        sf = None
        if us_y is not None and foreign_y is not None and spread is not None:
            auto_sf = spread * (1 + foreign_y) / (1 + us_y)
            if sf_manual:
                sf = st.number_input('Foreign-currency BBB spread (%)', 0.0, 100.0, auto_sf * 100, step=0.01, format='%.6f') / 100
            else:
                st.info(f'Automatic foreign spread: {auto_sf:.4%} ({auto_sf * 10000:.2f} basis points)')
            provenance.append(dict(input='Foreign BBB spread', value=sf if sf_manual else auto_sf, unit='decimal rate',
                                   mode='Manual override' if sf_manual else 'Calculated from USD spread and yield ratio',
                                   observation_date='', source='Class slides 584–585', retrieved_utc=''))
    with st.expander('Data sources, dates and retrieval status', expanded=False):
        st.dataframe(pd.DataFrame(provenance), hide_index=True, width='stretch')
        st.caption('OECD: combined statutory corporate income tax, general government; includes central and subcentral taxes. '
                   'Damodaran: the Unlevered beta column, not the cash-corrected column. '
                   'The borrowing spread is Baa2/BBB for large non-financial firms. '
                   'Refresh clears the one-hour data cache. A failed refresh does not make snapshots current.')
        st.json({k: {n: v for n, v in s.items() if n != 'data'} for k, s in sources.items()})
    if missing:
        st.info('Complete the missing manual inputs above to calculate results. No missing value is treated as zero.')
        st.stop()
    result = calculate(beta, tax, debt, erp, us_y, foreign_y, spread, sf)
    st.subheader('Annual financing costs')
    a, b = st.columns(2)
    for col, suffix, heading in [(a, 'us', 'USD'), (b, 'foreign', currency)]:
        with col:
            st.markdown(f'### {heading}')
            st.metric('WACC', f"{result['wacc_' + suffix]:.4%}")
            st.metric('Cost of equity', f"{result['equity_' + suffix]:.4%}")
            st.metric('Pretax cost of debt', f"{result['debt_' + suffix]:.4%}")
            st.metric('After-tax cost of debt', f"{result['after_tax_' + suffix]:.4%}")
    st.caption(f'Shared project tax: {tax:.4%} · Debt share: {debt:.0%} · ERP: {erp:.2%} · '
               f'Equity beta: {result["beta_e"]:.6f} · Currency factor: {result["factor"]:.6f}')
    if code == 'USA' and not math.isclose(us_y, foreign_y):
        st.warning('The selected country is the U.S., but the manually supplied yields differ. This is a hypothetical scenario.')
    with st.expander('Formulas and assumptions'):
        st.latex(r'\beta_E=\beta_U[1+(1-\tau)d/(1-d)]')
        st.latex(r'R_{e,USD}=R_{f,USD}+\beta_E ERP\qquad R_{d,USD}=R_{f,USD}+s_{USD}')
        st.latex(r'F=\frac{1+R_{f,foreign}}{1+R_{f,USD}},\quad R_{e,foreign}=(1+R_{e,USD})F-1')
        st.latex(r's_{foreign}=s_{USD}F\quad\text{unless overridden},\qquad R_{d,foreign}=R_{f,foreign}+s_{foreign}')
        st.latex(r'WACC_c=(1-d)R_{e,c}+dR_{d,c}(1-\tau)')
        st.write('Government yields are risk-free proxies and can contain sovereign, liquidity and term premia. '
                 'U.S. industry betas proxy for project risk. The model assumes zero debt beta, fully usable immediate '
                 'interest deductions, target market-value debt weights, relative PPP and equal real rates for the currency conversion. '
                 'There is no additional country equity premium or separate currency-risk premium. '
                 'A nominal return in one currency is not directly comparable to a nominal return in another as an investment ranking. '
                 'Compute each currency’s WACC from its equity and after-tax debt costs; do not convert USD WACC directly.')
    inputs = dict(industry=industry, country=country, currency_label=currency, unlevered_beta=beta, tax=tax,
                  debt_share=debt, equity_risk_premium=erp, us_yield=us_y, foreign_yield=foreign_y,
                  usd_spread=spread, foreign_spread_override=sf, tax_basis=tax_choice)
    export = pd.DataFrame([dict(**inputs, **result)])
    st.download_button('Download selected results (CSV)', export.to_csv(index=False), 'selected_results.csv', 'text/csv')
    st.download_button('Download full inputs, results and sources (JSON)',
                       json.dumps(dict(exported_utc=now(), inputs=inputs, results=result, sources=provenance), indent=2),
                       'calculation_audit.json', 'application/json')
    st.subheader('All-industry comparison')
    st.caption('Uses each industry’s source unlevered beta with the same tax, debt share, ERP, yields and spread settings. '
               'The selected industry uses its manual beta if enabled; other industries keep their source betas.')
    rows = []
    for name, source_beta in sorted(betas.items()):
        used_beta = beta if name == industry else source_beta
        r = calculate(used_beta, tax, debt, erp, us_y, foreign_y, spread, sf)
        rows.append(dict(industry=name, unlevered_beta=used_beta, **r, **{k:v for k,v in inputs.items() if k not in ['industry','unlevered_beta']}))
    all_results = pd.DataFrame(rows)
    shown = all_results[['industry', 'unlevered_beta', 'equity_us', 'equity_foreign', 'wacc_us', 'wacc_foreign']].copy()
    for c in ['equity_us', 'equity_foreign', 'wacc_us', 'wacc_foreign']:
        shown[c] = shown[c].map(lambda x: f'{x:.4%}')
    st.dataframe(shown, hide_index=True, width='stretch')
    st.download_button('Download all industries (CSV)', all_results.to_csv(index=False), 'all_industries.csv', 'text/csv')
    st.caption('CSV/JSON rates use decimal form (0.065 = 6.5%). Calculations retain full precision; only displays are rounded.')


if __name__ == '__main__':
    main()
