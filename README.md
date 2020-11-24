# Mutual Fund Analysis
### Python (Flask) App, majorly for Backend APIs for Individual Mutual Fund Investment Analysis


## Problem Statement
Over the years, investors have tried and tested various methodologies to keep a track of all investements.
The various problems faced for the same are -

1. Multi-vendor - The Mutual Funds are invested via multiple vendors, like Groww, Paytm Money, etc., hence no unified interface to track all investments.
2. The historic data is not accurately predicted - Over time the historic data loses importance and is overriden to be fitted only in Time Series Graph.
3. Periodic Tracking of data - Everyday net change in the invested amount.
4. Personalized Prediction - Currently all Mutual Fund Predictions are not personalized, only based on overall NAV chnages.

## API Sets
The app will consist of two major sets of API -

1. Current Data - Various APIs to fetch the current investment data details to be show in the Current Investment Dashboard
2. Prediction Data - Will predict the futur return, both overall, and per-investment basis, based on the user investment trend (will be available, only when the current dataset reached significant entires)

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
