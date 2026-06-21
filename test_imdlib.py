import imdlib as imd
import numpy as np
import pandas as pd
import os

# -------------------------------------------------
# 1. Parameters
# -------------------------------------------------
variable = 'rain'          # 'rain', 'tmin' or 'tmax'
start_yr = 2015            # Start year for time travel
end_yr = 2024              # End year for time travel
data_dir = './data'

# -------------------------------------------------
# 2. Create data directory
# -------------------------------------------------
os.makedirs(data_dir, exist_ok=True)

# -------------------------------------------------
# 3. Download and process multiple years
# -------------------------------------------------
all_years_df = []

for year in range(start_yr, end_yr + 1):
    print(f"\n{'='*50}")
    print(f"Processing year {year}...")
    print(f"{'='*50}")
    
    # Download if not exists
    if not os.path.exists(f"{data_dir}/{year}.grd"):
        print(f"  Downloading {year}...")
        imd.get_data(variable, year, year, fn_format='yearwise', file_dir=data_dir)
        print(f"  ✅ Download complete.")
    else:
        print(f"  ✅ Year {year} already downloaded.")
    
    # Open the data
    data = imd.open_data(variable, year, year, fn_format='yearwise', file_dir=data_dir)
    rainfall = data.data
    rainfall[rainfall == -999.0] = np.nan
    
    # Get dimensions
    time_steps, lats, lons = rainfall.shape
    print(f"  Data shape: {time_steps} days, {lats} lat points, {lons} lon points")
    
    # Days per month (adjust for leap year)
    if year % 4 == 0:
        days_per_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        print(f"  {year} is a leap year")
    else:
        days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Aggregate to monthly averages
    monthly_rain = []
    month_start = 0
    for month_days in days_per_month:
        month_end = month_start + month_days
        if month_end <= time_steps:
            month_data = rainfall[month_start:month_end, :, :]
            month_mean = np.nanmean(month_data, axis=0)
            monthly_rain.append(month_mean)
        month_start = month_end
    
    monthly_rain = np.array(monthly_rain)
    print(f"  Monthly data shape: {monthly_rain.shape}")
    
    # Get lat/lon (use approximate ranges)
    lat = np.linspace(6.5, 38.5, lats)
    lon = np.linspace(66.5, 100.5, lons)
    
    # Build DataFrame
    rows = []
    for t in range(12):  # months
        for i in range(lats):
            for j in range(lons):
                val = monthly_rain[t, i, j]
                if not np.isnan(val):
                    lat_val = lat[i]
                    lon_val = lon[j]
                    rows.append({
                        'year': year,
                        'lat': lat_val,
                        'lon': lon_val,
                        'month': t + 1,
                        'rainfall': val
                    })
    
    df = pd.DataFrame(rows)
    csv_file = f'monthly_rainfall_{year}.csv'
    df.to_csv(csv_file, index=False)
    print(f"  ✅ Saved {len(df)} rows to {csv_file}")
    
    all_years_df.append(df)

# -------------------------------------------------
# 4. Combine all years
# -------------------------------------------------
print(f"\n{'='*50}")
print("Combining all years...")
combined_df = pd.concat(all_years_df, ignore_index=True)
combined_csv = 'monthly_rainfall_all_years.csv'
combined_df.to_csv(combined_csv, index=False)
print(f"✅ Saved combined data with {len(combined_df)} rows to {combined_csv}")

# -------------------------------------------------
# 5. Statistics
# -------------------------------------------------
print(f"\n{'='*50}")
print("DATA STATISTICS")
print(f"{'='*50}")
print(f"Years: {start_yr} to {end_yr}")
print(f"Total rows: {len(combined_df):,}")
print(f"Latitude range: {combined_df['lat'].min():.2f} to {combined_df['lat'].max():.2f}")
print(f"Longitude range: {combined_df['lon'].min():.2f} to {combined_df['lon'].max():.2f}")
print(f"Rainfall range: {combined_df['rainfall'].min():.2f} to {combined_df['rainfall'].max():.2f}")
print(f"Average rainfall: {combined_df['rainfall'].mean():.2f} mm")

print("\n🎉 All data processing complete!")
print("\n📁 Generated files:")
for year in range(start_yr, end_yr + 1):
    print(f"  - monthly_rainfall_{year}.csv")
print(f"  - monthly_rainfall_all_years.csv")