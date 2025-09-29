import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
from plotly.subplots import make_subplots
import json
from datetime import datetime
import pytz
from flask import Flask, render_template, jsonify, request
import re

app = Flask(__name__)

# Load the datasets
apps_df = pd.read_csv('Play-Store-Data.csv')
reviews_df = pd.read_csv('User Reviews.csv')

# Data cleaning
def clean_data():
    global apps_df, reviews_df

    # Convert Rating to numeric, force errors to NaN
    apps_df['Rating'] = pd.to_numeric(apps_df['Rating'], errors='coerce')
    
    # Now drop rows with missing Rating
    apps_df = apps_df.dropna(subset=['Rating'])

    for column in apps_df.columns:
        if apps_df[column].dtype != 'object':
            apps_df[column] = apps_df[column].fillna(apps_df[column].median())
        else:
            apps_df[column] = apps_df[column].fillna(apps_df[column].mode()[0] if not apps_df[column].mode().empty else '')
    
    # Drop duplicates
    apps_df.drop_duplicates(inplace=True)
    
    # Filter valid ratings (<=5)
    apps_df = apps_df[apps_df['Rating'] <= 5]
    
    # Clean reviews data
    reviews_df.dropna(subset=['Translated_Review'], inplace=True)
    
    # Convert installs to numeric
    apps_df['Installs'] = apps_df['Installs'].str.replace('[+,]', '', regex=True)
    apps_df['Installs'] = pd.to_numeric(apps_df['Installs'], errors='coerce')
    
    # Convert size to numeric (MB)
    apps_df['Size'] = apps_df['Size'].apply(lambda x: float(str(x).replace('M', '')) if 'M' in str(x) else
                                           (float(str(x).replace('k', '')) / 1024 if 'k' in str(x) else np.nan))
    
    # Convert price to numeric
    apps_df['Price'] = apps_df['Price'].str.replace('$', '', regex=False).astype(float)
    
    # Extract Android version as numeric
    apps_df['Android_Ver_Number'] = apps_df['Android Ver'].str.extract(r'(\d+\.\d+)').astype(float)
    
    # Convert reviews to numeric
    apps_df['Reviews'] = pd.to_numeric(apps_df['Reviews'], errors='coerce')
    
    # Parse last updated date
    apps_df['Last_Updated_Date'] = pd.to_datetime(apps_df['Last Updated'], format='%B %d, %Y', errors='coerce')
    apps_df['Last_Updated_Month'] = apps_df['Last_Updated_Date'].dt.month_name()
    
    # Merge apps and reviews data
    merged_df = pd.merge(apps_df, reviews_df, on='App', how='left')
    
    return apps_df, reviews_df, merged_df


# Clean the data
apps_df, reviews_df, merged_df = clean_data()

# Function to check if current time is within specified range (IST)
def is_time_in_range(start_hour, end_hour):
    # Production version with actual time restrictions
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    current_hour = current_time.hour
    return start_hour <= current_hour < end_hour
    
    # For testing, uncomment below to always return True
    # return True

# Chart 1: Grouped bar chart for top 10 app categories
def generate_chart1():
    if not is_time_in_range(15, 17):  # 3PM to 5PM IST
        return {"visible": False}
    
    # Filter data
    filtered_df = apps_df[
        (apps_df['Rating'] >= 4.0) & 
        (apps_df['Size'] > 10) & 
        (apps_df['Last_Updated_Month'] == 'January')
    ]
    
    # Group by category and calculate metrics
    category_stats = filtered_df.groupby('Category').agg({
        'Rating': 'mean',
        'Reviews': 'sum',
        'Installs': 'sum'
    }).reset_index()
    
    # Get top 10 categories by installs
    top_categories = category_stats.sort_values('Installs', ascending=False).head(10)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_categories['Category'],
        y=top_categories['Rating'],
        name='Average Rating',
        marker_color='#4285F4',
        opacity=0.8
    ))
    
    fig.add_trace(go.Bar(
        x=top_categories['Category'],
        y=top_categories['Reviews'] / 1000,  # Scale down for better visualization
        name='Total Reviews (thousands)',
        marker_color='#EA4335',
        opacity=0.8
    ))
    
    fig.update_layout(
        title='Top 10 App Categories: Average Rating vs Total Reviews',
        xaxis_title='Category',
        yaxis_title='Value',
        barmode='group',
        legend=dict(x=0.01, y=0.99),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    )
    
    # Convert to JSON and parse back to ensure proper format
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return json.loads(graphJSON)

# Chart 2: Choropleth map for global installs by category
def generate_chart2(filter_type=None):
    if not is_time_in_range(18, 20):  # 6PM to 8PM IST
        return {"visible": False}
    
    # Get filter type from request args if not provided
    from flask import request
    if filter_type is None and request.args.get('filter'):
        filter_type = request.args.get('filter')
    
    # Define different filter options
    if filter_type == 'popular':
        # Filter for popular categories (high installs)
        filtered_categories = apps_df[apps_df['Installs'] > 5000000]
    elif filter_type == 'highrated':
        # Filter for high-rated categories
        filtered_categories = apps_df[apps_df['Rating'] >= 4.5]
    elif filter_type == 'trending':
        # Filter for recently updated apps
        filtered_categories = apps_df[apps_df['Last_Updated_Date'] > pd.Timestamp('2018-01-01')]
    else:
        # Default filter - categories that don't start with A, C, G, or S
        filtered_categories = apps_df[~apps_df['Category'].str.startswith(('A', 'C', 'G', 'S'))]
    
    # Group by category and calculate total installs
    category_installs = filtered_categories.groupby('Category').agg({
        'Installs': 'sum',
        'Rating': 'mean',
        'Reviews': 'sum'
    }).reset_index()
    
    # Filter categories with more than 1 million installs
    category_installs = category_installs[category_installs['Installs'] > 1000000]
    
    # Get top 5 categories by installs
    top_categories = category_installs.sort_values('Installs', ascending=False).head(5)
    
    # Create a more detailed dataset for the choropleth
    # Map categories to countries with the highest market share (simulated data)
    countries = ['United States', 'India', 'Brazil', 'United Kingdom', 'Germany', 'Japan', 'Russia', 
                'Canada', 'Australia', 'France', 'Mexico', 'Indonesia', 'Italy', 'South Korea', 'Spain']
    
    # Create expanded dataset with multiple countries per category
    choropleth_data = []
    for idx, category in enumerate(top_categories['Category']):
        installs = top_categories.iloc[idx]['Installs']
        rating = top_categories.iloc[idx]['Rating']
        # Distribute installs across countries with some variation
        for i, country in enumerate(countries[:10]):  # Use top 10 countries
            # Create a distribution that decreases with country index
            country_factor = 1 - (i * 0.08)  # Decreasing factor
            country_installs = int(installs * country_factor / 5)  # Divide by 5 to distribute
            choropleth_data.append({
                'Country': country,
                'Category': category,
                'Installs': country_installs,
                'Rating': rating,
                'Market_Share': country_factor * 20  # Convert to percentage
            })
    
    choropleth_df = pd.DataFrame(choropleth_data)
    
    # Create enhanced choropleth map
    fig = px.choropleth(
        choropleth_df,
        locations='Country',
        locationmode='country names',
        color='Installs',
        hover_name='Category',
        hover_data=['Rating', 'Market_Share'],
        color_continuous_scale='Viridis',
        projection='natural earth',  # More modern projection
        title='Global Installs by Category (Top 5)',
        labels={
            'Installs': 'Number of Installs',
            'Rating': 'Average Rating',
            'Market_Share': 'Market Share (%)'
        }
    )
    
    fig.update_layout(
        geo=dict(
            showframe=True,
            framecolor='rgba(255, 255, 255, 0.3)',
            showcoastlines=True,
            coastlinecolor='rgba(255, 255, 255, 0.5)',
            showland=True,
            landcolor='rgba(80, 80, 80, 0.2)',
            showcountries=True,
            countrycolor='rgba(255, 255, 255, 0.3)',
            projection_type='natural earth',
            bgcolor='rgba(0, 0, 0, 0)'
        ),
        coloraxis_colorbar=dict(
            title='Installs',
            tickprefix='',
            ticksuffix='',
            len=0.8,  # Make colorbar shorter
            thickness=15,  # Make colorbar thicker
            outlinecolor='rgba(255, 255, 255, 0.3)'
        ),
        margin={"r":0,"t":50,"l":0,"b":0},  # Reduce margins for better responsiveness
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        dragmode=False  # Disable drag mode for better mobile experience
    )
    
    # Add annotations for top markets
    for i, row in choropleth_df.sort_values('Installs', ascending=False).head(3).iterrows():
        fig.add_annotation(
            x=0.5,  # Centered at the bottom
            y=-0.12,  # Below the map
            xref='paper',
            yref='paper',
            text=f"Top Market: {row['Country']} - {row['Category']} ({int(row['Market_Share'])}% market share)",
            showarrow=False,
            font=dict(size=12, color='#bb86fc'),
            align='center',
            bgcolor='rgba(37, 37, 37, 0.7)',
            bordercolor='rgba(255, 255, 255, 0.3)',
            borderwidth=1,
            borderpad=4,
            opacity=0.8
        )
        break  # Just add one annotation to avoid clutter
    
    # Convert to JSON and parse back to ensure proper format
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return json.loads(graphJSON)

# Chart 3: Dual-axis chart comparing installs and revenue
def generate_chart3():
    if not is_time_in_range(13, 14):  # 1PM to 2PM IST
        return {"visible": False}
    
    # Filter data
    filtered_df = apps_df[
        (apps_df['Installs'] >= 10000) &
        (apps_df['Price'] * apps_df['Installs'] >= 10000) &  # Estimated revenue
        (apps_df['Android_Ver_Number'] > 4.0) &
        (apps_df['Size'] > 15) &
        (apps_df['Content Rating'] == 'Everyone') &
        (apps_df['App'].str.len() <= 30)
    ]
    
    # Get top 3 categories by installs
    top_categories = filtered_df.groupby('Category')['Installs'].sum().nlargest(3).index.tolist()
    category_df = filtered_df[filtered_df['Category'].isin(top_categories)]
    
    # Group by category and type (free vs paid)
    grouped_df = category_df.groupby(['Category', 'Type']).agg({
        'Installs': 'mean',
        'Price': lambda x: (x * category_df.loc[x.index, 'Installs']).mean()  # Average revenue
    }).reset_index()
    
    # Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    for category in top_categories:
        category_data = grouped_df[grouped_df['Category'] == category]
        
        fig.add_trace(
            go.Bar(
                x=[f"{category} ({row['Type']})" for _, row in category_data.iterrows()],
                y=category_data['Installs'],
                name=f"{category} - Installs",
                marker_color=['#4285F4' if t == 'Free' else '#34A853' for t in category_data['Type']],
                opacity=0.8
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=[f"{category} ({row['Type']})" for _, row in category_data.iterrows()],
                y=category_data['Price'],
                name=f"{category} - Revenue",
                marker_color=['#FBBC05' if t == 'Free' else '#EA4335' for t in category_data['Type']],
                mode='markers+lines',
                marker=dict(size=10)
            ),
            secondary_y=True
        )
    
    fig.update_layout(
        title='Average Installs vs Revenue: Free vs Paid Apps (Top 3 Categories)',
        xaxis_title='Category and Type',
        barmode='group',
        legend=dict(x=0.01, y=0.99),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    )
    
    fig.update_yaxes(title_text="Average Installs", secondary_y=False)
    fig.update_yaxes(title_text="Average Revenue ($)", secondary_y=True)
    
    # Convert to JSON and parse back to ensure proper format
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return json.loads(graphJSON)

# Chart 4: Time series line chart for installs over time
def generate_chart4():
    if not is_time_in_range(18, 21):  # 6PM to 9PM IST
        return {"visible": False}
    
    # Filter data
    filtered_df = apps_df[
        (~apps_df['App'].str.startswith(('X', 'Y', 'Z'), na=False)) &
        (apps_df['Category'].str.startswith(('E', 'C', 'B'), na=False)) &
        (apps_df['Reviews'] > 500) &
        (~apps_df['App'].str.contains('S', na=False))
    ]
    
    # Create a time series by using the Last_Updated_Date
    filtered_df = filtered_df.sort_values('Last_Updated_Date')
    
    # Group by category and date
    time_series = filtered_df.groupby(['Category', pd.Grouper(key='Last_Updated_Date', freq='M')])['Installs'].sum().reset_index()
    
    # Calculate month-over-month growth
    time_series['MoM_Growth'] = time_series.groupby('Category')['Installs'].pct_change() * 100
    
    # Translate category names
    category_translations = {
        'BEAUTY': 'सौंदर्य',  # Hindi
        'BUSINESS': 'வணிகம்',  # Tamil
        'DATING': 'Dating'  # German (same as English)
    }
    
    time_series['Category_Translated'] = time_series['Category'].map(
        lambda x: category_translations.get(x, x)
    )
    
    # Create time series chart
    fig = go.Figure()
    
    for category in time_series['Category'].unique():
        category_data = time_series[time_series['Category'] == category]
        translated_name = category_translations.get(category, category)
        
        fig.add_trace(go.Scatter(
            x=category_data['Last_Updated_Date'],
            y=category_data['Installs'],
            mode='lines+markers',
            name=translated_name,
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        # Highlight significant growth periods
        growth_periods = category_data[category_data['MoM_Growth'] > 20]
        if not growth_periods.empty:
            fig.add_trace(go.Scatter(
                x=growth_periods['Last_Updated_Date'],
                y=growth_periods['Installs'],
                fill='tozeroy',
                mode='none',
                name=f'{translated_name} Growth >20%',
                fillcolor='rgba(231, 76, 60, 0.3)'
            ))
    
    fig.update_layout(
        title='Total Installs Over Time by App Category',
        xaxis_title='Date',
        yaxis_title='Total Installs',
        legend=dict(x=0.01, y=0.99),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    )
    
    # Convert to JSON and parse back to ensure proper format
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return json.loads(graphJSON)

# Chart 5: Bubble chart for app size vs rating (based on Tkinter logic)
def generate_chart5():
    if not is_time_in_range(17, 19):  # 5PM to 7PM IST
        return {"visible": False}
    
    # Filter data based on Tkinter logic
    categories_to_keep = [
        'GAME', 'BEAUTY', 'BUSINESS', 'COMICS', 'COMMUNICATION',
        'DATING', 'ENTERTAINMENT', 'SOCIAL', 'EVENT'
    ]
    
    filtered_df = apps_df[
        (apps_df['Category'].str.upper().isin(categories_to_keep)) &
        (apps_df['App'].str.lower().str.contains('s') == False) &
        (apps_df['Reviews'].astype(float) > 500) &
        (apps_df['Rating'].astype(float) > 3.5)
    ]
    
    # Convert installs to numeric as in Tkinter code
    filtered_df['InstallsInt'] = filtered_df['Installs'].apply(
        lambda val: int(str(val).replace('+','').replace(',','')) if isinstance(val, str) else val
    )
    filtered_df = filtered_df[filtered_df['InstallsInt'] > 50000]
    
    # Convert Size to MB as in Tkinter code
    filtered_df['SizeMB'] = filtered_df['Size'].apply(
        lambda x: float(str(x).replace('M','')) if 'M' in str(x) else 
                (float(str(x).replace('k',''))/1024 if 'k' in str(x) else np.nan)
    )
    
    # Filter by sentiment subjectivity as in Tkinter code
    reviews_high = reviews_df[reviews_df['Sentiment_Subjectivity'].astype(float) > 0.5]
    app_list_subj = set(reviews_high['App'])
    filtered_df = filtered_df[filtered_df['App'].isin(app_list_subj)]
    
    # Translate category names as in Tkinter code
    category_translations = {
        "BEAUTY": "सौंदर्य", # Hindi
        "BUSINESS": "வணிகம்", # Tamil
        "DATING": "Dating (German: Dating)" # German
    }
    
    filtered_df['Category_Translated'] = filtered_df['Category'].apply(
        lambda cat: category_translations.get(cat.upper(), cat) if isinstance(cat, str) else cat
    )
    
    # Create bubble chart with Tkinter-like styling
    fig = px.scatter(
        filtered_df.dropna(subset=['SizeMB', 'Rating', 'InstallsInt']),
        x='SizeMB',
        y='Rating',
        size='InstallsInt',
        color='Category_Translated',
        hover_name='App',
        size_max=60,
        opacity=0.7,
        title='App Size vs Rating (Bubble Size = Installs)',
        labels={
            'SizeMB': 'App Size (MB)',
            'Rating': 'Average Rating',
            'InstallsInt': 'Number of Installs',
            'Category_Translated': 'Category'
        },
        hover_data={
            'InstallsInt': True,
            'SizeMB': ':.2f',
            'Rating': ':.2f',
            'Reviews': True
        },
        height=500,  # Set a fixed height for better rendering
        width=800    # Set a width that will be adjusted by responsive config
    )
    
    # Color bubbles based on Tkinter logic - GAME in pink, others in blue
    for i, d in enumerate(fig.data):
        # Add border to all bubbles for better visibility
        fig.data[i].marker.line = dict(width=1, color='rgba(255,255,255,0.3)')
        
        # Apply Tkinter-like coloring
        if 'GAME' in d.name:
            fig.data[i].marker.color = 'hotpink'
            fig.data[i].marker.line = dict(width=1.5, color='black')
        else:
            fig.data[i].marker.color = 'dodgerblue'
            fig.data[i].marker.line = dict(width=1.5, color='black')
    
    # Add category labels at bubble centers as in Tkinter code
    for trace in fig.data:
        for i, txt in enumerate(trace.hovertext):
            fig.add_annotation(
                x=trace.x[i],
                y=trace.y[i],
                text=trace.name,
                showarrow=False,
                font=dict(
                    size=9,
                    color='white' if 'GAME' in trace.name else 'black',
                    family='Arial',
                    weight='bold'
                )
            )
    
    fig.update_layout(
        xaxis=dict(
            title='App Size (MB)',
            autorange=True,
            fixedrange=False,
            showgrid=True,
            gridcolor='rgba(80,80,80,0.2)',
            zeroline=False,
            showline=True,
            linecolor='rgba(80,80,80,0.4)',
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title='Average Rating',
            autorange=True,
            fixedrange=False,
            showgrid=True,
            gridcolor='rgba(80,80,80,0.2)',
            zeroline=False,
            showline=True,
            linecolor='rgba(80,80,80,0.4)',
            tickfont=dict(size=10)
        ),
        legend=dict(
            title='Category',
            orientation='v',
            yanchor='top',
            y=0.99,
            xanchor='right',
            x=0.99,
            font=dict(size=10),
            bgcolor='rgba(0,0,0,0.1)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1,
            itemsizing='constant'
        ),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        dragmode='zoom',
        hovermode='closest',
        margin=dict(l=50, r=20, t=50, b=50),
        hoverlabel=dict(
            bgcolor='rgba(50,50,50,0.8)',
            font_size=12,
            font_family='Arial',
            bordercolor='rgba(255,255,255,0.3)',
            namelength=-1  # Show full names
        )
    )
    
    # Add custom legend like in Tkinter code
    fig.update_layout(
        annotations=[
            dict(
                x=0.01,
                y=0.01,
                xref="paper",
                yref="paper",
                text="Filters: Rating > 3.5, Selected categories, Reviews > 500, App name without 'S', Sentiment subjectivity > 0.5, Installs > 50K. Translations: Beauty (Hindi), Business (Tamil), Dating (German). Game category highlighted in pink.",
                showarrow=False,
                font=dict(size=10, color="#b3b3b3"),
                align="left",
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="rgba(255,255,255,0.2)",
                borderwidth=1,
                borderpad=4,
                width=500
            )
        ],
        # Add modebar buttons for better zoom control
        modebar=dict(
            orientation='v',
            bgcolor='rgba(0,0,0,0)',
            color='#bb86fc',
            activecolor='#d0b3fc'
        ),
        updatemenus=[
            dict(
                type='buttons',
                showactive=False,
                buttons=[
                    dict(
                        label='Reset Zoom',
                        method='relayout',
                        args=[{'xaxis.autorange': True, 'yaxis.autorange': True}]
                    )
                ],
                x=0.05,
                y=1.05,
                xanchor='left',
                yanchor='top',
                bgcolor='rgba(0,0,0,0.1)',
                bordercolor='rgba(255,255,255,0.2)',
                font=dict(color='#ffffff', size=10)
            )
        ]
    )
    
    # Convert to JSON and parse back to ensure proper format
    chart_json = json.loads(fig.to_json())
    return jsonify(chart_json)

# Chart 6: Stacked area chart for cumulative installs
def generate_chart6():
    if not is_time_in_range(16, 18):  # 4PM to 6PM IST
        return {"visible": False}
    
    # Filter data
    filtered_df = apps_df[
        (apps_df['Rating'] >= 4.2) &
        (~apps_df['App'].str.contains(r'\d', regex=True, na=False)) &
        (apps_df['Category'].str.startswith(('T', 'P'), na=False)) &
        (apps_df['Reviews'] > 1000) &
        (apps_df['Size'] >= 20) &
        (apps_df['Size'] <= 80)
    ]
    
    # Create a time series by using the Last_Updated_Date
    filtered_df = filtered_df.sort_values('Last_Updated_Date')
    
    # Group by category and date
    time_series = filtered_df.groupby(['Category', pd.Grouper(key='Last_Updated_Date', freq='M')])['Installs'].sum().reset_index()
    
    # Calculate cumulative installs
    time_series['Cumulative_Installs'] = time_series.groupby('Category')['Installs'].cumsum()
    
    # Calculate month-over-month growth
    time_series['MoM_Growth'] = time_series.groupby('Category')['Installs'].pct_change() * 100
    
    # Translate category names
    category_translations = {
        'TRAVEL_AND_LOCAL': 'Voyage et Local',  # French
        'PRODUCTIVITY': 'Productividad',  # Spanish
        'PHOTOGRAPHY': '写真'  # Japanese
    }
    
    time_series['Category_Translated'] = time_series['Category'].map(
        lambda x: category_translations.get(x, x)
    )
    
    # Create stacked area chart
    fig = px.area(
        time_series,
        x='Last_Updated_Date',
        y='Cumulative_Installs',
        color='Category_Translated',
        line_group='Category',
        title='Cumulative Installs Over Time by App Category',
        labels={
            'Last_Updated_Date': 'Date',
            'Cumulative_Installs': 'Cumulative Installs',
            'Category_Translated': 'Category'
        }
    )
    
    # Highlight months with significant growth
    high_growth = time_series[time_series['MoM_Growth'] > 25]
    if not high_growth.empty:
        for category in high_growth['Category'].unique():
            category_data = high_growth[high_growth['Category'] == category]
            translated_name = category_translations.get(category, category)
            
            fig.add_trace(go.Scatter(
                x=category_data['Last_Updated_Date'],
                y=category_data['Cumulative_Installs'],
                mode='markers',
                marker=dict(size=10, color='red'),
                name=f'{translated_name} Growth >25%'
            ))
    
    fig.update_layout(
        xaxis=dict(title='Date'),
        yaxis=dict(title='Cumulative Installs'),
        legend=dict(title='Category'),
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff')
    )
    
    # Convert to JSON and parse back to ensure proper format
    chart_json = json.loads(fig.to_json())
    return jsonify(chart_json)

# Routes
@app.route('/')
def index():
    # Pass developer info to the template
    developer_info = {
        'name': 'METHELESH KUMAR RATTU',
        'portfolio': 'https://metheleshrattu.viversed.com/',
        'current_date': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %B %Y'),
        'logo_url': 'https://images.indianexpress.com/2022/07/Google-Play-Store-new-logo.jpg'
    }
    return render_template('index.html', developer_info=developer_info)

@app.route('/api/charts/1')
def chart1_data():
    return generate_chart1()

@app.route('/api/charts/2')
def chart2_data():
    # Get filter parameter from request
    filter_type = request.args.get('filter', None)
    return generate_chart2(filter_type)

@app.route('/api/charts/3')
def chart3_data():
    return generate_chart3()

@app.route('/api/charts/4')
def chart4_data():
    return generate_chart4()

@app.route('/api/charts/5')
def chart5_data():
    return generate_chart5()

@app.route('/api/charts/6')
def chart6_data():
    return generate_chart6()

@app.route('/api/current-time')
def current_time():
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    return jsonify({
        'time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
        'hour': current_time.hour,
        'minute': current_time.minute
    })

if __name__ == '__main__':
    app.run(debug=True)