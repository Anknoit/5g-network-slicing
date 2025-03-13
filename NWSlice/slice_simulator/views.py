import subprocess
import pandas as pd
from django.shortcuts import render
from .models import SimulationResult

def run_ns3_simulation():
    # Run NS-3 simulation
    subprocess.run(["./waf", "--run", "scratch/ns3_5g_slicing"], cwd="ns3")

    # Read the output CSV
    df = pd.read_csv("ns3/5g_slicing_results.csv", names=["slice_type", "timestamp", "bytes_transmitted"])

    # Store results in DB
    for _, row in df.iterrows():
        SimulationResult.objects.create(
            slice_type=row["slice_type"],
            timestamp=row["timestamp"],
            bytes_transmitted=row["bytes_transmitted"]
        )

def start_simulation(request):
    if request.method == "POST":
        run_ns3_simulation()
    
    results = SimulationResult.objects.all()
    return render(request, "slicing_simulator/results.html", {"results": results})
