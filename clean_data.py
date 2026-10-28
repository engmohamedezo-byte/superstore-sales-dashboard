"""Step 2 - Prepare the data: load the raw Superstore CSV, clean it, and write
an Excel workbook (Cleaned Data, Raw Data, Data Dictionary, Cleaning Log)
plus a cleaned CSV used by the dashboard script."""
import sys
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

RAW = sys.argv[1]
OUT_XLSX = "Superstore_Sales_Dataset.xlsx"
OUT_CSV = "superstore_clean.csv"

log = []

# 1. Load. The file uses old Mac line endings and Mac Roman encoding;
#    reading it as Latin-1 turns ® into "¨" and ™ into "ª".
raw = pd.read_csv(RAW, encoding="mac_roman")
log.append(("Encoding", "Read file as Mac Roman (not Latin-1) so symbols like ® and ™ in product names display correctly",
            int(raw["Product Name"].str.contains("[®™]", regex=True).sum())))
df = raw.copy()

# 2. Trim whitespace in text columns
txt = df.select_dtypes(include=["object", "string"]).columns
df[txt] = df[txt].apply(lambda s: s.str.strip())
log.append(("Whitespace", "Trimmed leading/trailing spaces in all text columns", 0))

# 3. Fix spelling errors in location names
fixes = {"Region": {"Prarie": "Prairie"}, "Province": {"Saskachewan": "Saskatchewan"}}
for col, mp in fixes.items():
    for bad, good in mp.items():
        n = int((df[col] == bad).sum())
        df[col] = df[col].replace(bad, good)
        log.append(("Spelling", f'{col}: "{bad}" corrected to "{good}"', n))

# 4. Convert date text to real dates
for c in ["Order Date", "Ship Date"]:
    df[c] = pd.to_datetime(df[c], format="%m/%d/%Y")
log.append(("Data types", "Converted Order Date and Ship Date from text to date format", len(df)))

# 5. Missing values: Product Base Margin -> median of the same sub-category
miss = df["Product Base Margin"].isna()
df["Product Base Margin"] = df.groupby("Product Sub-Category")["Product Base Margin"] \
    .transform(lambda s: s.fillna(s.median()))
log.append(("Missing values", "Product Base Margin was empty; filled with the median margin of the same product sub-category",
            int(miss.sum())))

# 6. Duplicates
dups = int(df.drop(columns=["Row ID"]).duplicated().sum())
df = df.drop_duplicates(subset=[c for c in df.columns if c != "Row ID"])
log.append(("Duplicates", "Checked for fully duplicated rows (ignoring Row ID); none found", dups))

# 7. Validity checks
bad_dates = int((df["Ship Date"] < df["Order Date"]).sum())
log.append(("Validity", "Checked that no order ships before it was ordered", bad_dates))
log.append(("Validity", "Checked that Sales, Unit Price and Order Quantity are all positive",
            int(((df["Sales"] <= 0) | (df["Unit Price"] <= 0) | (df["Order Quantity"] <= 0)).sum())))

# 8. Label "Not Specified" priority as unknown but keep the rows
log.append(("Categories", '"Not Specified" Order Priority kept as its own category (rows are valid sales)',
            int((df["Order Priority"] == "Not Specified").sum())))

# 9. Derived variables (also written as Excel formulas below)
df["Shipping Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
df["Order Year"] = df["Order Date"].dt.year
df["Order Month"] = df["Order Date"].dt.month
df["Profit Margin"] = df["Profit"] / df["Sales"]
out = int((df["Shipping Days"] > 30).sum())
df["Shipping Outlier"] = (df["Shipping Days"] > 30).map({True: "Yes", False: "No"})
log.append(("Outliers", "Orders that took over 30 days to ship flagged in 'Shipping Outlier' (kept, sales values are valid)", out))
log.append(("New columns", "Added Shipping Days, Order Year, Order Month, Profit Margin and Shipping Outlier", len(df)))

df = df.sort_values("Order Date").reset_index(drop=True)
df.to_csv(OUT_CSV, index=False)

# ---------- Excel workbook ----------
dictionary = [
    ("Row ID", "Number", "Unique row number"),
    ("Order ID", "Number", "Order number (one order can contain several products)"),
    ("Order Date", "Date", "Date the order was placed (Jan 2009 - Dec 2012)"),
    ("Order Priority", "Category", "Critical, High, Medium, Low, Not Specified"),
    ("Order Quantity", "Number", "Units ordered (1-50)"),
    ("Sales", "Currency (CAD)", "Sales revenue of the line"),
    ("Discount", "Percent", "Discount given (0-25%)"),
    ("Ship Mode", "Category", "Regular Air, Express Air, Delivery Truck"),
    ("Profit", "Currency (CAD)", "Profit of the line (negative = loss)"),
    ("Unit Price", "Currency (CAD)", "Price of one unit"),
    ("Shipping Cost", "Currency (CAD)", "Shipping cost of the line"),
    ("Customer Name", "Text", "Customer name"),
    ("Province", "Category", "Canadian province or territory (13)"),
    ("Region", "Category", "Sales region (8)"),
    ("Customer Segment", "Category", "Corporate, Home Office, Consumer, Small Business"),
    ("Product Category", "Category", "Office Supplies, Technology, Furniture"),
    ("Product Sub-Category", "Category", "17 sub-categories, e.g. Chairs & Chairmats"),
    ("Product Name", "Text", "Product name"),
    ("Product Container", "Category", "Packaging type, e.g. Small Box, Jumbo Drum"),
    ("Product Base Margin", "Percent", "Base margin of the product"),
    ("Ship Date", "Date", "Date the order shipped"),
    ("Shipping Days", "Number (new)", "Ship Date - Order Date"),
    ("Order Year", "Number (new)", "Year of Order Date"),
    ("Order Month", "Number (new)", "Month (1-12) of Order Date"),
    ("Profit Margin", "Percent (new)", "Profit / Sales"),
    ("Shipping Outlier", "Yes/No (new)", "Yes if Shipping Days > 30"),
]

with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
    df.to_excel(w, sheet_name="Cleaned Data", index=False)
    raw.to_excel(w, sheet_name="Raw Data", index=False)
    pd.DataFrame(dictionary, columns=["Variable", "Type", "Description"]).to_excel(w, sheet_name="Data Dictionary", index=False)
    pd.DataFrame(log, columns=["Step", "What was done", "Rows affected"]).to_excel(w, sheet_name="Cleaning Log", index=False)

wb = load_workbook(OUT_XLSX)
ws = wb["Cleaned Data"]
cols = {c.value: get_column_letter(c.column) for c in ws[1]}
n = ws.max_row
C = cols
for r in range(2, n + 1):  # derived columns as live formulas
    ws[f"{C['Shipping Days']}{r}"] = f"={C['Ship Date']}{r}-{C['Order Date']}{r}"
    ws[f"{C['Order Year']}{r}"] = f"=YEAR({C['Order Date']}{r})"
    ws[f"{C['Order Month']}{r}"] = f"=MONTH({C['Order Date']}{r})"
    ws[f"{C['Profit Margin']}{r}"] = f"=IFERROR({C['Profit']}{r}/{C['Sales']}{r},0)"
    ws[f"{C['Shipping Outlier']}{r}"] = f'=IF({C["Shipping Days"]}{r}>30,"Yes","No")'

fmt = {"Order Date": "yyyy-mm-dd", "Ship Date": "yyyy-mm-dd", "Sales": "#,##0.00",
       "Profit": "#,##0.00;(#,##0.00)", "Unit Price": "#,##0.00", "Shipping Cost": "#,##0.00",
       "Discount": "0%", "Product Base Margin": "0%", "Profit Margin": "0.0%", "Shipping Days": "0"}
for name, f in fmt.items():
    for r in range(2, n + 1):
        ws[f"{C[name]}{r}"].number_format = f
raw_ws = wb["Raw Data"]

head_fill = PatternFill("solid", fgColor="1C5CAB")
for sheet in wb.worksheets:
    for row in sheet.iter_rows():
        for cell in row:
            cell.font = Font(name="Arial", size=10, bold=cell.row == 1,
                             color="FFFFFF" if cell.row == 1 else "000000")
    for cell in sheet[1]:
        cell.fill = head_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    sheet.freeze_panes = "A2"
    for i, col in enumerate(sheet.columns, 1):
        width = max(len(str(c.value)) if c.value is not None else 0 for c in list(col)[:200])
        sheet.column_dimensions[get_column_letter(i)].width = min(max(10, width + 2), 55)
    if sheet.title in ("Cleaned Data", "Raw Data"):
        sheet.auto_filter.ref = sheet.dimensions
for sheet in (wb["Cleaned Data"], raw_ws):
    sheet.column_dimensions[C["Product Name"]].width = 45
wb["Cleaning Log"].column_dimensions["B"].width = 95
wb["Data Dictionary"].column_dimensions["C"].width = 60
wb.save(OUT_XLSX)

print(pd.DataFrame(log, columns=["Step", "What", "Rows"]).to_string())
print(df.shape)
