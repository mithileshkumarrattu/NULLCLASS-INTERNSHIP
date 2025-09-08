# NULLCLASS-INTERNSHIP

Here's a sample README.md file for your Google Play Store Data Analysis Project, covering all important aspects. It references code structure, required files (such as your notebooks and CSV), and outlines how to use/run the code. You should place this file (README.md) at the root of your GitHub project directory, ensuring the example commands match your actual setup.

***

# Google Play Store Data Analysis Dashboard

This project provides a comprehensive analysis, visualization, and prediction toolkit for the Google Play Store dataset.
It features:
- Interactive dashboards (Tkinter),
- Data cleaning & transformation,
- Visual analytics (matplotlib, seaborn),
- Sentiment analysis of user reviews,
- Machine learning models for rating prediction.

***

## 🚀 Features

- **Data Cleaning & Transformation:** Handles missing values, formats numerical columns, and normalizes app size and installation numbers.  
- **Dashboards with Tkinter:** Multiple Tkinter apps present interactive matplotlib/seaborn visualizations for exploring categories, type, reviews, sentiment, installs, last update, revenue, genres, and more.  
- **Sentiment Analysis:** Analyzes user reviews using NLTK’s VADER sentiment tool.  
- **ML Regression:** Predict app ratings based on reviews, installs, and price using Random Forest Regression.  
- **Grouped Bar/Choropleth (Bonus):** Specialized time-gated dashboards for grouped bar and global choropleth visualizations based on category, installs, etc.

***

## 📁 Repository Structure

```
.
├── Analysis.ipynb          # Main analysis notebook (data prep, dashboard, ML)
├── Tasks.ipynb             # Specialized dashboard: Grouped bar, time-gated, etc.
├── Play-Store-Data.csv     # Main dataset (Google Play store apps)
├── User-Reviews.csv        # User reviews with sentiment
├── results/                # (Recommended) Place for screenshots, exports
└── README.md               # This file
```

***

## 🔧 Getting Started

### Prerequisites

- Python 3.8+
- Packages: pandas, numpy, matplotlib, seaborn, scikit-learn, nltk, tkinter, pytz, plotly, Pillow
- (For sentiment): nltk's VADER (downloads automatically)


### First time NLTK setup
The code downloads the `vader_lexicon` automatically, but you can run this manually in Python if needed:
```python
import nltk
nltk.download('vader_lexicon')
```
***

## 🏁 Running the Dashboards

### Main Dashboard (multi-viz, ML)
```bash
python Analysis.ipynb
```
Or open in Jupyter and run all cells.  
This provides dashboards on:
- Top categories, distribution by type (free/paid)
- Rating histogram & sentiment pie, 
- Installs by category, app update history,
- Revenue, top genres, boxplots by year/type, 
- ML regression visualization.

### Grouped Bar/Choropleth Dashboards (time-gated)
```bash
python Tasks.ipynb
```
- The grouped bar dashboard: visible only between 3–5 PM IST (see code).
- The advanced choropleth map: available 6–8 PM IST (see code).



## 📊 Notebook Previews

Notebooks include:
- Data exploration
- Cleaning code
- Visualizations (matplotlib, seaborn)
- Sentiment analysis steps (VADER)
- Model building & evaluation (RandomForestRegressor)
- Dashboard logic (Tkinter)

_For a fuller experience, run notebooks locally with Jupyter._

***

## 📄 Data Sources

- `Play-Store-Data.csv`: Store apps metadata (category, rating, price, installs, etc)
- `User-Reviews.csv`: Translated user reviews, sentiments



- [NLTK](https://www.nltk.org/) VADER sentiment analysis  
- [Matplotlib](https://matplotlib.org/), [Seaborn](https://seaborn.pydata.org/)
- [scikit-learn](https://scikit-learn.org/)
- Icons and category titles: Google Play Store Public Data


***
