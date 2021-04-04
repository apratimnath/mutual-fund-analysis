# Mutual Fund Analysis
### Python (Flask) App, majorly for Backend APIs for Individual Mutual Fund Investment Analysis


## Problem Statement
Over the years, investors have tried and tested various methodologies to keep a track of all investements.
The various problems faced for the same are -

1. Multi-vendor - The Mutual Funds are invested via multiple vendors, like Groww, Paytm Money, etc., hence no unified interface to track all investments.
2. The historic data is not accurately predicted - Over time the historic data loses importance and is overriden to be fitted only in Time Series Graph.
3. Periodic Tracking of data - Everyday net change in the invested amount.
4. Personalized Prediction - Currently all Mutual Fund Predictions are not personalized, only based on overall NAV chnages.
5. Finance Analysis - Track the monthly Income and Expenditures based on`Money Manager`. 
5. Alexa Skills - The Day-to-Day change for Mutual Funds & Month-on-Month change for expenses and income re now available over Alexa skills.

## Google Colaboratory Notebooks
1. RNN Prediction for upcoming trends in the funds (Step-forward) - [Link to notebook](https://colab.research.google.com/drive/1JKrulU9pEz3Z38gI7SY6wUmX0y6vOxxW?usp=sharing)
2. RGeneral calculations for MF Analysis - [Link to notebook](https://colab.research.google.com/drive/11DPecNi8eduuYcyNLmBInc40vM1iEpGq?usp=sharing)

## API Sets
The app will consist of two major sets of API -

1. Current Data - Various APIs to fetch the current investment data details to be show in the Current Investment Dashboard
2. Prediction Data - Will predict the futur return, both overall, and per-investment basis, based on the user investment trend (will be available, only when the current dataset reached significant entires)
3. Personal Finance APIs - Get the MoM changes for expenditure, Calculate the overall expenditure change every Month (SUM, MEAN & STD), Get All the Month Names, For each month get the different categories of expenditure and income, For each month get the Top 5 Spend Categories (Grouped Column Chart), Get the sum change of income and expenditure every month"

## Data collection, Storage and Analysis Blueprint
Data from differen apps will be collected in the following way -

1. Per day data of return is manually entered in Google Sheet.
2. The data from the Google Sheet is fetched in Python, and stored in a MySQL DB. Data fetching happens everyday, at 11:00 a.m.
3. Success or failure mails for everyday update is triggered based on the storage of data in the respective database.
4. APIs expose the various data, grouped by various factors to be used in the UI.
5. Once the stored data crosses a significant volume, this data is splitted into train and test data for future analysis.
6. The predicted data is again exposed over APIs, grouped by various factors.

## Deployment

Deployed using Heroku.

## Attaching to Heroku Repository

1. heroku git:remote -a mf-analysis-backend
2. git pull heroku main
3. git push heroku main
