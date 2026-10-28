"""Step 3 - Build the Superstore Sales Performance dashboard (PNG + PDF)."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter

d = pd.read_csv("superstore_clean.csv", parse_dates=["Order Date", "Ship Date"])

# ---- palette (validated) ----
SURF, PAGE = "#fcfcfb", "#f4f4f1"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, YELLOW, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e34948"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlesize": 11.5,
    "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left",
    "axes.titlepad": 10, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2, "axes.facecolor": SURF,
    "legend.frameon": False, "legend.fontsize": 8.5,
})

def money(x, _=None):
    a = abs(x)
    s = f"${a/1e6:.1f}M" if a >= 1e6 else (f"${a/1e3:.0f}K" if a >= 1e3 else f"${a:.0f}")
    return "-" + s if x < 0 else s

def clean_axes(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left" if grid_axis == "x" else "left"].set_visible(grid_axis == "x")
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)

fig = plt.figure(figsize=(20, 13.5), facecolor=PAGE)
gs = GridSpec(4, 3, figure=fig, height_ratios=[0.55, 2.1, 2.1, 2.1],
              hspace=0.62, wspace=0.42, width_ratios=[1, 1, 1.12], left=0.045, right=0.975, top=0.885, bottom=0.05)

# ---- header ----
fig.text(0.045, 0.955, "Superstore Sales Performance Dashboard", fontsize=24, fontweight="bold", color=INK)
fig.text(0.045, 0.925, "Canadian office-supplies retailer  ·  8,399 order lines  ·  Jan 2009 – Dec 2012  ·  all values in CAD",
         fontsize=11.5, color=INK2)

# ---- KPI tiles ----
S, P = d.Sales.sum(), d.Profit.sum()
kpis = [("Total Sales", money(S)), ("Total Profit", money(P)), ("Profit Margin", f"{P/S:.1%}"),
        ("Orders", f"{d['Order ID'].nunique():,}"), ("Customers", f"{d['Customer Name'].nunique():,}")]
kgs = gs[0, :].subgridspec(1, 5, wspace=0.08)
for i, (lab, val) in enumerate(kpis):
    ax = fig.add_subplot(kgs[0, i]); ax.set_xticks([]); ax.set_yticks([])
    ax.set_facecolor(SURF)
    for s in ax.spines.values():
        s.set_color("#e1e0d9")
    ax.text(0.06, 0.70, lab, fontsize=10.5, color=INK2, transform=ax.transAxes, va="center")
    ax.text(0.06, 0.30, val, fontsize=21, fontweight="bold", color=INK, transform=ax.transAxes, va="center")

# ---- 1. Line: monthly sales trend ----
ax = fig.add_subplot(gs[1, 0:2]); clean_axes(ax)
m = d.set_index("Order Date").resample("MS").Sales.sum()
roll = m.rolling(12).mean()
ax.plot(m.index, m.values, color=BLUE, lw=2, label="Monthly sales")
ax.plot(roll.index, roll.values, color=INK2, lw=2, ls=(0, (4, 3)), label="12-month moving average")
ax.scatter([m.idxmax(), m.idxmin()], [m.max(), m.min()], s=40, color=BLUE, edgecolor=SURF, lw=2, zorder=5)
ax.annotate(f"Peak: {m.idxmax():%b %Y}\n{money(m.max())}", (m.idxmax(), m.max()), xytext=(12, -8),
            textcoords="offset points", fontsize=8.5, color=INK2, va="top")
ax.annotate(f"Low: {m.idxmin():%b %Y}  {money(m.min())}", (m.idxmin(), m.min()), xytext=(0, -16),
            textcoords="offset points", fontsize=8.5, color=INK2, ha="center")
yr = d.groupby("Order Year").Sales.sum()
for y, v in yr.items():
    ax.text(pd.Timestamp(f"{y}-07-01"), 1.0, f"{y}: {money(v)}", transform=ax.get_xaxis_transform(),
            ha="center", va="bottom", fontsize=9, color=INK2, fontweight="bold")
for y in (2010, 2011, 2012):
    ax.axvline(pd.Timestamp(f"{y}-01-01"), color=GRID, lw=1, zorder=0)
ax.yaxis.set_major_formatter(FuncFormatter(money)); ax.set_ylim(0, 620000)
ax.set_ylabel("Sales (CAD)"); ax.set_xlabel("Order month")
ax.set_title("1. Monthly Sales Trend, 2009–2012", pad=24)
ax.legend(loc="upper right", ncol=2, bbox_to_anchor=(1, 0.99))

# ---- 2. Donut: sales share by customer segment ----
ax = fig.add_subplot(gs[1, 2])
seg = d.groupby("Customer Segment").Sales.sum().sort_values(ascending=False)
cols = [BLUE, ORANGE, AQUA, YELLOW]
w, _ = ax.pie(seg.values, colors=cols, startangle=90, counterclock=False,
              wedgeprops=dict(width=0.38, edgecolor=SURF, linewidth=2.5))
ax.text(0, 0.08, money(S), ha="center", fontsize=15, fontweight="bold")
ax.text(0, -0.15, "total sales", ha="center", fontsize=9, color=INK2)
ax.legend(w, [f"{k}  {v/S:.1%}  ({money(v)})" for k, v in seg.items()], loc="center left",
          bbox_to_anchor=(0.93, 0.5), title="Customer segment", title_fontsize=9, alignment="left")
ax.set_title("2. Sales Share by Customer Segment", x=0.0)
ax.set_anchor("W")

# ---- 3. Grouped bar: sales vs profit by category ----
ax = fig.add_subplot(gs[2, 0]); clean_axes(ax)
cat = d.groupby("Product Category")[["Sales", "Profit"]].sum().sort_values("Sales", ascending=False)
x = range(len(cat)); bw = 0.36
b1 = ax.bar([i - bw/2 - 0.01 for i in x], cat.Sales, bw, color=BLUE, label="Sales")
b2 = ax.bar([i + bw/2 + 0.01 for i in x], cat.Profit, bw, color=ORANGE, label="Profit")
for i, (s_, p_) in enumerate(zip(cat.Sales, cat.Profit)):
    ax.text(i - bw/2 - 0.01, s_, money(s_), ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.text(i + bw/2 + 0.01, p_, money(p_), ha="center", va="bottom", fontsize=8.5, color=INK2)
ax.set_xticks(list(x)); ax.set_xticklabels([f"{k}\n{r.Profit/r.Sales:.1%} margin" for k, r in cat.iterrows()])
ax.yaxis.set_major_formatter(FuncFormatter(money)); ax.set_ylim(0, 7.2e6)
ax.set_ylabel("CAD"); ax.legend(loc="upper right")
ax.set_title("3. Sales vs Profit by Product Category")

# ---- 4. Horizontal bar: sales by region ----
ax = fig.add_subplot(gs[2, 1]); clean_axes(ax, "x")
reg = d.groupby("Region").Sales.sum().sort_values()
ax.barh(reg.index, reg.values, color=BLUE, height=0.62)
for i, v in enumerate(reg.values):
    ax.text(v + 4e4, i, f"{money(v)}  ({v/S:.0%})", va="center", fontsize=8.5, color=INK2)
ax.xaxis.set_major_formatter(FuncFormatter(money)); ax.set_xlim(0, 4.6e6)
ax.set_xlabel("Sales (CAD)")
ax.set_title("4. Sales by Region")

# ---- 5. Diverging bar: profit by sub-category ----
ax = fig.add_subplot(gs[2:, 2]); clean_axes(ax, "x")
sub = d.groupby("Product Sub-Category").Profit.sum().sort_values()
sub = sub.rename(index={"Telephones and Communication": "Telephones & Communication",
                        "Binders and Binder Accessories": "Binders & Accessories",
                        "Scissors, Rulers and Trimmers": "Scissors, Rulers & Trimmers",
                        "Copiers and Fax": "Copiers & Fax"})
ax.barh(sub.index, sub.values, color=[RED if v < 0 else BLUE for v in sub.values], height=0.64)
ax.axvline(0, color=AXIS, lw=1)
for i, v in enumerate(sub.values):
    ax.text(v + (6e3 if v >= 0 else -6e3), i, money(v), va="center", ha="left" if v >= 0 else "right",
            fontsize=8.3, color=INK2)
ax.xaxis.set_major_formatter(FuncFormatter(money)); ax.set_xlim(-1.65e5, 3.9e5)
ax.set_xlabel("Profit (CAD)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=BLUE, label="Profit"), Patch(color=RED, label="Loss")], loc="lower right")
ax.set_title("5. Total Profit by Product Sub-Category")

# ---- 6. Bar: profit margin by discount level ----
ax = fig.add_subplot(gs[3, 0]); clean_axes(ax)
d["Discount Band"] = pd.cut(d.Discount, [-0.01, 0.03, 0.06, 0.09, 0.25], labels=["0–3%", "4–6%", "7–9%", "10–25%"])
db = d.groupby("Discount Band", observed=True).agg(S=("Sales", "sum"), P=("Profit", "sum"), n=("Sales", "size"))
mg = db.P / db.S
ax.bar(range(len(mg)), mg.values, color=BLUE, width=0.55)
for i, (v, n) in enumerate(zip(mg.values, db.n)):
    ax.text(i, v + 0.003, f"{v:.1%}", ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=INK)
    ax.text(i, 0.004, f"{n:,} lines", ha="center", va="bottom", fontsize=8, color="#ffffff")
ax.set_xticks(range(len(mg))); ax.set_xticklabels(mg.index)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}")); ax.set_ylim(0, 0.16)
ax.set_xlabel("Discount given"); ax.set_ylabel("Profit margin")
ax.set_title("6. Profit Margin by Discount Level")

# ---- 7. Table: yearly summary ----
ax = fig.add_subplot(gs[3, 1]); ax.axis("off")
ys = d.groupby("Order Year").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                                 Orders=("Order ID", "nunique"), Ship=("Shipping Days", "mean"))
ys["Margin"] = ys.Profit / ys.Sales
ys["Growth"] = ys.Sales.pct_change()
rows = [[str(y), f"${r.Sales:,.0f}", f"${r.Profit:,.0f}", f"{r.Margin:.1%}",
         "—" if pd.isna(r.Growth) else f"{r.Growth:+.1%}", f"{int(r.Orders):,}"] for y, r in ys.iterrows()]
rows.append(["Total", f"${S:,.0f}", f"${P:,.0f}", f"{P/S:.1%}", "", f"{d['Order ID'].nunique():,}"])
hdr = ["Year", "Sales", "Profit", "Margin", "Growth", "Orders"]
t = ax.table(cellText=rows, colLabels=hdr, loc="upper center", cellLoc="right", colLoc="right",
             colWidths=[0.12, 0.22, 0.2, 0.14, 0.16, 0.14], bbox=[0, 0.02, 1, 0.9])
t.auto_set_font_size(False); t.set_fontsize(9.5)
for (r, c), cell in t.get_celld().items():
    cell.set_edgecolor(GRID); cell.set_linewidth(0.8)
    cell.visible_edges = "B"
    if c == 0:
        cell.set_text_props(ha="left"); cell._loc = "left"
    if r == 0:
        cell.set_text_props(fontweight="bold", color=INK2); cell.set_facecolor(SURF)
    elif r == len(rows):
        cell.set_text_props(fontweight="bold"); cell.set_facecolor("#eef4fc")
    else:
        cell.set_facecolor(SURF)
ax.set_title("7. Yearly Performance Summary")

fig.text(0.975, 0.012, "Data: Superstore Sales sample dataset (Canada), cleaned in Python. Profit margin = Profit ÷ Sales.",
         ha="right", fontsize=8.5, color=MUTED)

import os
if os.environ.get("APPX") == "1":
    fig.text(0.975, 0.962, "Appendix A \u2013 Full-page dashboard", ha="right", fontsize=11, color=MUTED)
    fig.savefig("dashboard_appendixA.pdf", facecolor=PAGE)
else:
    fig.savefig("Superstore_Dashboard.png", dpi=170, facecolor=PAGE)
    fig.savefig("Superstore_Dashboard.pdf", facecolor=PAGE)
print("saved")
