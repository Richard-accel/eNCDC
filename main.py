from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Query
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import geopandas as gpd
import json
import os
from sqlalchemy import create_engine
from keplergl import KeplerGl
import copy

# Initialize the FastAPI app
app = FastAPI()

patient_cases_df = None

# Mount static and templates directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load Malaysia simplified polygon GeoJSON for state boundaries
with open("data/geoBoundaries-MYS-ADM1_simplified.geojson", "r", encoding="utf-8") as f:
    geojson = json.load(f)


# Configuration for COVID-19 map (polygon-based)
config = {
    'version': 'v1',
    'config': {
        'visState': {
            'layers': [{
                'id': 'covid_layer',
                'type': 'geojson',
                'config': {
                    'dataId': 'Malaysia_COVID_Cases',
                    'label': 'COVID-19 Total Cases',
                    'color': [255, 203, 153],
                    'highlightColor': [252, 242, 26, 255],
                    'columns': {
                        'geojson': '_geojson'  
                    },
                    'isVisible': True,
                    'visConfig': {
                        'opacity': 0.7,
                        'strokeOpacity': 0.8,
                        'thickness': 0.5,
                        'colorRange': {
                            'name': 'ColorBrewer YlOrRd-6',
                            'type': 'sequential',
                            'category': 'ColorBrewer',
                            'colors': ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']
                        },
                        'radius': 10,
                        'sizeRange': [0, 10],
                        'filled': True
                    }
                }
            }],
            'interactionConfig': {
                'tooltip': {
                    'fieldsToShow': {
                        'Malaysia_COVID_Cases': ['shapeName', 'total_cases']
                    },
                    'enabled': True
                }
            }
        },
        'mapState': {
            'latitude': 4.2105,
            'longitude': 101.9758,
            'zoom': 4,
        }
    }
}

# Configuration for polygon map (state-based with clinic and pharmacy counts)
polygon_map_config = {
    'version': 'v1',
    'config': {
        'mapState': {
            'latitude': 4.2105,
            'longitude': 101.9758,
            'zoom': 4.5
        },
        'visState': {
            'layers': [{
                'id': 'polygon_layer',
                'type': 'geojson',
                'config': {
                    'dataId': 'Malaysia_States',
                    'label': 'State Polygon',
                    'color': [255, 203, 153],
                    'highlightColor': [252, 242, 26, 255],
                    'columns': {
                        'geojson': '_geojson'
                    },
                    'isVisible': True,
                    'visConfig': {
                        'opacity': 0.5,
                        'thickness': 1,
                        'colorRange': {
                            'name': 'ColorBrewer YlOrRd-6',
                            'type': 'sequential',
                            'category': 'ColorBrewer',
                            'colors': ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']
                        },
                        'filled': True
                    }
                }
            }],
            'interactionConfig': {
                'tooltip': {
                    'fieldsToShow': {
                        'Malaysia_States': ['shapeName', 'clinic_count', 'pharmacy_count']
                    },
                    'enabled': True
                }
            }
        }
    }
}

# Configuration for point map (facilities plotted as points)
point_config = {
    "version": "v1",
    "config": {
        "mapState": {
            "latitude": 4.2105,
            "longitude": 101.9758,
            "zoom": 5
        },
        "visState": {
            "layers": [{
                "id": "facility_layer",
                "type": "point",
                "config": {
                    "dataId": "All Facilities",
                    "label": "Health Facilities",
                    "color": [0, 153, 255],
                    "columns": {
                        "lat": "latitude",
                        "lng": "longitude"
                    },
                    "isVisible": True,
                    "visConfig": {
                        "radius": 10,
                        "fixedRadius": False,
                        "opacity": 0.8,
                        "outline": False,
                        "thickness": 2,
                        "filled": True
                    }
                }
            }],
            "interactionConfig": {
                "tooltip": {
                    "fieldsToShow": {
                        "All Facilities": ["name", "amenity", "state"]
                    },
                    "enabled": True
                }
            }
        }
    }
}


# === Covid data configuration 
# Load Covid CSV data
csv_data = pd.read_csv('https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/refs/heads/main/epidemic/cases_state.csv')

# Sum total cases per state
state_totals = csv_data.groupby('state')['cases_new'].sum().reset_index()
state_totals.columns = ['state', 'total_cases']

# Load Boundaries GeoJSON
geo_data = gpd.read_file('asserts/geoBoundaries-MYS-ADM1_simplified.geojson')

# Rename states to match
geo_data['shapeName'] = geo_data['shapeName'].replace({
    'Pulau Pinang': 'Penang',
    'Kuala Lumpur': 'W.P. Kuala Lumpur',
    'Labuan': 'W.P. Labuan',
    'Putrajaya': 'W.P. Putrajaya'
})

# Merge and clean
merged_data = geo_data.merge(state_totals, how='left', left_on='shapeName', right_on='state')
merged_data['total_cases'] = merged_data['total_cases'].fillna(0).astype(int)

# Clean geometry to avoid JSON serialization warnings
merged_data = merged_data[merged_data.is_valid]
merged_data = merged_data.dropna(subset=['geometry'])
merged_data.replace([float('inf'), float('-inf')], 0, inplace=True)

# Create map & add data
covid_map = KeplerGl(show_docs=False, height=450,read_only=True,width=900)
covid_map.add_data(data=merged_data, name="Malaysia_COVID_Cases")
covid_map.config=config

# === Facilities DB Config ===
DB_USER = "testing1_415q_user"
DB_PASSWORD = "syezjh72qciEKZUCBIcR4LF6YkiH7aXK"
DB_HOST = "dpg-cvr1u8ngi27c738j3acg-a.singapore-postgres.render.com"
DB_PORT = "5432"
DB_NAME = "testing1_415q"
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
query = "SELECT name, amenity, state, latitude, longitude FROM health_facilities;"

# === Patient Cases DB Config ===
PATIENT_DB_USER = "postgres.hrbvbvlssmffrsjzzgcc"
PATIENT_DB_PASSWORD = "Novoheal9527"
PATIENT_DB_HOST = "aws-0-ap-southeast-1.pooler.supabase.com"
PATIENT_DB_PORT = "6543"
PATIENT_DB_NAME = "postgres"
patient_engine = create_engine(f"postgresql+psycopg2://{PATIENT_DB_USER}:{PATIENT_DB_PASSWORD}@{PATIENT_DB_HOST}:{PATIENT_DB_PORT}/{PATIENT_DB_NAME}")

patient_query = "SELECT * FROM encdc.patientcase;"

# === Covid Data ===
cases_url = "https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/cases_malaysia.csv"
hospital_url = "https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/hospital.csv"
death_url = "https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/deaths_malaysia.csv"
state_cases_url = "https://raw.githubusercontent.com/MoH-Malaysia/covid19-public/main/epidemic/cases_state.csv"

# === Generate Covid Charts and KPI ===
def generate_charts():
    df_cases = pd.read_csv(cases_url, parse_dates=['date'])
    df_hospital = pd.read_csv(hospital_url, parse_dates=['date'])
    df_deaths = pd.read_csv(death_url, parse_dates=['date'])
    df_state_cases = pd.read_csv(state_cases_url, parse_dates=['date'])

    today = df_cases['date'].max()
    new_cases = int(df_cases[df_cases['date'] == today]['cases_new'].fillna(0).values[0])
    deaths = int(df_deaths[df_deaths['date'] == today]['deaths_new'].fillna(0).values[0])
    hosp_today = df_hospital[df_hospital['date'] == today]
    hospitalized = int(hosp_today['admitted_covid'].fillna(0).values[0]) if not hosp_today.empty else 0
    discharged = int(hosp_today['discharged_covid'].fillna(0).values[0]) if not hosp_today.empty else 0


    df_cases['total_cases'] = df_cases['cases_new'].fillna(0).cumsum()
    line_fig = go.Figure()
    line_fig.add_trace(go.Scatter(x=df_cases['date'], y=df_cases['total_cases'], mode='lines', name='Total Cases'))
    line_fig.update_layout(title='Total COVID-19 Cases Over Time', xaxis_title='Date', yaxis_title='Cumulative Cases')

    df_hospital['year'] = df_hospital['date'].dt.year
    annual_data = df_hospital.groupby('year')[['admitted_covid', 'discharged_covid']].sum().reset_index()
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(x=annual_data['year'], y=annual_data['admitted_covid'], name='Hospitalized', marker_color='orange'))
    bar_fig.add_trace(go.Bar(x=annual_data['year'], y=annual_data['discharged_covid'], name='Discharged', marker_color='green'))
    bar_fig.update_layout(title='Hospitalized vs Discharged per Year', xaxis_title='Year', yaxis_title='Patients', barmode='group')

    df_state_cases_today = df_state_cases[df_state_cases['date'] == today]
    state_fig = px.pie(df_state_cases_today, names='state', values='cases_new', title=f'COVID-19 New Cases by State on {today.strftime("%Y-%m-%d")}', hole=0.3)

    return {
        "covid_latest_case_date": today.strftime('%d %B %Y'),
        "covid_new_cases": new_cases,
        "covid_hospitalized": hospitalized,
        "covid_discharged": discharged,
        "covid_deaths": deaths,
        "covid_line_chart": line_fig.to_html(full_html=False),
        "covid_bar_chart": bar_fig.to_html(full_html=False),
        "covid_state_chart": state_fig.to_html(full_html=False),
    }

# === Generate Polygon HTML ===
def generate_polygon_html():
    df = pd.read_sql(query, engine)
    df['amenity'] = df['amenity'].str.lower()
    counts = df.groupby('state')['amenity'].value_counts().unstack(fill_value=0).reset_index()
    counts.rename(columns={'clinic': 'clinic_count', 'pharmacy': 'pharmacy_count'}, inplace=True)

    geojson_copy = copy.deepcopy(geojson)  # 🔧 Important

    for feature in geojson_copy['features']:
        state_name = feature['properties'].get('shapeName', '').lower()
        match = counts[counts['state'].str.lower() == state_name]
        if not match.empty:
            feature['properties']['clinic_count'] = int(match['clinic_count'].values[0])
            feature['properties']['pharmacy_count'] = int(match['pharmacy_count'].values[0])
        else:
            feature['properties']['clinic_count'] = 0
            feature['properties']['pharmacy_count'] = 0

    kepler_map = KeplerGl(height=450, read_only=True, width=900)
    kepler_map.add_data(data=geojson_copy, name='Malaysia_States')  # 🔧 use the copy here
    kepler_map.config = polygon_map_config

    return kepler_map._repr_html_()

def load_patient_cases():
    global patient_cases_df
    patient_cases_df = pd.read_sql(patient_query, patient_engine)

load_patient_cases()

@app.get("/")
def home(request: Request):
    data = generate_charts()
    facility_data = facility_kpi()

    if patient_cases_df is not None:
        temp_df = patient_cases_df.copy()

        # Convert any datetime columns to string for JSON serialization
        for col in temp_df.select_dtypes(include=['datetime64[ns]', 'datetime64[ns, UTC]']):
            temp_df[col] = temp_df[col].astype(str)

        patient_cases_json = temp_df.to_dict(orient="records")

        # Gender donut chart
        gender_counts = temp_df['patientgender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        gender_donut = px.pie(gender_counts, names='Gender', values='Count', title='Patient Gender Distribution', hole=0.4)
        gender_donut_html = gender_donut.to_html(full_html=False)

        # Age group bar chart
        age_bins = [0, 20, 40, 60, 80, 100]
        age_labels = ['1-20', '21-40', '41-60', '61-80', '81-100']
        temp_df['age_group'] = pd.cut(temp_df['patientage'], bins=age_bins, labels=age_labels, right=True)
        age_group_counts = temp_df['age_group'].value_counts().sort_index().reset_index()
        age_group_counts.columns = ['Age Group', 'Count']
        age_bar = px.bar(age_group_counts, x='Age Group', y='Count', title='Patient Age Distribution', color='Age Group')
        age_bar_html = age_bar.to_html(full_html=False)

        # ✅ Line chart: Number of cases over time based on diagnosisdatetime
        if 'diagnosisdatetime' in temp_df.columns:
            temp_df['diagnosis_date'] = pd.to_datetime(temp_df['diagnosisdatetime'], errors='coerce').dt.date
            daily_counts = temp_df.groupby('diagnosis_date').size().reset_index(name='Count')
            line_chart = px.line(daily_counts, x='diagnosis_date', y='Count', title='Patient Cases Over Time')
            line_chart_html = line_chart.to_html(full_html=False)
        else:
            line_chart_html = ""

    else:
        patient_cases_json = []
        gender_donut_html = ""
        age_bar_html = ""
        line_chart_html = ""

    return templates.TemplateResponse("index.html", {
        "request": request,
        **data,
        **facility_data,
        "patient_cases_json": json.dumps(patient_cases_json),
        "patient_gender_donut": gender_donut_html,
        "patient_age_bar": age_bar_html,
        "patient_cases_over_time_chart": line_chart_html  # ✅ Don't forget the comma here
    })




@app.get("/empty_map", response_class=HTMLResponse)
def empty_map():
    empty_map = KeplerGl(show_docs=False, height=450,read_only=True,width=900)
    empty_map.config=config
    return HTMLResponse(content=empty_map._repr_html_(), status_code=200)

@app.get("/map/facilities", response_class=HTMLResponse)
def map_facilities():
    facilities_df = pd.read_sql(query, engine)
    facilities_map = KeplerGl(height=450,read_only=True,width=900)
    facilities_map.add_data(data=facilities_df, name='All Facilities')
    facilities_map.config = config 
    return HTMLResponse(content=facilities_map._repr_html_(), status_code=200)

@app.get("/map/clinic", response_class=HTMLResponse)
def map_clinic():
    df = pd.read_sql(query, engine)
    clinic_df = df[df['amenity'].str.lower() == 'clinic']
    clinic_map = KeplerGl(height=450,read_only=True,width=900)
    clinic_map.add_data(data=clinic_df, name='Clinics Only')
    clinic_map.config = config
    return HTMLResponse(content=clinic_map._repr_html_(), status_code=200)

@app.get("/map/pharmacy", response_class=HTMLResponse)
def map_pharmacy():
    df = pd.read_sql(query, engine)
    pharmacy_df = df[df['amenity'].str.lower() == 'pharmacy']
    pharmacy_map = KeplerGl(height=450,read_only=True,width=900)
    pharmacy_map.add_data(data=pharmacy_df, name='Pharmacy Only')
    pharmacy_map.config = config
    return HTMLResponse(content=pharmacy_map._repr_html_(), status_code=200)

@app.get("/map/covid")
def covid_data():
    covid_map.config = config
    return HTMLResponse(content=covid_map._repr_html_(), status_code=200)
    
@app.get("/kpi/facilities")
def facility_kpi():
    df = pd.read_sql(query, engine)
    total_facilities = len(df)
    clinics = len(df[df['amenity'].str.lower() == 'clinic'])
    pharmacies = len(df[df['amenity'].str.lower() == 'pharmacy'])

    pie_fig = px.pie(
        names=['Clinics', 'Pharmacies'],
        values=[clinics, pharmacies],
        title='Facility Distribution',
        hole=0.3
    )

    return {
        "facility_total": total_facilities,
        "clinic_count": clinics,
        "pharmacy_count": pharmacies,
        "facility_donut_chart": pie_fig.to_html(full_html=False)
    }

# === Route for Polygon Map ===
@app.get("/map/polygon", response_class=HTMLResponse)
def map_polygon():
    html = generate_polygon_html()
    return HTMLResponse(content=html, status_code=200)


@app.get("/map/patientcases", response_class=HTMLResponse)
def map_patientcases(condition: str = Query(None)):
    global patient_cases_df

    if patient_cases_df is None:
        return HTMLResponse(content="<h3>Patient Cases Data Not Loaded.</h3>", status_code=500)

    filtered_df = patient_cases_df
    if condition:
        filtered_df = patient_cases_df[patient_cases_df['conditionname'].str.lower() == condition.lower()]

    patient_map = KeplerGl(height=450, read_only=True, width=900)
    patient_map.add_data(data=filtered_df, name="Patient Cases")

    patient_map.config = {
        "version": "v1",
        "config": {
            "mapState": {"latitude": 4.2105, "longitude": 101.9758, "zoom": 5},
            "visState": {
                "layers": [{
                    "id": "patient_layer",
                    "type": "point",
                    "config": {
                        "dataId": "Patient Cases",
                        "label": "Patient Cases",
                        "color": [255, 0, 0],
                        "columns": {"lat": "addresslatitude", "lng": "addresslongitude"},
                        "isVisible": True,
                        "visConfig": {"radius": 8, "opacity": 0.8, "filled": True}
                    }
                }],
                "interactionConfig": {
                    "tooltip": {
                        "fieldsToShow": {"Patient Cases": ["caseid", "patientname", "patientgender", "statename", "conditionname", "casestatus"]},
                        "enabled": True
                    }
                }
            }
        }
    }

    return HTMLResponse(content=patient_map._repr_html_(), status_code=200)

@app.get("/map/patientcases/{condition}", response_class=HTMLResponse)
def map_patientcases_condition(condition: str):
    global patient_cases_df

    if patient_cases_df is None:
        return HTMLResponse(content="<h3>Patient Cases Data Not Loaded.</h3>", status_code=500)

    filtered_df = patient_cases_df[patient_cases_df['conditionname'].str.lower() == condition.lower()]

    patient_map = KeplerGl(height=450, read_only=True, width=900)
    patient_map.add_data(data=filtered_df, name="Patient Cases")

    patient_map.config = {
        "version": "v1",
        "config": {
            "mapState": {"latitude": 4.2105, "longitude": 101.9758, "zoom": 5},
            "visState": {
                "layers": [{
                    "id": "patient_layer",
                    "type": "point",
                    "config": {
                        "dataId": "Patient Cases",
                        "label": "Patient Cases",
                        "color": [255, 0, 0],
                        "columns": {"lat": "addresslatitude", "lng": "addresslongitude"},
                        "isVisible": True,
                        "visConfig": {"radius": 8, "opacity": 0.8, "filled": True}
                    }
                }],
                "interactionConfig": {
                    "tooltip": {
                        "fieldsToShow": {"Patient Cases": ["caseid", "patientname", "patientgender", "statename", "conditionname", "casestatus"]},
                        "enabled": True
                    }
                }
            }
        }
    }

    return HTMLResponse(content=patient_map._repr_html_(), status_code=200)

@app.get("/kpi/patientcases")
def patientcases_kpi():
    df = pd.read_sql(patient_query, patient_engine)   # ❗ reload fresh data like facility_kpi

    # 👇 Add debug here
    print("==== Patient Cases Data ====")
    print(df[['caseid', 'casestatus']].head(20))  # show 20 rows only
    print("============================")

    submitted = len(df[df['casestatus'].str.lower() == "submitted"])
    closed = len(df[df['casestatus'].str.lower() == "closed"])
    not_submitted = len(df[df['casestatus'].str.lower() == "not submitted"])

    return {
        "submitted": submitted,
        "closed": closed,
        "not_submitted": not_submitted
    }

