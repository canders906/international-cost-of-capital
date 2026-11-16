# International Cost of Capital

A Streamlit app for FINC 470 comparing one project's equity cost, debt cost and WACC in USD and a selected country's currency. Uses the formulas in Sergio Rebelo's 2026 class slides 576–587.

## Deploy

1. Create a GitHub repository, for example `international-cost-of-capital`.
2. Upload `app.py`, `requirements.txt`, `packages.txt`, and `README.md` into the repository's root.
3. In Streamlit Community Cloud, create an app from that repository, branch `main`, entry point `app.py`. Use Python 3.12. No secrets or API keys are required.
4. After deployment, inspect source status and dates, click Refresh source data, and check the results. In particular, verify Trading Economics accessibility from the deployed host.

Local run (optional):

```bash
pip install -r requirements.txt
# Install Chromium using your operating system package manager first.
streamlit run app.py
```

## Defaults and controls

- Industry: Software (System & Application).
- Target country: United States; tax basis: U.S. combined statutory corporate tax.
- Equity risk premium: 6.5%; target debt share: 30%.
- Select an industry and country; change ERP and debt financing.
- Switch the shared project tax between U.S. and selected-country rates using the radio buttons.
- Independently override beta, project tax, USD spread and each government yield.
- Override the foreign-currency spread or switch the override off to restore the automatically calculated value.
- View annual equity, pretax debt, after-tax debt and WACC rates side by side.
- Download the current result, an audit JSON with inputs and source dates, or the all-industry CSV.

The beta override affects the selected industry only. The other industries retain their own source betas. All industry calculations share the remaining scenario inputs. Country selection includes ISO countries and territories; some do not have published 10-year bond yields or OECD tax observations. Missing source inputs require explicit manual entry. There is no invented country rate.

## Sources and refresh behavior

| Input | Source | Selection |
|---|---|---|
| Beta | https://pages.stern.nyu.edu/~adamodar/pc/datasets/betas.xls | Industry Averages sheet, **Unlevered beta**, not cash-corrected beta |
| USD spread | https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/ratings.html | Left-hand large non-financial firm table, Baa2/BBB |
| Tax | https://sdmx.oecd.org/public/rest/v1/data/OECD.CTP.TPS,DSD_TAX_CIT@DF_CIT,2.0/.?startPeriod=2000&format=csvfile | CIT_C, ST, S13, annual, percent of taxable income; latest nonfuture year per country |
| Government yields | https://tradingeconomics.com/bonds | Local-currency 10-year government yields from the public page, with normal Chromium rendering when static HTML contains no table |

OECD background: https://www.oecd.org/en/data/datasets/corporate-income-tax-rates-database.html . The supplied 2024 report explains the series, but live retrieval uses the current OECD dataset. Combined statutory rates include central and subcentral taxes; the U.S. rate is therefore not merely its federal rate.

Fetches are cached for one hour. Refresh clears this cache and refetches all four sources. Source observation dates and retrieval times are separate. Live retrieval is attempted on launch. The package embeds verified snapshots for continuity: January 2026 betas and BBB spread; OECD observations retrieved November 16, 2026; and a U.S. yield snapshot of 5.13% dated November 16, 2026 from https://tradingeconomics.com/united-states/government-bond-yield . The snapshots are not represented as live results. Only the U.S. yield is embedded. A fallback shows an explicit warning and its date; other missing yields need manual input. Source-date omissions are identified, not replaced with today's date.

## Build 1.1: browser-rendered yield retrieval

The original implementation directly requested `bonds?partial=markets`, which returned HTTP 405 on the deployed host. Build 1.1 removes that request. It first checks the public `/bonds` HTML. If that does not contain readable yields, it opens the normal `/bonds` page in a fresh Chromium instance, lets the page run its JavaScript, and waits for the U.S. 10-year row. It reads only canonical 10-year rows and keeps the source's displayed timestamps. The parser locates the yield relative to the country cell, including layouts with a separate flag column, rather than assuming a fixed cell number.

`requirements.txt` adds Playwright, and `packages.txt` installs Chromium on Streamlit Community Cloud. Upload both dependency files with the updated app. Reboot the app if the system package is not installed automatically. No API key, credential, spoofed browser identity, proxy, CAPTCHA solving, or verification bypass is used. A browser that encounters human verification or access denial stops and reports the issue. Browser resources are closed after success or failure.

**Verification status:** source parsing, fallback routing, browser lifecycle and challenge handling passed fixture-based tests, and the earlier financial/UI regression checks passed. These tests do not establish live Trading Economics access. This workspace could not launch a local browser; a separate cloud-browser inspection encountered a human-verification challenge. The browser change is therefore a deployment candidate, not a verified end-to-end resolution. It may encounter the same restriction on Streamlit. If it does, do not label the assignment's live-yield requirement complete. Damodaran and OECD live fetches passed in the original build.

To check deployment, confirm the app caption says **Build 1.1**, click **Refresh source data**, and expand **Data sources, dates and retrieval status**. A successful yield fetch must say `Fetched`, show method `Public HTML` or `Chromium-rendered public page`, and have an updated retrieval timestamp. `Saved snapshot` is not success. Select a second country to confirm that its yield was retrieved as well.

## Formulas

All rates are decimals internally and in CSV/JSON exports; display rates are percentages. Calculations retain full precision.

Let `d` be D/(D+E), `t` the one chosen project tax rate, `bU` unlevered beta, `p` ERP, `u` the U.S. government yield, `f` the foreign government yield, and `s` the USD credit spread.

```text
D/E        = d / (1-d)
bE         = bU * (1 + (1-t) * d/(1-d))
Re_USD     = u + bE*p
Rd_USD     = u + s
F          = (1+f)/(1+u)
Re_foreign = (1+Re_USD)*F - 1
s_foreign  = s*F                      [unless manually overridden]
Rd_foreign = f + s_foreign
WACC_c    = (1-d)*Re_c + d*Rd_c*(1-t)
```

Do not convert USD WACC directly with F: the class method computes equity and pretax debt costs first, then applies the interest tax shield in each currency. Changing the foreign credit spread does not change equity costs or any USD result.

The model assumes U.S. industry betas proxy for project risk, zero debt beta, fully usable immediate interest deductions, market-value debt weights, relative PPP and equal real interest rates for currency conversion. Government yields are proxies and can contain sovereign risk and term/liquidity premia. No extra country equity premium or separate currency-risk premium is added. Higher nominal foreign returns do not establish a more attractive investment. Debt share must be below 100% because D/E is undefined at 100% debt.

## Development verification

A separate high-precision Decimal calculation used a **hypothetical Canada scenario**, not the Colombia class example. Inputs below are deliberately illustrative, not current market estimates:

| Input | Value |
|---|---:|
| Unlevered beta | 0.90 |
| Shared project tax | 25% |
| Debt share | 40% |
| ERP | 6.5% |
| U.S. yield | 4% |
| Canadian yield | 3% |
| USD spread | 1.2% |

Independent intermediate arithmetic:

```text
D/E = 0.4/0.6 = 2/3
bE = 0.9 * [1 + 0.75*(2/3)] = 1.35
USD equity = 0.04 + 1.35*0.065 = 0.12775
USD debt = 0.04 + 0.012 = 0.052
USD WACC = 0.6*0.12775 + 0.4*0.052*0.75 = 0.09225
F = 1.03/1.04
CAD equity = 1.12775*1.03/1.04 - 1 = 0.11690625
CAD spread = 0.012*1.03/1.04 = 0.01188461538461538
CAD debt = 0.03 + 0.01188461538461538 = 0.04188461538461538
CAD WACC = 0.6*0.11690625 + 0.4*0.04188461538461538*0.75
         = 0.08270913461538462
```

| Output | USD | CAD |
|---|---:|---:|
| Equity cost | 12.775000% | 11.690625% |
| Pretax debt cost | 5.200000% | 4.188462% |
| After-tax debt cost | 3.900000% | 3.141346% |
| WACC | 9.225000% | 8.270913% |

Calculation results agreed within 1e-12. Equal-yield equality, zero-debt WACC equality with equity cost, and USD independence from foreign-spread overrides passed across a grid of debt/tax inputs. Streamlit's AppTest confirmed the default screen, foreign-country missing-data handling, manual yield entry and USD result independence when changing the foreign spread. These UI tests used source fixtures, so they do not establish live Trading Economics availability.

For the student's required independent verification, reproduce this arithmetic in a calculator or spreadsheet and compare it with the deployed app. Do not represent the AI's development checks alone as the student's own verification. Save your own comparison and an AI-chat screenshot for the submission document.

## Submission checklist

- GitHub repository link.
- Deployed Streamlit app link.
- AI-chat snapshots.
- Your calculator/spreadsheet check and a short explanation of one formula or design choice you checked.
- Confirm data retrieval status and dates on the deployed host; disclose any manual inputs or source restrictions.
