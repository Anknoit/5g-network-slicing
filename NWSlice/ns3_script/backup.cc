#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/lte-module.h"
#include "ns3/point-to-point-helper.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/ipv4-flow-classifier.h"
#include "ns3/random-variable-stream.h"

#include <fstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("5G_Slicing_Simulation");

// Function to log results to a CSV file
void LogResults(std::string sliceType, double timestamp, uint32_t bytesTransmitted,
                double latency, double jitter, double packetLoss, double throughput,
                int userCount, double signalStrength) {
    std::ofstream file;
    file.open("5g_slicing_results.csv", std::ios::app);
    file << sliceType << "," << timestamp << "," << bytesTransmitted << ","
         << latency << "," << jitter << "," << packetLoss << ","
         << throughput << "," << userCount << "," << signalStrength << "\n";
    file.close();
}

// Function to capture FlowMonitor statistics
void MonitorTraffic(Ptr<FlowMonitor> monitor, Ptr<Ipv4FlowClassifier> classifier, std::string sliceType) {
    FlowMonitor::FlowStatsContainer stats = monitor->GetFlowStats();

    for (auto iter = stats.begin(); iter != stats.end(); ++iter) {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(iter->first);
        std::cout << "Flow: " << t.sourceAddress << " -> " << t.destinationAddress << std::endl;
        double latency = iter->second.delaySum.GetSeconds();
        double jitter = iter->second.jitterSum.GetSeconds();
        double packetLoss = iter->second.lostPackets;
        double throughput = iter->second.txBytes * 8.0 / iter->second.timeLastTxPacket.GetSeconds() / 1e6; // Mbps
        uint32_t bytesTransmitted = iter->second.txBytes;
        double signalStrength = -80 + static_cast<double>(rand() % 30); // Simulated dBm values (-80 to -50)
        int userCount = rand() % 100; // Simulated number of users

        LogResults(sliceType, Simulator::Now().GetSeconds(), bytesTransmitted,
                   latency, jitter, packetLoss, throughput, userCount, signalStrength);
    }
}

int main(int argc, char *argv[]) {
    LogComponentEnable("5G_Slicing_Simulation", LOG_LEVEL_INFO);

    // Seed the random number generator
    srand(time(0));

    // Create LTE modules
    Ptr<LteHelper> lteHelper = CreateObject<LteHelper>();
    Ptr<PointToPointEpcHelper> epcHelper = CreateObject<PointToPointEpcHelper>();
    lteHelper->SetEpcHelper(epcHelper);

    Ptr<Node> pgw = epcHelper->GetPgwNode();
    InternetStackHelper internet;
    internet.Install(pgw);

    // Create remote host (acts as the internet)
    NodeContainer remoteHostContainer;
    remoteHostContainer.Create(1);
    internet.Install(remoteHostContainer);
    Ptr<Node> remoteHost = remoteHostContainer.Get(0);

    // Create nodes for point-to-point link
    NodeContainer p2pNodes;
    p2pNodes.Create(2); // Create two nodes for the point-to-point link

    // Install Internet stack on p2pNodes
    internet.Install(p2pNodes);

    // Setup routing
    Ipv4AddressHelper ipv4h;
    PointToPointHelper p2ph;
    p2ph.SetDeviceAttribute("DataRate", StringValue("10Gbps"));
    p2ph.SetChannelAttribute("Delay", StringValue("2ms"));

    ipv4h.SetBase("1.0.0.0", "255.0.0.0");
    NetDeviceContainer remoteHostDevices = p2ph.Install(p2pNodes); // Use p2pNodes here
    Ipv4InterfaceContainer internetIpIfaces = ipv4h.Assign(remoteHostDevices);
    Ipv4Address remoteHostAddr = internetIpIfaces.GetAddress(0);

    // Create eNB and UEs
    NodeContainer enbNodes, ueNodes;
    enbNodes.Create(1);
    ueNodes.Create(3);

    // Install Internet stack on UEs
    internet.Install(ueNodes);

    // Mobility model for UEs
    MobilityHelper mobility;
    mobility.SetMobilityModel("ns3::RandomWalk2dMobilityModel",
                              "Bounds", RectangleValue(Rectangle(-500, 500, -500, 500)));
    mobility.Install(ueNodes);

    // Fixed position for eNB
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(enbNodes);

    // Install LTE devices
    NetDeviceContainer enbDevs = lteHelper->InstallEnbDevice(enbNodes);
    NetDeviceContainer ueDevs = lteHelper->InstallUeDevice(ueNodes);

    // Assign IP addresses to UEs
    Ipv4InterfaceContainer ueIpIfaces = epcHelper->AssignUeIpv4Address(NetDeviceContainer(ueDevs));

    // Attach UEs to the eNB
    lteHelper->Attach(ueDevs, enbDevs.Get(0));

    // Install applications (traffic generation)
    uint16_t port = 9;
    ApplicationContainer apps;
    Ptr<UniformRandomVariable> randVar = CreateObject<UniformRandomVariable>();

    for (uint32_t i = 0; i < ueNodes.GetN(); i++) {
        // Randomize data rate and packet size
        double dataRate = randVar->GetValue(1.0, 50.0); // Random data rate between 1 Mbps and 50 Mbps
        uint32_t packetSize = randVar->GetValue(512, 2048); // Random packet size between 512 and 2048 bytes

        OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(remoteHostAddr, port));
        onoff.SetAttribute("DataRate", DataRateValue(DataRate(dataRate)));
        onoff.SetAttribute("PacketSize", UintegerValue(packetSize));

        apps = onoff.Install(ueNodes.Get(i));
        apps.Start(Seconds(randVar->GetValue(1.0, 2.0))); // Random start time between 1.0 and 2.0 seconds
        apps.Stop(Seconds(10.0));
    }

    // Enable FlowMonitor to track network performance
    FlowMonitorHelper flowmonHelper;
    Ptr<FlowMonitor> monitor = flowmonHelper.InstallAll();

    // Schedule monitoring function
    Simulator::Schedule(Seconds(2.0), &MonitorTraffic, monitor, DynamicCast<Ipv4FlowClassifier>(flowmonHelper.GetClassifier()), "eMBB");
    Simulator::Schedule(Seconds(5.0), &MonitorTraffic, monitor, DynamicCast<Ipv4FlowClassifier>(flowmonHelper.GetClassifier()), "URLLC");
    Simulator::Schedule(Seconds(8.0), &MonitorTraffic, monitor, DynamicCast<Ipv4FlowClassifier>(flowmonHelper.GetClassifier()), "mMTC");

    // Run the simulation
    Simulator::Stop(Seconds(10.0));
    Simulator::Run();

    // Save FlowMonitor data
    monitor->SerializeToXmlFile("flowmon-results.xml", true, true);

    Simulator::Destroy();
    return 0;
}