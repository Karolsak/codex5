# Advanced Synchronous Generator Analyzer

## Overview

A comprehensive Python + Tkinter application for analyzing synchronous generator parallel operation with advanced features for electrical engineering applications.

## Problem Statement

This application solves the following problem:

Two non-salient pole rotor synchronous generators A and B with unsaturated magnetic circuits operate in parallel. The stator windings of both generators are Y-connected.

**Nominal (rated) parameters:**
- Generator A: Pn = 500 kW, Ifn = 21.0 A, xs = 1.5 pu
- Generator B: Pn = 350 kW, Ifn = 16.0 A, xs = 1.6 pu
- Output voltage: V1n = 6300 V
- Power factors: cos φn = 0.85 lagging (both generators)

**Part (a):** Calculate the field excitation current of generator B (IfB) to obtain V = Vn for:
- Load power: PL = 720 kW
- Load power factor: cos φL = 0.8 lagging
- Field excitation current of generator A: IfA = 20 A
- Each generator delivers 360 kW

**Part (b):** With the same conditions as part (a), additional load has been connected:
- Additional load: ΔP = 130 kW at cos φ = 1.0 (unity power factor)
- Keeping the same operating conditions of generator B
- Calculate the new field excitation current of generator A (IfA)

## Features

### 1. Steady-State Analysis
- Parallel operation of synchronous generators
- Field current calculations for voltage regulation
- Power flow analysis (active and reactive power)
- Reactive power distribution between generators
- Detailed power balance verification
- Interactive parameter adjustment with sliders

### 2. Dynamic Simulation
- Transient stability analysis using swing equation
- Real-time ODE solvers:
  - **RK45 (Runge-Kutta 4th/5th order)** - High accuracy
  - **Euler method** - Fast computation
- Rotor angle dynamics
- Frequency oscillation analysis
- Power oscillation studies
- Phase plane portraits
- Power-angle curve visualization

### 3. Visualization
- **Phasor Diagrams:**
  - Terminal voltage (V)
  - Current (I)
  - Internal EMF (E)
  - Synchronous reactance voltage drop (jXs·I)
  - Power angle (δ)
  - Power factor angle (φ)

- **Dynamic Plots:**
  - Rotor angle vs time
  - Rotor speed vs time
  - Frequency deviation vs time
  - Electrical and mechanical power vs time
  - Phase plane (speed vs angle)
  - Power-angle operating trajectory

### 4. User Interface
- Professional Tkinter GUI with tabbed interface
- Main menu with quick navigation
- Parameter input with validation
- Control sliders for real-time adjustment
- Auto-scaling plots that adjust with window size
- Start/Stop/Reset controls for simulation
- Scrollable results display with detailed analysis

## Installation

### Requirements

```bash
pip install numpy matplotlib scipy
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

### Required Packages
- Python 3.7+
- numpy - Numerical computations
- matplotlib - Plotting and visualization
- scipy - ODE solvers (solve_ivp, odeint)
- tkinter - GUI (usually included with Python)

## Usage

### Running the Application

```bash
python3 synchronous_generator_analyzer.py
```

Or make it executable:

```bash
chmod +x synchronous_generator_analyzer.py
./synchronous_generator_analyzer.py
```

### Using the Application

#### 1. Main Menu Tab
- Overview of application features
- Quick navigation buttons to different modules
- Application description and capabilities

#### 2. Steady-State Analysis Tab

**Steps:**
1. Adjust generator parameters (Pn, Ifn, xs) if needed
2. Set operating conditions using sliders:
   - Load power (PL)
   - Load power factor (cos φL)
   - Generator A field current (IfA)
   - Active power distribution (PA)
3. Click "Calculate Part (a)" to find IfB
4. Adjust additional load (ΔP)
5. Click "Calculate Part (b)" to find new IfA

**Results Display:**
- Field excitation currents
- Active and reactive power for each generator
- Apparent power and power factors
- Power balance verification
- Detailed analysis report

#### 3. Dynamic Simulation Tab

**Steps:**
1. Set simulation parameters:
   - Mechanical power (Pm)
   - Terminal voltage (V)
   - Internal EMF (E)
   - Initial rotor angle (δ₀)
   - Simulation time
2. Choose integration method (RK45 or Euler)
3. Click "Start" to run simulation
4. Observe real-time plots
5. Click "Stop" to pause or "Reset" to clear

**Visualizations:**
- Rotor angle oscillations
- Rotor speed variations
- Frequency deviations from 60 Hz
- Power balance (Pe vs Pm)
- Phase plane trajectory
- Power-angle operating curve

#### 4. Phasor Diagrams Tab

**Steps:**
1. Calculate Part (a) or Part (b) first
2. Select generator (A or B)
3. Click "Draw Phasor Diagram"

**Display:**
- Vector representation of all electrical quantities
- Power angle (δ) and power factor angle (φ)
- Magnitude and phase information
- Detailed parameter values

## Mathematical Background

### Synchronous Generator Model

**Per-Unit System:**
- Base power: Sbase = Pn / cos φn
- Base voltage: Vbase = V1n / √3 (phase)
- Base current: Ibase = Sbase / (√3 × V1n)
- Base impedance: Zbase = Vbase / Ibase

**EMF Equation:**
```
E = V + jXs·I
```

Where:
- E = Internal EMF (proportional to field current)
- V = Terminal voltage
- Xs = Synchronous reactance
- I = Armature current

**Power Equations:**
```
Pe = (E·V/Xs) sin(δ)
S = P + jQ = V·I*
```

### Swing Equation (Dynamic Model)

**Rotor Dynamics:**
```
d²δ/dt² = (ωs/2H)(Pm - Pe - D·Δω)
dω/dt = (ωs/2H)(Pm - Pe - D·(ω - ωs))
```

Where:
- δ = Rotor angle (rad)
- ω = Rotor speed (rad/s)
- ωs = Synchronous speed (2π·60 rad/s)
- H = Inertia constant (s)
- D = Damping coefficient
- Pm = Mechanical power (pu)
- Pe = Electrical power (pu)

## Solution Method

### Part (a) - Finding IfB

1. Calculate load reactive power: QL = PL × tan(φL)
2. For Generator A with given IfA and PA:
   - Calculate EMF: EA = V + jXsA·IA
   - Determine reactive power QA
3. Calculate Generator B reactive power: QB = QL - QA
4. Find IfB from EMF-field current relationship:
   - IfB = Ifn × (EB/En)

### Part (b) - Finding IfA

1. New total load: PL_new = PL + ΔP
2. Reactive power unchanged: QL_new = QL (unity pf load)
3. With IfB constant, calculate QB
4. Calculate required QA = QL_new - QB
5. Find IfA for new operating point

## Advanced Features

### Auto-Scaling
- All plots automatically adjust when window is resized
- Responsive layout using Tkinter grid weights
- Maintains aspect ratio for phasor diagrams

### Real-Time Control
- Slider adjustments update displayed values
- Thread-based simulation for responsive GUI
- Start/Stop/Reset controls for simulation

### Professional Output
- Formatted results with proper units
- Power balance verification
- IEEE-style phasor diagrams
- Publication-ready plots

## Practical Applications

This tool is useful for:

1. **Power System Design:**
   - Generator sizing and selection
   - Excitation system design
   - Voltage regulation studies

2. **Operation Planning:**
   - Load sharing between generators
   - Reactive power management
   - Voltage control strategies

3. **Stability Analysis:**
   - Transient stability assessment
   - Oscillation damping studies
   - Critical clearing time determination

4. **Education:**
   - Power system courses
   - Electrical machine laboratories
   - Understanding generator dynamics

## Results for Given Problem

### Part (a) Solution
For the given conditions (PL = 720 kW, cos φL = 0.8, IfA = 20 A, PA = PB = 360 kW):

**Expected Results:**
- IfB ≈ 15-17 A (depending on exact model)
- Generator A: Operating at lower excitation, may be absorbing reactive power
- Generator B: Higher excitation to maintain voltage

### Part (b) Solution
With additional 130 kW at unity pf:

**Expected Results:**
- New total load: 850 kW
- IfA increases to supply additional reactive power
- Generator power distribution: PA ≈ 425 kW, PB ≈ 425 kW

## Troubleshooting

### Common Issues

**1. Import Errors:**
```bash
# Install missing packages
pip install numpy matplotlib scipy
```

**2. Tkinter Not Found:**
```bash
# On Ubuntu/Debian
sudo apt-get install python3-tk

# On macOS (usually included)
# On Windows (usually included)
```

**3. Display Issues:**
- Ensure you have a display environment (X11 for Linux)
- For remote systems, enable X11 forwarding

**4. Slow Simulation:**
- Use RK45 method for accuracy
- Use Euler method for speed
- Reduce simulation time or increase time step

## Code Structure

```
synchronous_generator_analyzer.py
├── GeneratorParameters (dataclass)
│   └── Generator specifications
├── SynchronousGeneratorModel (class)
│   ├── Base value calculations
│   ├── EMF calculations
│   └── Field current calculations
├── ParallelGeneratorAnalyzer (class)
│   ├── solve_part_a()
│   └── solve_part_b()
├── DynamicSimulator (class)
│   ├── swing_equation()
│   └── simulate_transient()
└── AdvancedGeneratorGUI (class)
    ├── Main menu tab
    ├── Steady-state analysis tab
    ├── Dynamic simulation tab
    └── Phasor diagram tab
```

## Future Enhancements

Possible additions:
- Export results to CSV/PDF
- Parameter optimization
- Multi-machine simulation
- Fault analysis
- Generator capability curves
- Excitation system models
- Governor models
- Network impedance effects

## References

1. P. Kundur, "Power System Stability and Control", McGraw-Hill, 1994
2. IEEE Standards for Synchronous Generators
3. J. Machowski et al., "Power System Dynamics: Stability and Control"

## License

This educational tool is provided for learning and research purposes.

## Author

Created for electrical engineering education and practical power system analysis.

## Support

For issues or questions, please refer to the code comments and documentation.
