import pandas as pd

def aggregate_minute_to_hourly(input_file, output_file):
    # Load CSV
    df = pd.read_csv(input_file)

    # Check that required column exists
    if "Date Time" not in df.columns:
        raise ValueError("Input file must contain a 'Date Time' column.")

    # Convert 'Date Time' column to datetime objects
    df["Date Time"] = pd.to_datetime(df["Date Time"], errors='coerce', dayfirst=True)

    # Drop rows with invalid or missing datetime values
    df.dropna(subset=["Date Time"], inplace=True)

    # Set datetime as index
    df.set_index("Date Time", inplace=True)

    # Resample to hourly, taking the mean of all other columns
    hourly_df = df.resample("H").mean()

    # Reset index for clean CSV output
    hourly_df.reset_index(inplace=True)
    hourly_df["Date Time"] = hourly_df["Date Time"].dt.strftime('%d-%m-%Y %H:%M')

    # Save to new CSV
    hourly_df.to_csv(output_file, index=False)
    print(f"Hourly aggregated data saved to: {output_file}")

# Example usage
if __name__ == "__main__":
    aggregate_minute_to_hourly("Stockton_20240901.csv", "Stockton_20240901_hour.csv")

