import subprocess
import pandas as pd
from django.shortcuts import render
from .models import SimulationResult
from django.views.decorators.csrf import csrf_exempt
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import io
import base64

def home(request):
    return render(request, "homepage.html")

def run_ns3_simulation():
    # Print the current working directory
    print("Current working directory:", os.getcwd())
    print("Running NS-3 Simulator")

    # Define the absolute path to the NS-3 executable
    ns3_executable = "/home/ankit/ns-allinone-3.44/ns-3.44/ns3" 
    simulation_script = "scratch/ns3_5g_slicing"

    # Run the NS-3 simulation
    result = subprocess.run([ns3_executable, "run", simulation_script], cwd="/home/ankit/ns-allinone-3.44/ns-3.44")  # Change 'your_username' to your actual username
    # Check if the simulation ran successfully
    if result.returncode != 0:
        print("Error running NS-3 simulation")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return

    print("Simulation Completed")

    print("Reading Data")

    # Define the path to the output CSV file
    output_csv_path = "/home/ankit/ns-allinone-3.44/ns-3.44/5g_slicing_results.csv"

    # Read the output CSV
    df = pd.read_csv(output_csv_path, names=["slice_type", "timestamp", "bytes_transmitted", "latency","jitter","packet_loss","throughput","user_count","signal_strength", "sinr", "cqi"])
    print("Data Reading Complete")

    # Store results in DB
    for _, row in df.iterrows():
        SimulationResult.objects.create(
            slice_type=row["slice_type"],
            timestamp=row["timestamp"],
            bytes_transmitted=row["bytes_transmitted"],
            latency=row["latency"],
            jitter=row["jitter"],
            packet_loss=row["packet_loss"],
            throughput=row["throughput"],
            user_count=row["user_count"],
            signal_strength=row["signal_strength"],
            sinr=row["sinr"],
            cqi=row["cqi"],
        )

def plot_graphs(df):
    # Plot throughput vs. slice type
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="slice_type", y="throughput", data=df)
    plt.title("Throughput by Slice Type")
    plt.xlabel("Slice Type")
    plt.ylabel("Throughput (Mbps)")
    throughput_graph = get_graph()

    # Plot latency vs. slice type
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="slice_type", y="latency", data=df)
    plt.title("Latency by Slice Type")
    plt.xlabel("Slice Type")
    plt.ylabel("Latency (s)")
    latency_graph = get_graph()

    return throughput_graph, latency_graph

def get_graph():
    # Convert plot to base64 for embedding in HTML
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    return image_base64

def train_ml_model(df):
    # Encode slice_type as labels
    df["slice_type"] = df["slice_type"].map({"eMBB": 0, "URLLC": 1, "mMTC": 2})

    # Features and target
    X = df[["throughput", "latency", "jitter", "packet_loss", "user_count", "signal_strength", "sinr", "cqi"]]
    y = df["slice_type"]

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a Random Forest Classifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Predict on test data
    y_pred = model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["eMBB", "URLLC", "mMTC"])

    return model, accuracy, report

@csrf_exempt
def start_simulation(request):
    if request.method == "POST":
        run_ns3_simulation()

        # Load data from the database
        results = SimulationResult.objects.all()
        df = pd.DataFrame(list(results.values()))

        # Plot graphs
        throughput_graph, latency_graph = plot_graphs(df)

        # Train ML model
        model, accuracy, report = train_ml_model(df)

        # Render results page
        return render(request, "slicing_simulator/results.html", {
            "throughput_graph": throughput_graph,
            "latency_graph": latency_graph,
            "accuracy": accuracy,
            "report": report,
            "results": results,
        })