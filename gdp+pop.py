import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("🗺️ Interactive U.S. County Data Map (2023)")

# --- Sidebar: Data selection ---
view_option = st.sidebar.selectbox("Select Data to View:", ["GDP", "Population"])

# --- Function to load and clean data ---
def load_data(view_option):
    if view_option == "GDP":
        df = pd.read_csv("county_gdp_2023.csv", skiprows=3)
        df = df.rename(columns={"GeoFips": "fips", "GeoName": "county", "2023": "gdp_2023"})
        df["gdp_2023"] = pd.to_numeric(df["gdp_2023"], errors="coerce")
    else:
        df = pd.read_csv("county_population_2023.csv", skiprows=3)
        df = df.rename(columns={"GeoFips": "fips", "GeoName": "county", "2023": "population_2023"})
        df["population_2023"] = pd.to_numeric(df["population_2023"], errors="coerce")

    df["fips"] = df["fips"].astype(str).str.zfill(5)
    return df

# --- Load selected data ---
try:
    data_df = load_data(view_option)
except Exception as e:
    st.error(f"Failed to load {view_option} data: {e}")
    st.stop()

# --- Load county geometry ---
geo_url = "https://raw.githubusercontent.com/holtzy/The-Python-Graph-Gallery/master/static/data/US-counties.geojson"
geo = gpd.read_file(geo_url)
geo["id"] = geo["id"].astype(str).str.zfill(5)
geo = geo[~geo["STATE"].isin(["02", "15", "72"])]  # Exclude AK, HI, PR

# --- Merge data with GeoDataFrame ---
merged = geo.merge(data_df, left_on="id", right_on="fips")

# --- Choose color column and label ---
color_column = "gdp_2023" if view_option == "GDP" else "population_2023"
color_label = "GDP ($)" if view_option == "GDP" else "Population"

# --- Create interactive map ---
fig = px.choropleth(
    merged,
    geojson=merged.geometry,
    locations=merged.index,
    color=color_column,
    hover_name="county",
    hover_data={"fips": True, color_column: ":,.0f"},
    color_continuous_scale="Viridis",
    labels={color_column: color_label},
    title=f"County-Level {view_option} (2023)"
)

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(
    margin={"r":0,"t":50,"l":0,"b":0},
    coloraxis_colorbar=dict(title=color_label)
)

# --- Show map and table ---
st.plotly_chart(fig, use_container_width=True)

st.subheader(f"Top 10 Counties by {view_option} (2023)")
top10 = merged.sort_values(color_column, ascending=False).head(10)[["county", color_column]].copy()
top10[color_column] = top10[color_column].apply(lambda x: f"{x:,.0f}")
st.dataframe(top10.reset_index(drop=True))