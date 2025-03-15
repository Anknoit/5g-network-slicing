import subprocess
import pandas as pd
from django.shortcuts import render
from .models import SimulationResult
from django.views.decorators.csrf import csrf_exempt
import os
from ns3_script import *


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
    # output_csv_path = os.path.abspath(os.path.join(os.getcwd(), "../ns3_script/5g_slicing_results.csv"))
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

@csrf_exempt
def start_simulation(request):
    if request.method == "POST":
        run_ns3_simulation()
    
    results = SimulationResult.objects.all()
    return render(request, "slicing_simulator/results.html", {"results": results})