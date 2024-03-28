import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns 
import pandas as pd
import requests
from pymongo import MongoClient

MONGO_URI= st.secrets.db_credentials.MONGO_URI
DB_NAME = st.secrets.db_credentials.DB_NAME
COLLECTION_NAME= st.secrets.db_credentials.COLLECTION_NAME

def mongo_to_pandas(mongo_uri, db_name, collection_name):
    """Connect to Mongo and convert fetched to pandas"""
    client = MongoClient(
        mongo_uri,
        # bypass connection errors
        tls=True,  
        tlsAllowInvalidCertificates=True  
    )

    db = client[db_name]
    collection = db[collection_name]
    
    docs= collection.find()
    df = pd.DataFrame(list(docs)) # Convert to Pandas


    client.close() # Close MongoDB connection

    return df

def handle_salary_range(salary_str):
    """Handle edge cases such as 40000-50000"""
    if '-' in salary_str:
        low, high = salary_str.split('-')
        return (float(low) + float(high)) / 2
    else:
        return salary_str


def data_analysis(dforiginal):
    """Return some metrics calculated from data"""
    df = dforiginal.copy()
    df = df.dropna(subset=['salary_per_year']) # Drop rows with NaN values
    mean_salary = df['salary_per_year'].mean()
    max_salary = df['salary_per_year'].max()
    min_salary = df['salary_per_year'].min()

    def clean_level(level):
        if "mid" in level:
            return "mid"
        else:
            return level

    level_counts = df.level.apply(clean_level).value_counts()
    wfh_counts = df.wfh.value_counts()


    return mean_salary, max_salary, min_salary, level_counts, wfh_counts

def geocode(query):
    """Convert location name to latitude, longitude"""
    url = 'https://nominatim.openstreetmap.org/search'
    headers = {
        'User-Agent': 'GeoLocator/1.2 (geolocator_support@example.com)',  
    }
    params = {
        'q': query,
        'format': 'json',
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        results = response.json()
        if results:
            first_result = results[0]
            return (float(first_result['lat']), float(first_result['lon']))
    return (55.3781, 3.4360)





st.set_page_config(layout="wide")
sns.set_style("darkgrid")

st.title("Data Engineering Indeed")

st.markdown("---")

df = mongo_to_pandas(MONGO_URI,DB_NAME,COLLECTION_NAME)
df['salary_per_year'] = df['salary_per_year'].apply(handle_salary_range)
df['salary_per_year'] = pd.to_numeric(df['salary_per_year'], errors='coerce')
df.loc[df['salary_per_year'] < 8000, 'salary_per_year'] = None


st.write(f"{len(df)} jobs found")
st.dataframe(df.style.highlight_max(axis=0))
st.markdown("---")

job_id = st.slider("Job slider",
						   min_value=0,
						   max_value=len(df) - 1
						   )

id, indeed_id,_, role_name, url, location, industry, job_type, wfh, company_name, salary_per_annum, summary, tech_stack, skills, level = df.iloc[job_id]

st.subheader(f"{role_name} at {company_name}")
with st.container():
    
    # Use columns to layout the content in 3 columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border = False):
            
            st.write(f'**Summary:** {summary}')
            st.write(f'**Id:** {id}')
            st.write(f'**Indeed ID:** {indeed_id}')
            st.write(f'**Location:** {location}')
            st.write(f'**Industry:** {industry}')
            st.write(f'**Job Type:** {job_type}')
            st.write(f'**WFH:** {wfh}')
            st.write(f'**URL:** {url}')

    with col2:
        with st.container(border = False):
            st.write(f'**Salary per Annum:** {salary_per_annum}')
            
            st.write(f'**Tech Stack:** {tech_stack}')
            st.write(f'**Skills:** {skills}')
            st.write(f'**Level:** {level}')
    
    with col3:
        with st.container(border = False):
            lat, long = geocode(location)
            map_data = pd.DataFrame({
                'lat': [lat],
                'lon': [long]
            })

            st.map(map_data)    

    st.markdown("---")



mean_salary, max_salary, min_salary, level_counts, wfh_counts = data_analysis(df)
# st.write(f"Mean salary: {mean_salary}")
# st.write(f"Lowest salary: {min_salary}")
# st.write(f"Highest salary: {max_salary}")

salary_data = pd.DataFrame({
	            'job': ['Lowest', "Current", 'Average'],
	            'Salary': [min_salary, salary_per_annum, mean_salary]
               })





tech_lists = df['tech_stack'].str.lower().str.strip().str.split(', ')
filtered_tech_lists = [[tech for tech in sublist if tech not in ['na', 'n/a', 'none', '']] for sublist in tech_lists]
filtered_tech_lists = [tech for sublist in filtered_tech_lists for tech in sublist]
filtered_tech_lists = pd.Series(filtered_tech_lists)
top_techs_filtered = filtered_tech_lists.value_counts().head(10)

skill_lists = df['skills'].str.lower().str.strip().str.split(', ')
filtered_skill_lists = [[tech for tech in sublist if tech not in ['na', 'n/a', 'none', '']] for sublist in skill_lists]
filtered_skill_lists = [tech for sublist in filtered_skill_lists for tech in sublist]
filtered_skill_lists = pd.Series(filtered_skill_lists)
skill_lists_filtered = filtered_skill_lists.value_counts().head(10)

with st.container():
    st.subheader("Salary comparison")
    st.bar_chart(data = salary_data,
        x = 'job',
        y = 'Salary')   


with st.container():
    col5, _, col6 = st.columns(3)

    with col5:
        st.subheader("Top tech stack")
        st.write(top_techs_filtered)
    with col6:
        st.subheader("Top skills")
        st.write(skill_lists_filtered)

