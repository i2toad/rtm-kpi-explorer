# streamlit_app.py
# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")
# DATA_FOLDER = Path("./data")  # put your excel files in ./data or change this path
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     # returns dict sheet_name -> dataframe
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         # small cleanup: ensure index reset
#         for k,v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error":[str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     # attempt to convert common KPI columns to numeric
#     for c in df.columns:
#         if df[c].dtype == object:
#             # try to coerce if many numeric-like values
#             coerced = pd.to_numeric(df[c].astype(str).str.replace(",","").str.replace("₦","").str.strip(), errors="coerce")
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# # ---------- UI ----------
# st.title("MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # File discovery
# st.sidebar.header("Data source")
# st.sidebar.write("Place Excel files in:", f"`{DATA_FOLDER.resolve()}`")
# if not DATA_FOLDER.exists():
#     st.sidebar.error("Data folder not found. Create the folder and add your Excel files.")
# files = list_excel_files(DATA_FOLDER)

# if not files:
#     st.warning("No Excel files found in the data folder. Add `.xlsx` files and reload.")
#     st.stop()

# # File selector
# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # Load sheets
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0,0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# # Quick data clean
# df = safe_numeric_cols(df)

# # Display dataframe
# st.subheader(f"{selected_file_name} — {selected_sheet}")
# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns")
#     cols = df.columns.tolist()
#     st.write(cols)
#     st.write("Basic stats for numeric columns")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # Lightweight pivot / chart builder
# st.markdown("---")
# st.subheader("Quick Chart / Pivot")

# col1, col2 = st.columns([2,1])

# with col2:
#     x_axis = st.selectbox("X axis (categorical / datetime)", ["<none>"] + df.columns.tolist())
#     y_axis = st.selectbox("Y axis (numeric)", ["<none>"] + df.columns.tolist())
#     agg_func = st.selectbox("Aggregation", ["sum", "mean", "median", "count"])
#     chart_type = st.selectbox("Chart type", ["line (time series)", "bar", "table"])
#     apply_filter = st.checkbox("Apply simple filter (column equals value)")
#     filter_col, filter_val = None, None
#     if apply_filter:
#         filter_col = st.selectbox("Filter column", df.columns.tolist())
#         # show unique values (first 100)
#         unique_vals = df[filter_col].dropna().astype(str).unique().tolist()[:200]
#         filter_val = st.selectbox("Filter value", ["<all>"] + unique_vals)

# with col1:
#     if x_axis == "<none>" or y_axis == "<none>":
#         st.info("Select X and Y to build a chart or select 'table' to view a pivot.")
#     else:
#         chart_df = df.copy()
#         if apply_filter and filter_val and filter_val != "<all>":
#             chart_df = chart_df[chart_df[filter_col].astype(str) == filter_val]
#         # if x is datetime-like try to parse
#         try:
#             if pd.api.types.is_datetime64_any_dtype(chart_df[x_axis]):
#                 chart_df[x_axis] = pd.to_datetime(chart_df[x_axis])
#         except Exception:
#             pass

#         # aggregate
#         if agg_func == "sum":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].sum().reset_index()
#         elif agg_func == "mean":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].mean().reset_index()
#         elif agg_func == "median":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].median().reset_index()
#         else:
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].count().reset_index().rename(columns={y_axis:"count"})

#         # show table
#         if chart_type == "table":
#             st.dataframe(agg_df, use_container_width=True)
#         else:
#             if chart_type.startswith("line"):
#                 fig = px.line(agg_df, x=x_axis, y=agg_df.columns[1], markers=True, title=f"{chart_type} of {y_axis} by {x_axis}")
#             else:
#                 fig = px.bar(agg_df, x=x_axis, y=agg_df.columns[1], title=f"{chart_type} of {y_axis} by {x_axis}")
#             st.plotly_chart(fig, use_container_width=True)

# # Download current sheet / pivot
# st.markdown("---")
# st.subheader("Export / Download")
# download_df = st.checkbox("Download current sheet (as CSV)")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(label="Download CSV", data=b, file_name=f"{selected_file_name}_{selected_sheet}.csv", mime="text/csv")

# # Show raw file list and option to upload a new file
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size//1024} KB)")
# st.sidebar.markdown("Add more Excel files to the folder and rerun the app.")

# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app generated by ChatGPT — modify as needed.")



##############################################################################################


# streamlit_app.py
# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# # ✅ Updated data folder path to your Excel location
# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data")
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k,v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error":[str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(df[c].astype(str).str.replace(",","").str.replace("₦","").str.strip(), errors="coerce")
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# # ---------- UI ----------
# st.title("MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # File discovery
# st.sidebar.header("Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# # File selector
# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # Load sheets
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0,0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# df = safe_numeric_cols(df)

# # Display dataframe
# st.subheader(f"{selected_file_name} — {selected_sheet}")
# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # Chart builder
# st.markdown("---")
# st.subheader("Quick Chart / Pivot")

# col1, col2 = st.columns([2,1])
# with col2:
#     x_axis = st.selectbox("X axis (categorical / datetime)", ["<none>"] + df.columns.tolist())
#     y_axis = st.selectbox("Y axis (numeric)", ["<none>"] + df.columns.tolist())
#     agg_func = st.selectbox("Aggregation", ["sum", "mean", "median", "count"])
#     chart_type = st.selectbox("Chart type", ["line (time series)", "bar", "table"])
#     apply_filter = st.checkbox("Apply simple filter (column equals value)")
#     if apply_filter:
#         filter_col = st.selectbox("Filter column", df.columns.tolist())
#         unique_vals = df[filter_col].dropna().astype(str).unique().tolist()[:200]
#         filter_val = st.selectbox("Filter value", ["<all>"] + unique_vals)
#     else:
#         filter_col, filter_val = None, None

# with col1:
#     if x_axis == "<none>" or y_axis == "<none>":
#         st.info("Select X and Y to build a chart or select 'table' to view a pivot.")
#     else:
#         chart_df = df.copy()
#         if apply_filter and filter_val and filter_val != "<all>":
#             chart_df = chart_df[chart_df[filter_col].astype(str) == filter_val]

#         try:
#             if pd.api.types.is_datetime64_any_dtype(chart_df[x_axis]):
#                 chart_df[x_axis] = pd.to_datetime(chart_df[x_axis])
#         except Exception:
#             pass

#         # Aggregate
#         if agg_func == "sum":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].sum().reset_index()
#         elif agg_func == "mean":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].mean().reset_index()
#         elif agg_func == "median":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].median().reset_index()
#         else:
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].count().reset_index().rename(columns={y_axis:"count"})

#         # Show chart or table
#         if chart_type == "table":
#             st.dataframe(agg_df, use_container_width=True)
#         else:
#             if chart_type.startswith("line"):
#                 fig = px.line(agg_df, x=x_axis, y=agg_df.columns[1], markers=True, title=f"{chart_type} of {y_axis} by {x_axis}")
#             else:
#                 fig = px.bar(agg_df, x=x_axis, y=agg_df.columns[1], title=f"{chart_type} of {y_axis} by {x_axis}")
#             st.plotly_chart(fig, use_container_width=True)

# # Download option
# st.markdown("---")
# st.subheader("Export / Download")
# download_df = st.checkbox("Download current sheet (as CSV)")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(label="Download CSV", data=b, file_name=f"{selected_file_name}_{selected_sheet}.csv", mime="text/csv")

# # Sidebar info
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size//1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))




############################################################################





# streamlit_app.py
# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data")  # ✅ change if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# # File selector
# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # Load sheets
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# df = safe_numeric_cols(df)
# df.columns = df.columns.astype(str).str.strip()

# # ---------- AUTO-DETECT MONTH COLUMNS ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None

# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()

# # ---------- HEADER FILTERS ----------
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")
#     filter_values = {}
#     cols = st.columns(len(filter_columns))

#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             unique_vals = df[col].dropna().astype(str).unique().tolist()
#             unique_vals.sort()
#             options = ["All"] + unique_vals
#             default_val = "All"
#             filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

#     # Apply filters dynamically
#     for col, val in filter_values.items():
#         if val != "All":
#             df = df[df[col].astype(str) == val]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ---------- DISPLAY ----------
# st.subheader(f"{selected_file_name} — {selected_sheet}")
# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # ---------- CHART BUILDER ----------
# st.markdown("---")
# st.subheader("📈 Quick Chart / Pivot")

# col1, col2 = st.columns([2, 1])
# with col2:
#     x_axis = st.selectbox("X axis (categorical / datetime)", ["<none>"] + df.columns.tolist())
#     y_axis = st.selectbox("Y axis (numeric)", ["<none>"] + df.columns.tolist())
#     agg_func = st.selectbox("Aggregation", ["sum", "mean", "median", "count"])
#     chart_type = st.selectbox("Chart type", ["line (time series)", "bar", "table"])
#     apply_filter = st.checkbox("Apply simple filter (column equals value)")
#     if apply_filter:
#         filter_col = st.selectbox("Filter column", df.columns.tolist())
#         unique_vals = df[filter_col].dropna().astype(str).unique().tolist()[:200]
#         filter_val = st.selectbox("Filter value", ["<all>"] + unique_vals)
#     else:
#         filter_col, filter_val = None, None

# with col1:
#     if x_axis == "<none>" or y_axis == "<none>":
#         st.info("Select X and Y to build a chart or select 'table' to view a pivot.")
#     else:
#         chart_df = df.copy()
#         if apply_filter and filter_val and filter_val != "<all>":
#             chart_df = chart_df[chart_df[filter_col].astype(str) == filter_val]

#         try:
#             if pd.api.types.is_datetime64_any_dtype(chart_df[x_axis]):
#                 chart_df[x_axis] = pd.to_datetime(chart_df[x_axis])
#         except Exception:
#             pass

#         # Aggregate
#         if agg_func == "sum":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].sum().reset_index()
#         elif agg_func == "mean":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].mean().reset_index()
#         elif agg_func == "median":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].median().reset_index()
#         else:
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].count().reset_index().rename(columns={y_axis: "count"})

#         # Display
#         if chart_type == "table":
#             st.dataframe(agg_df, use_container_width=True)
#         else:
#             if chart_type.startswith("line"):
#                 fig = px.line(agg_df, x=x_axis, y=agg_df.columns[1], markers=True, title=f"{y_axis} by {x_axis}")
#             else:
#                 fig = px.bar(agg_df, x=x_axis, y=agg_df.columns[1], title=f"{y_axis} by {x_axis}")
#             st.plotly_chart(fig, use_container_width=True)

# # ---------- DOWNLOAD ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))



###################################################################


# streamlit_app.py
# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data")  # ✅ change if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # ---------- LOAD SHEETS ----------
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# df = safe_numeric_cols(df)
# df.columns = df.columns.astype(str).str.strip()

# # ---------- DETECT MONTH COLUMNS ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None
# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()

# # ---------- HEADER FILTERS ----------
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")
#     filter_values = {}

#     # Normalize for matching Region and Area columns
#     normalized_cols = {c.lower(): c for c in filter_columns}
#     region_col = normalized_cols.get("region")
#     area_col = normalized_cols.get("area")

#     cols = st.columns(len(filter_columns))
#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             if col == area_col and region_col and region_col in df.columns:
#                 # Dependent AREA filter — filter Areas based on selected Region
#                 selected_region = filter_values.get(region_col, "All")
#                 if selected_region and selected_region != "All":
#                     valid_areas = (
#                         df[df[region_col].astype(str) == selected_region][area_col]
#                         .dropna()
#                         .astype(str)
#                         .unique()
#                         .tolist()
#                     )
#                 else:
#                     valid_areas = df[area_col].dropna().astype(str).unique().tolist()

#                 valid_areas.sort()
#                 options = ["All"] + valid_areas
#                 filter_values[col] = st.selectbox("Area", options, index=0, key=f"filter_{col}")
#             else:
#                 # Normal filter
#                 unique_vals = df[col].dropna().astype(str).unique().tolist()
#                 unique_vals.sort()
#                 options = ["All"] + unique_vals
#                 filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

#     # Apply filters in order
#     for col, val in filter_values.items():
#         if val != "All":
#             df = df[df[col].astype(str) == val]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ---------- DISPLAY ----------
# st.subheader(f"{selected_file_name} — {selected_sheet}")
# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # ---------- CHART BUILDER ----------
# st.markdown("---")
# st.subheader("📈 Quick Chart / Pivot")

# col1, col2 = st.columns([2, 1])
# with col2:
#     x_axis = st.selectbox("X axis (categorical / datetime)", ["<none>"] + df.columns.tolist())
#     y_axis = st.selectbox("Y axis (numeric)", ["<none>"] + df.columns.tolist())
#     agg_func = st.selectbox("Aggregation", ["sum", "mean", "median", "count"])
#     chart_type = st.selectbox("Chart type", ["line (time series)", "bar", "table"])
#     apply_filter = st.checkbox("Apply simple filter (column equals value)")
#     if apply_filter:
#         filter_col = st.selectbox("Filter column", df.columns.tolist())
#         unique_vals = df[filter_col].dropna().astype(str).unique().tolist()[:200]
#         filter_val = st.selectbox("Filter value", ["<all>"] + unique_vals)
#     else:
#         filter_col, filter_val = None, None

# with col1:
#     if x_axis == "<none>" or y_axis == "<none>":
#         st.info("Select X and Y to build a chart or select 'table' to view a pivot.")
#     else:
#         chart_df = df.copy()
#         if apply_filter and filter_val and filter_val != "<all>":
#             chart_df = chart_df[chart_df[filter_col].astype(str) == filter_val]

#         try:
#             if pd.api.types.is_datetime64_any_dtype(chart_df[x_axis]):
#                 chart_df[x_axis] = pd.to_datetime(chart_df[x_axis])
#         except Exception:
#             pass

#         # Aggregate
#         if agg_func == "sum":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].sum().reset_index()
#         elif agg_func == "mean":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].mean().reset_index()
#         elif agg_func == "median":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].median().reset_index()
#         else:
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].count().reset_index().rename(columns={y_axis: "count"})

#         if chart_type == "table":
#             st.dataframe(agg_df, use_container_width=True)
#         else:
#             if chart_type.startswith("line"):
#                 fig = px.line(agg_df, x=x_axis, y=agg_df.columns[1], markers=True, title=f"{y_axis} by {x_axis}")
#             else:
#                 fig = px.bar(agg_df, x=x_axis, y=agg_df.columns[1], title=f"{y_axis} by {x_axis}")
#             st.plotly_chart(fig, use_container_width=True)

# # ---------- DOWNLOAD ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))



########################################################################




# streamlit_app.py
# import streamlit as st
# import pandas as pd
# from pathlib import Path
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data")  # ✅ Adjust if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # ---------- LOAD SHEETS ----------
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# df = safe_numeric_cols(df)
# df.columns = df.columns.astype(str).str.strip()

# # ---------- DETECT MONTH COLUMNS ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None
# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()

# # ---------- HEADER FILTERS ----------
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")
#     filter_values = {}

#     # Normalize names
#     normalized_cols = {c.lower(): c for c in filter_columns}
#     region_col = normalized_cols.get("region")
#     area_col = normalized_cols.get("area")

#     cols = st.columns(len(filter_columns))

#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             if col == area_col and region_col and region_col in df.columns:
#                 # Cascading Area filter (depends on Region)
#                 selected_regions = filter_values.get(region_col, ["All"])
#                 if "All" not in selected_regions:
#                     valid_areas = (
#                         df[df[region_col].astype(str).isin(selected_regions)][area_col]
#                         .dropna()
#                         .astype(str)
#                         .unique()
#                         .tolist()
#                     )
#                 else:
#                     valid_areas = df[area_col].dropna().astype(str).unique().tolist()
#                 valid_areas.sort()
#                 options = ["All"] + valid_areas
#                 filter_values[col] = st.multiselect("Area", options, default=["All"], key=f"filter_{col}")
#             else:
#                 # Regular multi-select
#                 unique_vals = df[col].dropna().astype(str).unique().tolist()
#                 unique_vals.sort()
#                 options = ["All"] + unique_vals
#                 filter_values[col] = st.multiselect(col, options, default=["All"], key=f"filter_{col}")

#     # Apply filters
#     for col, selected_vals in filter_values.items():
#         if "All" not in selected_vals:
#             df = df[df[col].astype(str).isin(selected_vals)]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ---------- DISPLAY ----------
# st.subheader(f"{selected_file_name} — {selected_sheet}")
# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # ---------- CHART BUILDER ----------
# st.markdown("---")
# st.subheader("📈 Quick Chart / Pivot")

# col1, col2 = st.columns([2, 1])
# with col2:
#     x_axis = st.selectbox("X axis (categorical / datetime)", ["<none>"] + df.columns.tolist())
#     y_axis = st.selectbox("Y axis (numeric)", ["<none>"] + df.columns.tolist())
#     agg_func = st.selectbox("Aggregation", ["sum", "mean", "median", "count"])
#     chart_type = st.selectbox("Chart type", ["line (time series)", "bar", "table"])
#     apply_filter = st.checkbox("Apply simple filter (column equals value)")
#     if apply_filter:
#         filter_col = st.selectbox("Filter column", df.columns.tolist())
#         unique_vals = df[filter_col].dropna().astype(str).unique().tolist()[:200]
#         filter_val = st.selectbox("Filter value", ["<all>"] + unique_vals)
#     else:
#         filter_col, filter_val = None, None

# with col1:
#     if x_axis == "<none>" or y_axis == "<none>":
#         st.info("Select X and Y to build a chart or select 'table' to view a pivot.")
#     else:
#         chart_df = df.copy()
#         if apply_filter and filter_val and filter_val != "<all>":
#             chart_df = chart_df[chart_df[filter_col].astype(str) == filter_val]

#         try:
#             if pd.api.types.is_datetime64_any_dtype(chart_df[x_axis]):
#                 chart_df[x_axis] = pd.to_datetime(chart_df[x_axis])
#         except Exception:
#             pass

#         # Aggregate
#         if agg_func == "sum":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].sum().reset_index()
#         elif agg_func == "mean":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].mean().reset_index()
#         elif agg_func == "median":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].median().reset_index()
#         else:
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].count().reset_index().rename(columns={y_axis: "count"})

#         if chart_type == "table":
#             st.dataframe(agg_df, use_container_width=True)
#         else:
#             if chart_type.startswith("line"):
#                 fig = px.line(agg_df, x=x_axis, y=agg_df.columns[1], markers=True, title=f"{y_axis} by {x_axis}")
#             else:
#                 fig = px.bar(agg_df, x=x_axis, y=agg_df.columns[1], title=f"{y_axis} by {x_axis}")
#             st.plotly_chart(fig, use_container_width=True)

# # ---------- DOWNLOAD ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))




###################################################


# streamlit_app.py
# streamlit_app.py
# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data")  # ✅ change if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # ---------- LOAD SHEETS ----------
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# df = safe_numeric_cols(df)
# df.columns = df.columns.astype(str).str.strip()

# # ---------- DETECT MONTH COLUMNS ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None
# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()

# # ---------- HEADER FILTERS ----------
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")
#     filter_values = {}

#     # Normalize for easier matching
#     normalized_cols = {c.lower(): c for c in filter_columns}
#     region_col = normalized_cols.get("region")
#     area_col = normalized_cols.get("area")
#     rtm_kpi_col = normalized_cols.get("rtm kpis")  # <-- RTM KPIs filter column

#     cols = st.columns(len(filter_columns))
#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             unique_vals = df[col].dropna().astype(str).unique().tolist()
#             unique_vals.sort()

#             if col == area_col and region_col:
#                 # Dependent AREA filter based on selected Region
#                 selected_region = filter_values.get(region_col, "All")
#                 if selected_region != "All":
#                     valid_areas = df[df[region_col].astype(str) == selected_region][area_col].dropna().astype(str).unique().tolist()
#                 else:
#                     valid_areas = unique_vals
#                 valid_areas.sort()
#                 options = ["All"] + valid_areas
#                 filter_values[col] = st.selectbox("Area", options, index=0, key=f"filter_{col}")

#             elif col == rtm_kpi_col:
#                 # ✅ Only RTM KPIs column is multi-select
#                 selected_vals = st.multiselect(col, unique_vals, default=unique_vals, key=f"filter_{col}")
#                 filter_values[col] = selected_vals

#             else:
#                 # All other filters (including Region) remain single-select
#                 options = ["All"] + unique_vals
#                 filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

#     # Apply filters
#     for col, val in filter_values.items():
#         if col == rtm_kpi_col:
#             if val and len(val) > 0:
#                 df = df[df[col].astype(str).isin(val)]
#         else:
#             if val != "All":
#                 df = df[df[col].astype(str) == val]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ---------- DISPLAY ----------
# st.subheader(f"{selected_file_name} — {selected_sheet}")
# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # ---------- CHART BUILDER ----------
# st.markdown("---")
# st.subheader("📈 Quick Chart / Pivot")

# col1, col2 = st.columns([2, 1])
# with col2:
#     x_axis = st.selectbox("X axis (categorical / datetime)", ["<none>"] + df.columns.tolist())
#     y_axis = st.selectbox("Y axis (numeric)", ["<none>"] + df.columns.tolist())
#     agg_func = st.selectbox("Aggregation", ["sum", "mean", "median", "count"])
#     chart_type = st.selectbox("Chart type", ["line (time series)", "bar", "table"])
#     apply_filter = st.checkbox("Apply simple filter (column equals value)")
#     if apply_filter:
#         filter_col = st.selectbox("Filter column", df.columns.tolist())
#         unique_vals = df[filter_col].dropna().astype(str).unique().tolist()[:200]
#         filter_val = st.selectbox("Filter value", ["<all>"] + unique_vals)
#     else:
#         filter_col, filter_val = None, None

# with col1:
#     if x_axis == "<none>" or y_axis == "<none>":
#         st.info("Select X and Y to build a chart or select 'table' to view a pivot.")
#     else:
#         chart_df = df.copy()
#         if apply_filter and filter_val and filter_val != "<all>":
#             chart_df = chart_df[chart_df[filter_col].astype(str) == filter_val]

#         try:
#             if pd.api.types.is_datetime64_any_dtype(chart_df[x_axis]):
#                 chart_df[x_axis] = pd.to_datetime(chart_df[x_axis])
#         except Exception:
#             pass

#         # Aggregate
#         if agg_func == "sum":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].sum().reset_index()
#         elif agg_func == "mean":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].mean().reset_index()
#         elif agg_func == "median":
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].median().reset_index()
#         else:
#             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].count().reset_index().rename(columns={y_axis: "count"})

#         if chart_type == "table":
#             st.dataframe(agg_df, use_container_width=True)
#         else:
#             if chart_type.startswith("line"):
#                 fig = px.line(agg_df, x=x_axis, y=agg_df.columns[1], markers=True, title=f"{y_axis} by {x_axis}")
#             else:
#                 fig = px.bar(agg_df, x=x_axis, y=agg_df.columns[1], title=f"{y_axis} by {x_axis}")
#             st.plotly_chart(fig, use_container_width=True)

# # ---------- DOWNLOAD ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))



###########################################################


# # streamlit_app.py
# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data")  # ✅ change if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # ---------- LOAD SHEETS ----------
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# df = safe_numeric_cols(df)
# df.columns = df.columns.astype(str).str.strip()

# # ---------- DETECT MONTH COLUMNS ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None
# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()

# # ---------- HEADER FILTERS ----------
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")
#     filter_values = {}

#     # Normalize for easier matching
#     normalized_cols = {c.lower(): c for c in filter_columns}
#     region_col = normalized_cols.get("region")
#     area_col = normalized_cols.get("area")
#     rtm_kpi_col = normalized_cols.get("rtm kpis")  # <-- RTM KPIs filter column

#     cols = st.columns(len(filter_columns))
#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             unique_vals = df[col].dropna().astype(str).unique().tolist()
#             unique_vals.sort()

#             if col == area_col and region_col:
#                 # Dependent AREA filter based on selected Region
#                 selected_region = filter_values.get(region_col, "All")
#                 if selected_region != "All":
#                     valid_areas = df[df[region_col].astype(str) == selected_region][area_col].dropna().astype(str).unique().tolist()
#                 else:
#                     valid_areas = unique_vals
#                 valid_areas.sort()
#                 options = ["All"] + valid_areas
#                 filter_values[col] = st.selectbox("Area", options, index=0, key=f"filter_{col}")

#             elif col == rtm_kpi_col:
#                 # ✅ RTM KPIs multi-select with "All" option
#                 all_options = ["All"] + unique_vals
#                 selected_vals = st.multiselect(col, all_options, default=["All"], key=f"filter_{col}")
#                 if "All" in selected_vals:
#                     # If "All" is selected, use all unique_vals
#                     filter_values[col] = unique_vals
#                 else:
#                     filter_values[col] = selected_vals

#             else:
#                 # All other filters (including Region) remain single-select
#                 options = ["All"] + unique_vals
#                 filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

#     # Apply filters
#     for col, val in filter_values.items():
#         if col == rtm_kpi_col:
#             if val and len(val) > 0:
#                 df = df[df[col].astype(str).isin(val)]
#         else:
#             if val != "All":
#                 df = df[df[col].astype(str) == val]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ---------- DISPLAY ----------
# st.subheader(f"{selected_file_name} — {selected_sheet}")
# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # ---------- CHART BUILDER ----------
# # st.markdown("---")
# # st.subheader("📈 Quick Chart / Pivot")

# # col1, col2 = st.columns([2, 1])
# # with col2:
# #     x_axis = st.selectbox("X axis (categorical / datetime)", ["<none>"] + df.columns.tolist())
# #     y_axis = st.selectbox("Y axis (numeric)", ["<none>"] + df.columns.tolist())
# #     agg_func = st.selectbox("Aggregation", ["sum", "mean", "median", "count"])
# #     chart_type = st.selectbox("Chart type", ["line (time series)", "bar", "table"])
# #     apply_filter = st.checkbox("Apply simple filter (column equals value)")
# #     if apply_filter:
# #         filter_col = st.selectbox("Filter column", df.columns.tolist())
# #         unique_vals = df[filter_col].dropna().astype(str).unique().tolist()[:200]
# #         filter_val = st.selectbox("Filter value", ["<all>"] + unique_vals)
# #     else:
# #         filter_col, filter_val = None, None

# # with col1:
# #     if x_axis == "<none>" or y_axis == "<none>":
# #         st.info("Select X and Y to build a chart or select 'table' to view a pivot.")
# #     else:
# #         chart_df = df.copy()
# #         if apply_filter and filter_val and filter_val != "<all>":
# #             chart_df = chart_df[chart_df[filter_col].astype(str) == filter_val]

# #         try:
# #             if pd.api.types.is_datetime64_any_dtype(chart_df[x_axis]):
# #                 chart_df[x_axis] = pd.to_datetime(chart_df[x_axis])
# #         except Exception:
# #             pass

# #         # Aggregate
# #         if agg_func == "sum":
# #             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].sum().reset_index()
# #         elif agg_func == "mean":
# #             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].mean().reset_index()
# #         elif agg_func == "median":
# #             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].median().reset_index()
# #         else:
# #             agg_df = chart_df.groupby(x_axis, dropna=False)[y_axis].count().reset_index().rename(columns={y_axis: "count"})

# #         if chart_type == "table":
# #             st.dataframe(agg_df, use_container_width=True)
# #         else:
# #             if chart_type.startswith("line"):
# #                 fig = px.line(agg_df, x=x_axis, y=agg_df.columns[1], markers=True, title=f"{y_axis} by {x_axis}")
# #             else:
# #                 fig = px.bar(agg_df, x=x_axis, y=agg_df.columns[1], title=f"{y_axis} by {x_axis}")
# #             st.plotly_chart(fig, use_container_width=True)

# # ---------- DOWNLOAD ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))

######################################################################################





# # streamlit_app.py
# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data")  # ✅ change if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# def prettify_filename(file_name: str, sheet_name: str) -> str:
#     # Remove extension
#     base_name = os.path.splitext(file_name)[0]
#     # Replace underscores with spaces
#     base_name = base_name.replace("_", " ")
#     # Expand abbreviations
#     base_name = base_name.replace("MoM", "Month-on-Month").replace("Cats", "Categories")
#     # Combine with sheet name if not a default Sheet
#     if sheet_name.lower() not in ["sheet1", "sheet2", "sheet3"]:
#         return f"{base_name} — {sheet_name}"
#     else:
#         return base_name

# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # ---------- LOAD SHEETS ----------
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df = sheets[selected_sheet].copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}**  | Columns: **{len(df.columns):,}**")

# df = safe_numeric_cols(df)
# df.columns = df.columns.astype(str).str.strip()

# # ---------- DETECT MONTH COLUMNS ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None
# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()

# # ---------- HEADER FILTERS ----------
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")
#     filter_values = {}

#     # Normalize for easier matching
#     normalized_cols = {c.lower(): c for c in filter_columns}
#     region_col = normalized_cols.get("region")
#     area_col = normalized_cols.get("area")
#     rtm_kpi_col = normalized_cols.get("rtm kpis")  # <-- RTM KPIs filter column

#     cols = st.columns(len(filter_columns))
#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             unique_vals = df[col].dropna().astype(str).unique().tolist()
#             unique_vals.sort()

#             if col == area_col and region_col:
#                 # Dependent AREA filter based on selected Region
#                 selected_region = filter_values.get(region_col, "All")
#                 if selected_region != "All":
#                     valid_areas = df[df[region_col].astype(str) == selected_region][area_col].dropna().astype(str).unique().tolist()
#                 else:
#                     valid_areas = unique_vals
#                 valid_areas.sort()
#                 options = ["All"] + valid_areas
#                 filter_values[col] = st.selectbox("Area", options, index=0, key=f"filter_{col}")

#             elif col == rtm_kpi_col:
#                 # ✅ RTM KPIs multi-select with "All" option
#                 all_options = ["All"] + unique_vals
#                 selected_vals = st.multiselect(col, all_options, default=["All"], key=f"filter_{col}")
#                 if "All" in selected_vals or not selected_vals:
#                     filter_values[col] = unique_vals
#                 else:
#                     filter_values[col] = selected_vals

#             else:
#                 # All other filters (including Region) remain single-select
#                 options = ["All"] + unique_vals
#                 filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

#     # Apply filters
#     for col, val in filter_values.items():
#         if col == rtm_kpi_col:
#             if val and len(val) > 0:
#                 df = df[df[col].astype(str).isin(val)]
#         else:
#             if val != "All":
#                 df = df[df[col].astype(str) == val]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ---------- DISPLAY ----------
# display_name = prettify_filename(selected_file_name, selected_sheet)
# st.subheader(display_name)

# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")
#     st.dataframe(df.describe(include="number").T, use_container_width=True)

# # ---------- DOWNLOAD ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df)
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))


###########################################################
### this fixed the % s isseus

# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data") # ✅ change if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# def prettify_filename(file_name: str, sheet_name: str) -> str:
#     # Remove extension
#     base_name = os.path.splitext(file_name)[0]
#     # Replace underscores with spaces
#     base_name = base_name.replace("_", " ")
#     # Expand abbreviations
#     base_name = base_name.replace("MoM", "Month-on-Month").replace("Cats", "Categories")
#     # Combine with sheet name if not a default Sheet
#     if sheet_name.lower() not in ["sheet1", "sheet2", "sheet3"]:
#         return f"{base_name} — {sheet_name}"
#     else:
#         return base_name

# # ✅ MAJOR UPDATE: Now requires month_cols to be passed directly
# def format_percentage_columns(df: pd.DataFrame, month_cols: List[str], percent_col_name: str = "rtm kpis") -> pd.DataFrame:
#     # Identify the column containing KPI names
#     normalized_cols = {c.lower(): c for c in df.columns}
#     kpi_col = normalized_cols.get(percent_col_name.lower())

#     if not kpi_col:
#         return df

#     # 1. Identify KPIs that contain '%'
#     percent_kpis = df[kpi_col].astype(str).str.strip().loc[
#         df[kpi_col].astype(str).str.strip().str.contains("%", case=False, na=False)
#     ].unique().tolist()

#     # 2. Add "Strike Rate" explicitly
#     strike_rate_kpi = df[kpi_col].astype(str).str.strip().loc[
#         df[kpi_col].astype(str).str.strip().str.contains(r'^\s*Strike Rate\s*$', case=False, na=False, regex=True)
#     ].unique()

#     percent_kpis.extend(strike_rate_kpi)

#     # Remove duplicates and ensure we have unique KPI names
#     percent_kpis = list(set(percent_kpis))

#     if not percent_kpis:
#         return df

#     # We operate on a copy of the data to safely convert it to string formatting.
#     df_formatted = df.copy()

#     # Use the passed month_cols list directly
#     numeric_month_cols = [c for c in month_cols if c in df_formatted.columns]

#     if not numeric_month_cols:
#         return df # No month data columns found

#     # Loop through the month columns and apply percentage formatting for the relevant rows
#     for col in numeric_month_cols:
#         # Select rows where the KPI name is one of the identified percent KPIs
#         percent_rows_mask = df_formatted[kpi_col].astype(str).str.strip().isin(percent_kpis)

#         # Ensure the column is numeric before trying to multiply
#         if df_formatted[col].dtype not in ['int64', 'float64']:
#             df_formatted[col] = pd.to_numeric(df_formatted[col], errors='coerce')

#         # Multiply the values by 100, format them as strings with '%'
#         # Use a lambda to handle potential NaN/non-numeric values gracefully
#         df_formatted.loc[percent_rows_mask, col] = df_formatted.loc[percent_rows_mask, col].apply(
#             lambda x: f"{x * 100:.2f}%" if pd.notna(x) else ""
#         )
#     return df_formatted

# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY (Unchanged) ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # ---------- LOAD SHEETS ----------
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# # Keep the original, unfiltered numeric DF for potential use (especially summary stats)
# df_original_copy = sheets[selected_sheet].copy()
# df_original_copy = safe_numeric_cols(df_original_copy)
# df_original_copy.columns = df_original_copy.columns.astype(str).str.strip()

# df = df_original_copy.copy() # df is the data that will be filtered and formatted
# st.sidebar.markdown(f"Rows: **{len(df):,}** | Columns: **{len(df.columns):,}**")

# # ---------- DETECT MONTH COLUMNS (Crucial for the fix) ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None
# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()
# # ✅ Define the month columns here, before filtering, using the index
# month_columns = df.columns[month_start_index:].tolist()
# rtm_kpi_col = {c.lower(): c for c in filter_columns}.get("rtm kpis")


# # ---------- HEADER FILTERS (Unchanged) ----------
# filter_values = {}
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")

#     # Normalize for easier matching
#     normalized_cols = {c.lower(): c for c in filter_columns}
#     region_col = normalized_cols.get("region")
#     area_col = normalized_cols.get("area")

#     cols = st.columns(len(filter_columns))
#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             unique_vals = df[col].dropna().astype(str).unique().tolist()
#             unique_vals.sort()

#             if col == area_col and region_col:
#                 # Dependent AREA filter based on selected Region
#                 selected_region = filter_values.get(region_col, "All")
#                 if selected_region != "All":
#                     valid_areas = df[df[region_col].astype(str) == selected_region][area_col].dropna().astype(str).unique().tolist()
#                 else:
#                     valid_areas = unique_vals
#                 valid_areas.sort()
#                 options = ["All"] + valid_areas
#                 filter_values[col] = st.selectbox("Area", options, index=0, key=f"filter_{col}")

#             elif col == rtm_kpi_col:
#                 # RTM KPIs multi-select with "All" option
#                 all_options = ["All"] + unique_vals
#                 selected_vals = st.multiselect(col, all_options, default=["All"], key=f"filter_{col}")
#                 if "All" in selected_vals or not selected_vals:
#                     filter_values[col] = unique_vals
#                 else:
#                     filter_values[col] = selected_vals

#             else:
#                 # All other filters (including Region) remain single-select
#                 options = ["All"] + unique_vals
#                 filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

#     # Apply filters to the main df
#     for col, val in filter_values.items():
#         if col == rtm_kpi_col:
#             if val and len(val) > 0:
#                 df = df[df[col].astype(str).isin(val)]
#         else:
#             if val != "All":
#                 df = df[df[col].astype(str) == val]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ✅ Call the function, passing the reliably-identified month_columns list
# df_display = format_percentage_columns(df.copy(), month_columns, "rtm kpis")

# # ---------- DISPLAY (Unchanged) ----------
# display_name = prettify_filename(selected_file_name, selected_sheet)
# st.subheader(display_name)

# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df_display, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")

#     # Apply the same filters to the original numeric data for accurate stats
#     df_numeric = df_original_copy.copy()
#     for col, val in filter_values.items():
#         if col == rtm_kpi_col:
#             if val and len(val) > 0:
#                 df_numeric = df_numeric[df_numeric[col].astype(str).isin(val)]
#         else:
#             if val != "All":
#                 df_numeric = df_numeric[df_numeric[col].astype(str) == val]

#     st.dataframe(df_numeric.describe(include="number").T, use_container_width=True)


# # ---------- DOWNLOAD (Unchanged) ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df_display) # Use the formatted DF for download
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO (Unchanged) ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))




###################################################################
####### this is also very goood



# import streamlit as st
# import pandas as pd
# import os
# from pathlib import Path
# import io
# import re
# import plotly.express as px
# from typing import Dict, List

# # ---------- CONFIG ----------
# st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

# DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data") # ✅ change if needed
# ALLOWED_EXT = (".xlsx", ".xls")

# # ---------- UTILITIES ----------
# @st.cache_data(ttl=3600)
# def list_excel_files(folder: Path) -> List[Path]:
#     if not folder.exists():
#         return []
#     return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

# @st.cache_data(ttl=3600)
# def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
#     try:
#         xls = pd.read_excel(path, sheet_name=None)
#         for k, v in xls.items():
#             xls[k] = v.reset_index(drop=True)
#         return xls
#     except Exception as e:
#         return {"__error__": pd.DataFrame({"error": [str(e)]})}

# def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
#     return df.to_csv(index=False).encode("utf-8")

# def safe_numeric_cols(df: pd.DataFrame):
#     for c in df.columns:
#         if df[c].dtype == object:
#             coerced = pd.to_numeric(
#                 df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
#                 errors="coerce",
#             )
#             if coerced.notna().sum() > 0:
#                 df[c] = coerced
#     return df

# def prettify_filename(file_name: str, sheet_name: str) -> str:
#     # Remove extension
#     base_name = os.path.splitext(file_name)[0]
#     # Replace underscores with spaces
#     base_name = base_name.replace("_", " ")
#     # Expand abbreviations
#     base_name = base_name.replace("MoM", "Month-on-Month").replace("Cats", "Categories")
#     # Combine with sheet name if not a default Sheet
#     if sheet_name.lower() not in ["sheet1", "sheet2", "sheet3"]:
#         return f"{base_name} — {sheet_name}"
#     else:
#         return base_name

# # ✅ FUNCTION: Format KPIs as percentages (0.85 -> 85.00%)
# def format_percentage_columns(df: pd.DataFrame, month_cols: List[str], percent_col_name: str = "rtm kpis") -> pd.DataFrame:
#     normalized_cols = {c.lower(): c for c in df.columns}
#     kpi_col = normalized_cols.get(percent_col_name.lower())

#     if not kpi_col:
#         return df

#     # 1. Identify KPIs that contain '%'
#     percent_kpis = df[kpi_col].astype(str).str.strip().loc[
#         df[kpi_col].astype(str).str.strip().str.contains("%", case=False, na=False)
#     ].unique().tolist()

#     # 2. Add "Strike Rate" explicitly
#     strike_rate_kpi = df[kpi_col].astype(str).str.strip().loc[
#         df[kpi_col].astype(str).str.strip().str.contains(r'^\s*Strike Rate\s*$', case=False, na=False, regex=True)
#     ].unique()

#     percent_kpis.extend(strike_rate_kpi)
#     percent_kpis = list(set(percent_kpis))

#     if not percent_kpis:
#         return df

#     df_formatted = df.copy()
#     numeric_month_cols = [c for c in month_cols if c in df_formatted.columns]

#     if not numeric_month_cols:
#         return df

#     for col in numeric_month_cols:
#         percent_rows_mask = df_formatted[kpi_col].astype(str).str.strip().isin(percent_kpis)

#         # Ensure the column is numeric before trying to multiply
#         if df_formatted[col].dtype not in ['int64', 'float64']:
#             df_formatted[col] = pd.to_numeric(df_formatted[col], errors='coerce')

#         # Apply formatting
#         df_formatted.loc[percent_rows_mask, col] = df_formatted.loc[percent_rows_mask, col].apply(
#             lambda x: f"{x * 100:.2f}%" if pd.notna(x) else ""
#         )
#     return df_formatted

# # ✅ CORRECTED FUNCTION: Format specified KPIs as whole numbers (e.g., 5.8 -> 6)
# def format_whole_numbers(df: pd.DataFrame, whole_number_kpis: List[str], kpi_col_name: str = "rtm kpis", month_cols: List[str] = None) -> pd.DataFrame:
#     if not whole_number_kpis or not month_cols:
#         return df

#     normalized_cols = {c.lower(): c for c in df.columns}
#     kpi_col = normalized_cols.get(kpi_col_name.lower())

#     if not kpi_col:
#         return df

#     df_formatted = df.copy()

#     # Identify unique KPI names to format
#     kpis_to_format = df[kpi_col].astype(str).str.strip().loc[
#         df[kpi_col].astype(str).str.strip().isin(whole_number_kpis)
#     ].unique().tolist()

#     if not kpis_to_format:
#         return df

#     numeric_month_cols = [c for c in month_cols if c in df_formatted.columns]

#     # Loop through month columns and apply whole number formatting
#     for col in numeric_month_cols:
#         # Select rows where the KPI name is one of the identified whole number KPIs
#         whole_number_rows_mask = df_formatted[kpi_col].astype(str).str.strip().isin(kpis_to_format)

#         # 🐛 CRITICAL FIX APPLIED: Extract numeric values from the current column, ignoring formatting strings
#         numeric_series = pd.to_numeric(
#             df_formatted.loc[whole_number_rows_mask, col].astype(str).str.replace('%', '').str.replace(',', ''),
#             errors='coerce'
#         )

#         # Apply whole number formatting (round, convert to int, add thousand separator)
#         formatted_values = numeric_series.apply(
#             lambda x: f"{int(round(x)):,}" if pd.notna(x) else ""
#         )

#         # Update only the specific rows with the new string values
#         df_formatted.loc[whole_number_rows_mask, col] = formatted_values

#     return df_formatted


# # ---------- UI ----------
# st.title("📊 MoM RTM KPI — Explorer")
# st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# # ---------- FILE DISCOVERY ----------
# st.sidebar.header("📁 Data source")
# st.sidebar.write("Reading Excel files from:")
# st.sidebar.code(str(DATA_FOLDER))

# files = list_excel_files(DATA_FOLDER)
# if not files:
#     st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
#     st.stop()

# file_options = [f.name for f in files]
# selected_file_name = st.sidebar.selectbox("Select file", file_options)
# selected_path = DATA_FOLDER / selected_file_name

# # ---------- LOAD SHEETS ----------
# with st.spinner(f"Loading {selected_file_name}..."):
#     sheets = read_excel_all_sheets(selected_path)

# if "__error__" in sheets:
#     st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
#     st.stop()

# sheet_names = list(sheets.keys())
# selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

# df_original_copy = sheets[selected_sheet].copy()
# df_original_copy = safe_numeric_cols(df_original_copy)
# df_original_copy.columns = df_original_copy.columns.astype(str).str.strip()

# df = df_original_copy.copy()
# st.sidebar.markdown(f"Rows: **{len(df):,}** | Columns: **{len(df.columns):,}**")

# # ---------- DETECT MONTH COLUMNS ----------
# month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
# month_start_index = None
# for idx, col in enumerate(df.columns):
#     if month_pattern.search(str(col)):
#         month_start_index = idx
#         break

# if month_start_index is None:
#     month_start_index = min(3, len(df.columns))

# filter_columns = df.columns[:month_start_index].tolist()
# month_columns = df.columns[month_start_index:].tolist()
# rtm_kpi_col = {c.lower(): c for c in filter_columns}.get("rtm kpis")


# # ---------- HEADER FILTERS ----------
# filter_values = {}
# if filter_columns:
#     st.markdown("### 🔎 Filters (Before Month Columns)")

#     normalized_cols = {c.lower(): c for c in filter_columns}
#     region_col = normalized_cols.get("region")
#     area_col = normalized_cols.get("area")

#     cols = st.columns(len(filter_columns))
#     for i, col in enumerate(filter_columns):
#         with cols[i]:
#             unique_vals = df[col].dropna().astype(str).unique().tolist()
#             unique_vals.sort()

#             if col == area_col and region_col:
#                 selected_region = filter_values.get(region_col, "All")
#                 if selected_region != "All":
#                     valid_areas = df[df[region_col].astype(str) == selected_region][area_col].dropna().astype(str).unique().tolist()
#                 else:
#                     valid_areas = unique_vals
#                 valid_areas.sort()
#                 options = ["All"] + valid_areas
#                 filter_values[col] = st.selectbox("Area", options, index=0, key=f"filter_{col}")

#             elif col == rtm_kpi_col:
#                 all_options = ["All"] + unique_vals
#                 selected_vals = st.multiselect(col, all_options, default=["All"], key=f"filter_{col}")
#                 if "All" in selected_vals or not selected_vals:
#                     filter_values[col] = unique_vals
#                 else:
#                     filter_values[col] = selected_vals

#             else:
#                 options = ["All"] + unique_vals
#                 filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

#     # Apply filters to the main df
#     for col, val in filter_values.items():
#         if col == rtm_kpi_col:
#             if val and len(val) > 0:
#                 df = df[df[col].astype(str).isin(val)]
#         else:
#             if val != "All":
#                 df = df[df[col].astype(str) == val]

# st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# # ✅ Apply percentage formatting
# df_display = format_percentage_columns(df.copy(), month_columns, "rtm kpis")

# # ✅ Apply whole number formatting for SKU count
# WHOLE_NUMBER_KPI = ["Average # of SKU per store"]
# df_display = format_whole_numbers(
#     df_display,
#     whole_number_kpis=WHOLE_NUMBER_KPI,
#     kpi_col_name="rtm kpis",
#     month_cols=month_columns
# )

# # ---------- DISPLAY ----------
# display_name = prettify_filename(selected_file_name, selected_sheet)
# st.subheader(display_name)

# view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
# if view_mode == "Table":
#     st.dataframe(df_display, use_container_width=True)
# else:
#     st.write("Columns:")
#     st.write(df.columns.tolist())
#     st.write("Basic stats for numeric columns:")

#     # Apply the same filters to the original numeric data for accurate stats
#     df_numeric = df_original_copy.copy()
#     for col, val in filter_values.items():
#         if col == rtm_kpi_col:
#             if val and len(val) > 0:
#                 df_numeric = df_numeric[df_numeric[col].astype(str).isin(val)]
#         else:
#             if val != "All":
#                 df_numeric = df_numeric[df_numeric[col].astype(str) == val]

#     st.dataframe(df_numeric.describe(include="number").T, use_container_width=True)


# # ---------- DOWNLOAD ----------
# st.markdown("---")
# st.subheader("⬇️ Export / Download")
# download_df = st.checkbox("Download current (filtered) sheet as CSV")
# if download_df:
#     b = df_to_csv_bytes(df_display)
#     st.download_button(
#         label="Download CSV",
#         data=b,
#         file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
#         mime="text/csv",
#     )

# # ---------- SIDEBAR INFO ----------
# st.sidebar.markdown("---")
# st.sidebar.header("Files found")
# for p in files:
#     st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
# st.sidebar.markdown("---")
# st.sidebar.write("Streamlit app configured for:")
# st.sidebar.code(str(DATA_FOLDER))



#######################################################


import streamlit as st
import pandas as pd
import os
from pathlib import Path
import io
import re
import plotly.express as px
from typing import Dict, List

# =========================================================================
# 🔐 AUTHENTICATION FUNCTION (Add this to the very top of your script)
# =========================================================================

def check_password():
    """Returns True if the user has entered the correct password."""

    # 1. Check if the password is correct
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            # Don't store the password after verification
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    # 2. Check current state
    if st.session_state.get("password_correct", False):
        return True

    # 3. Show password input if not correct
    st.title("🔐 RTM KPI Login")
    
    st.text_input(
        "Enter Access Code", 
        type="password", 
        on_change=password_entered, 
        key="password",
        # Use collapsed visibility to hide the input label, keeping it clean
        label_visibility="collapsed" 
    )
    
    # Display error message if password was tried and failed
    if "password_correct" in st.session_state:
        st.error("Incorrect password. Please try again.")
    
    return False

# =========================================================================
# 🛑 CALL THE GATE FUNCTION (Add this right after the function definition)
# =========================================================================

if not check_password():
    st.stop() 

# =========================================================================
# The rest of your app code (st.set_page_config, st.title, etc.) 
# starts here and will only run if check_password() returns True.
# =========================================================================

# ---------- CONFIG ----------
st.set_page_config(page_title="MoM RTM KPI Viewer", layout="wide")

#DATA_FOLDER = Path(__file__).parent / "Data"
DATA_FOLDER = Path(__file__).parent
#DATA_FOLDER = Path(r"C:\Users\HP\Desktop\ExcelProject\Data") # ✅ change if needed
ALLOWED_EXT = (".xlsx", ".xls")

# ---------- UTILITIES ----------
@st.cache_data(ttl=3600)
def list_excel_files(folder: Path) -> List[Path]:
    if not folder.exists():
        return []
    return sorted([p for p in folder.iterdir() if p.suffix.lower() in ALLOWED_EXT])

@st.cache_data(ttl=3600)
def read_excel_all_sheets(path: Path) -> Dict[str, pd.DataFrame]:
    try:
        xls = pd.read_excel(path, sheet_name=None)
        for k, v in xls.items():
            xls[k] = v.reset_index(drop=True)
        return xls
    except Exception as e:
        return {"__error__": pd.DataFrame({"error": [str(e)]})}

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

def safe_numeric_cols(df: pd.DataFrame):
    for c in df.columns:
        if df[c].dtype == object:
            coerced = pd.to_numeric(
                df[c].astype(str).str.replace(",", "").str.replace("₦", "").str.strip(),
                errors="coerce",
            )
            if coerced.notna().sum() > 0:
                df[c] = coerced
    return df

def prettify_filename(file_name: str, sheet_name: str) -> str:
    # Remove extension
    base_name = os.path.splitext(file_name)[0]
    # Replace underscores with spaces
    base_name = base_name.replace("_", " ")
    # Expand abbreviations
    base_name = base_name.replace("MoM", "Month-on-Month").replace("Cats", "Categories")
    # Combine with sheet name if not a default Sheet
    if sheet_name.lower() not in ["sheet1", "sheet2", "sheet3"]:
        return f"{base_name} — {sheet_name}"
    else:
        return base_name

# ✅ FUNCTION: Format KPIs as percentages (0.85 -> 85.00%)
def format_percentage_columns(df: pd.DataFrame, month_cols: List[str], percent_col_name: str = "rtm kpis") -> pd.DataFrame:
    normalized_cols = {c.lower(): c for c in df.columns}
    kpi_col = normalized_cols.get(percent_col_name.lower())

    if not kpi_col:
        return df

    # 1. Identify KPIs that contain '%'
    percent_kpis = df[kpi_col].astype(str).str.strip().loc[
        df[kpi_col].astype(str).str.strip().str.contains("%", case=False, na=False)
    ].unique().tolist()

    # 2. Add "Strike Rate" explicitly
    strike_rate_kpi = df[kpi_col].astype(str).str.strip().loc[
        df[kpi_col].astype(str).str.strip().str.contains(r'^\s*Strike Rate\s*$', case=False, na=False, regex=True)
    ].unique()

    percent_kpis.extend(strike_rate_kpi)
    percent_kpis = list(set(percent_kpis))

    if not percent_kpis:
        return df

    df_formatted = df.copy()
    numeric_month_cols = [c for c in month_cols if c in df_formatted.columns]

    if not numeric_month_cols:
        return df

    for col in numeric_month_cols:
        percent_rows_mask = df_formatted[kpi_col].astype(str).str.strip().isin(percent_kpis)

        if df_formatted[col].dtype not in ['int64', 'float64']:
            df_formatted[col] = pd.to_numeric(df_formatted[col], errors='coerce')

        df_formatted.loc[percent_rows_mask, col] = df_formatted.loc[percent_rows_mask, col].apply(
            lambda x: f"{x * 100:.2f}%" if pd.notna(x) else ""
        )
    return df_formatted

# ✅ FUNCTION: Format specified KPIs as whole numbers with thousand separators (e.g., 5.8 -> 6)
def format_whole_numbers(df: pd.DataFrame, whole_number_kpis: List[str], kpi_col_name: str = "rtm kpis", month_cols: List[str] = None) -> pd.DataFrame:
    if not whole_number_kpis or not month_cols:
        return df

    normalized_cols = {c.lower(): c for c in df.columns}
    kpi_col = normalized_cols.get(kpi_col_name.lower())

    if not kpi_col:
        return df

    df_formatted = df.copy()

    # Identify unique KPI names to format
    kpis_to_format = df[kpi_col].astype(str).str.strip().loc[
        df[kpi_col].astype(str).str.strip().isin(whole_number_kpis)
    ].unique().tolist()

    if not kpis_to_format:
        return df

    numeric_month_cols = [c for c in month_cols if c in df_formatted.columns]

    # Loop through month columns and apply whole number formatting
    for col in numeric_month_cols:
        # Select rows where the KPI name is one of the identified whole number KPIs
        whole_number_rows_mask = df_formatted[kpi_col].astype(str).str.strip().isin(kpis_to_format)

        # Extract numeric values from the current column, ignoring formatting strings
        numeric_series = pd.to_numeric(
            df_formatted.loc[whole_number_rows_mask, col].astype(str).str.replace('%', '').str.replace(',', ''),
            errors='coerce'
        )

        # Apply whole number formatting (round, convert to int, add thousand separator)
        formatted_values = numeric_series.apply(
            lambda x: f"{int(round(x)):,}" if pd.notna(x) else ""
        )

        # Update only the specific rows with the new string values
        df_formatted.loc[whole_number_rows_mask, col] = formatted_values

    return df_formatted


# ---------- UI ----------
st.title("📊 MoM RTM KPI — Explorer")
#st.markdown("Browse Excel KPI files, preview sheets, build quick charts, and export data.")

# ---------- FILE DISCOVERY ----------
#st.sidebar.header("📁 Data source")
#st.sidebar.write("Reading Excel files from:")
st.sidebar.code(str(DATA_FOLDER))

files = list_excel_files(DATA_FOLDER)
if not files:
    st.error(f"No Excel files found in {DATA_FOLDER}. Please ensure your .xlsx files are in that folder.")
    st.stop()

file_options = [f.name for f in files]
selected_file_name = st.sidebar.selectbox("Select file", file_options)
selected_path = DATA_FOLDER / selected_file_name

# ---------- LOAD SHEETS ----------
with st.spinner(f"Loading {selected_file_name}..."):
    sheets = read_excel_all_sheets(selected_path)

if "__error__" in sheets:
    st.error("Error reading file: " + str(sheets["__error__"].iloc[0, 0]))
    st.stop()

sheet_names = list(sheets.keys())
selected_sheet = st.sidebar.selectbox("Select sheet", sheet_names)

df_original_copy = sheets[selected_sheet].copy()
df_original_copy = safe_numeric_cols(df_original_copy)
df_original_copy.columns = df_original_copy.columns.astype(str).str.strip()

df = df_original_copy.copy()
#st.sidebar.markdown(f"Rows: **{len(df):,}** | Columns: **{len(df.columns):,}**")

# ---------- DETECT MONTH COLUMNS ----------
month_pattern = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\b20\d{2}[-_/]?\d{0,2})", re.IGNORECASE)
month_start_index = None
for idx, col in enumerate(df.columns):
    if month_pattern.search(str(col)):
        month_start_index = idx
        break

if month_start_index is None:
    month_start_index = min(3, len(df.columns))

filter_columns = df.columns[:month_start_index].tolist()
month_columns = df.columns[month_start_index:].tolist()
rtm_kpi_col = {c.lower(): c for c in filter_columns}.get("rtm kpis")


# ---------- HEADER FILTERS ----------
filter_values = {}
if filter_columns:
    #st.markdown("### 🔎 Filters (Before Month Columns)")

    normalized_cols = {c.lower(): c for c in filter_columns}
    region_col = normalized_cols.get("region")
    area_col = normalized_cols.get("area")

    cols = st.columns(len(filter_columns))
    for i, col in enumerate(filter_columns):
        with cols[i]:
            unique_vals = df[col].dropna().astype(str).unique().tolist()
            unique_vals.sort()

            if col == area_col and region_col:
                selected_region = filter_values.get(region_col, "All")
                if selected_region != "All":
                    valid_areas = df[df[region_col].astype(str) == selected_region][area_col].dropna().astype(str).unique().tolist()
                else:
                    valid_areas = unique_vals
                valid_areas.sort()
                options = ["All"] + valid_areas
                filter_values[col] = st.selectbox("Area", options, index=0, key=f"filter_{col}")

            elif col == rtm_kpi_col:
                all_options = ["All"] + unique_vals
                selected_vals = st.multiselect(col, all_options, default=["All"], key=f"filter_{col}")
                if "All" in selected_vals or not selected_vals:
                    filter_values[col] = unique_vals
                else:
                    filter_values[col] = selected_vals

            else:
                options = ["All"] + unique_vals
                filter_values[col] = st.selectbox(col, options, index=0, key=f"filter_{col}")

    # Apply filters to the main df
    for col, val in filter_values.items():
        if col == rtm_kpi_col:
            if val and len(val) > 0:
                df = df[df[col].astype(str).isin(val)]
        else:
            if val != "All":
                df = df[df[col].astype(str) == val]

#st.markdown(f"✅ Showing **{len(df):,}** filtered rows.")

# ✅ Apply percentage formatting
df_display = format_percentage_columns(df.copy(), month_columns, "rtm kpis")

# ✅ Define the list of KPIs that require thousand separators and whole numbers
WHOLE_NUMBER_KPI = [
    "Average # of SKU per store",
    "# of Outlet Covered",
    "# of Productive Outlets",
    "Asun Prod. Outlets",
    "Bama Jars Prod. Outlets",
    "Bama Sac Prod. Outlets",
    "Curry Prod. Outlets",
    "Gino Max Prod. Outlets",
    "Jago Jars Prod. Outlets",
    "Jago Sac Prod. Outlets",
    "Jumbo Cubes Prod. Outlets",
    "PCC Prod. Outlets",
    "PCT Prod. Outlets",
    "RH Pepper Prod. Outlets",
    "Sales per outlet visited (N)",
    "Shawarma Jars Prod. Outlets",
    "Shawarma Sac Prod. Outlets",
    "Thyme Prod. Outlets",
    "Tom tins/SUP Prod. Outlets",
    "Tomato Sac Prod. Outlets",
    "Total Sell out Value"
]

# ✅ Apply whole number and thousand-separator formatting
df_display = format_whole_numbers(
    df_display,
    whole_number_kpis=WHOLE_NUMBER_KPI,
    kpi_col_name="rtm kpis",
    month_cols=month_columns
)

# ---------- DISPLAY ----------
display_name = prettify_filename(selected_file_name, selected_sheet)
st.subheader(display_name)

#view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True)
view_mode = st.radio("View mode", ["Table", "Summary"], horizontal=True, label_visibility="collapsed")
if view_mode == "Table":
    st.dataframe(df_display, use_container_width=True)
else:
    st.write("Columns:")
    st.write(df.columns.tolist())
    st.write("Basic stats for numeric columns:")

    # Apply the same filters to the original numeric data for accurate stats
    df_numeric = df_original_copy.copy()
    for col, val in filter_values.items():
        if col == rtm_kpi_col:
            if val and len(val) > 0:
                df_numeric = df_numeric[df_numeric[col].astype(str).isin(val)]
        else:
            if val != "All":
                df_numeric = df_numeric[df_numeric[col].astype(str) == val]

    st.dataframe(df_numeric.describe(include="number").T, use_container_width=True)


# ---------- DOWNLOAD ----------
st.markdown("---")
st.subheader("⬇️ Export / Download")
download_df = st.checkbox("Download current (filtered) sheet as CSV")
if download_df:
    b = df_to_csv_bytes(df_display)
    st.download_button(
        label="Download CSV",
        data=b,
        file_name=f"{selected_file_name}_{selected_sheet}_filtered.csv",
        mime="text/csv",
    )

# ---------- SIDEBAR INFO ----------
st.sidebar.markdown("---")
#st.sidebar.header("Files found")
#for p in files:
#    st.sidebar.write(f"- {p.name} ({p.stat().st_size // 1024} KB)")
st.sidebar.markdown("---")
st.sidebar.write("Streamlit app configured for:")
st.sidebar.code(str(DATA_FOLDER))




