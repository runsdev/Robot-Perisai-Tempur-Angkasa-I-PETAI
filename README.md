# Robot-Perisai-Tempur-Angkasa-I-PETAI

## Load Balancer Visualization System

A Python visualization tool for simulating and analyzing different load balancing algorithms and server configurations in real-time.

## Features

- **7 Load Balancing Algorithms**:
  - Round Robin
  - Least Connections
  - Weighted Round Robin
  - Least Response Time
  - Resource Based
  - Random
  - Power of Two

- **4 Server Types**:
  - Standard
  - High-Performance
  - Memory Optimized
  - CPU Optimized

- **User Traffic Simulation**:
  - Light, Standard, Heavy, Burst, and Naughty user types
  - Configurable spawn rates and traffic patterns
  - Naughty users can perform some attack to the servers

- **Real-time Performance Monitoring**:
  - Server metrics tracking
  - Algorithm success rate analysis
  - Response time measurements

- **Report Generation**:
  - Comprehensive HTML, CSV and JSON reports
  - Per-server statistics 
  - Algorithm performance comparison

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Robot-Perisai-Tempur-Angkasa-I-PETAI.git
cd Robot-Perisai-Tempur-Angkasa-I-PETAI

# Install required packages
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Controls

- **SPACE** - Spawn single user
- **B** - Spawn burst traffic (8 users)
- **A** - Toggle auto algorithm cycling
- **1-7** - Switch algorithms (Round Robin, Least Conn, etc.)
- **Q/W/E/R** - Traffic patterns (Steady/Wave/Spike/Random)
- **S** - Start/Stop simulation
- **ESC** - Quit and save reports

## Generated Reports

All reports are saved in the `reports/` directory and include:
- HTML visualization reports
- CSV data files for servers and users
- JSON complete dataset
- Summary text reports

## Requirements

- Python 3.10+
- PyGame
- NumPy