
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib
import os

def train_and_save_model():
    """
    This script trains a RandomForestRegressor model on the system_data.csv
    and saves the trained model to a new file, 'irrigation_model.pkl',
    in the same directory as the script.
    """
    # --- 1. Load Data ---
    # Construct the path to the CSV file relative to this script's location
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, 'system_data.csv')
        df = pd.read_csv(csv_path)
        print("Successfully loaded system_data.csv")
    except FileNotFoundError:
        print(f"Error: system_data.csv not found at {csv_path}")
        return

    # --- 2. Define Features (X) and Target (y) ---
    # Ensure column names match the CSV file exactly
    features = ['Soil Moisture (%)', 'Temperature (°C)', 'Humidity (%)', 'Light Level (lx)']
    target = 'Valve Duration (s)'

    X = df[features]
    y = df[target]
    print("Features and target defined.")

    # --- 3. Split Data ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print("Data split into training and testing sets.")

    # --- 4. Train the Model ---
    # Using the RandomForestRegressor as specified in the notebook
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )
    print("Training the RandomForestRegressor model...")
    model.fit(X_train, y_train)
    print("Model training complete.")

    # --- 5. Evaluate the Model (Optional but good practice) ---
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    print(f"Model evaluation (R2 Score): {r2:.4f}")

    # --- 6. Save the Trained Model ---
    # Save the new model to 'irrigation_model.pkl' in the same directory
    model_path = os.path.join(script_dir, 'irrigation_model.pkl')
    joblib.dump(model, model_path)
    
    print("-" * 50)
    print(f"Successfully trained and saved new model to:")
    print(model_path)
    print("-" * 50)


if __name__ == '__main__':
    # Ensure the necessary libraries are installed
    try:
        import sklearn
        import pandas
        print(f"Using scikit-learn version: {sklearn.__version__}")
        print(f"Using pandas version: {pandas.__version__}")
        train_and_save_model()
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please make sure you have scikit-learn and pandas installed in your environment.")
        print("You can install them using: pip install scikit-learn pandas")

