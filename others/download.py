import pandas as pd
import requests
import os

# Load the Excel file with URL and feature data
excel_file = "IMAGE DATA.xlsx"
df = pd.read_excel(excel_file)
download_dir = "app1\static\downloaded_images1\male"
os.makedirs(download_dir, exist_ok=True)
# Iterate through each row in the DataFrame
for index, row in df.iterrows():
    # Extract the URL, Occasion, and Bodytype using column names
    url = row[df.columns[0]]  # Assumes URL is the first column
    type1 = row[df.columns[1]]  # Assumes Occasion is the second column
    theme = row[df.columns[2]]  # Assumes Bodytype is the third column

    # Get the image filename from the URL
    filename = os.path.join(download_dir, f'{type1}_{theme}_{index+1}.jpg')

    try:
        # Download the image using requests
        response = requests.get(url)
        if response.status_code == 200:
            # Save the image to the output directory
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
        else:
            print(f"Failed to download: {url}")
    except Exception as e:
        print(f"Error while downloading {url}: {e}")

print("Download complete.")