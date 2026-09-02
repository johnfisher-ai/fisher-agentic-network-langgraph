"""A config-driven multi-agent network built on LangGraph.

The agent roster, the routing and synthesis prompts, the demo scenarios and every
agent's canned reply live in an XML file, not in code. Point the loader at a
different file and the same graph becomes a different business.

    from agentic_network import load_config, build_network, ConsoleChannel

    cfg = load_config("config/config_travel.xml")
    net = build_network(cfg, channel=ConsoleChannel())
    net.run("My bookings for November are down 20%.")
"""

from .config import Agent, NetworkConfig, Scenario, load_config
from .channels import Channel, ConsoleChannel, QueueChannel
from .graph import Network, build_network

__all__ = [
    "Agent", "NetworkConfig", "Scenario", "load_config",
    "Channel", "ConsoleChannel", "QueueChannel",
    "Network", "build_network",
]
