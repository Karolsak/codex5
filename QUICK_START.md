# Quick Start Guide

## Installation

### Step 1: Install Required Packages

```bash
pip3 install numpy matplotlib scipy
```

Or use the requirements file:

```bash
pip3 install -r requirements.txt
```

### Step 2: Run the Application

```bash
python3 synchronous_generator_analyzer.py
```

## Quick Test

To verify the calculations without GUI:

```bash
python3 test_generator_calculations.py
```

This will:
- Test Part (a) calculation (finding IfB)
- Test Part (b) calculation (finding IfA)
- Test dynamic simulation (RK45 and Euler methods)
- Display detailed results and power balance verification

## Problem Solutions

### Part (a): Calculate IfB

**Given:**
- Load: PL = 720 kW at cos φ = 0.8 lagging
- Generator A: IfA = 20 A, PA = 360 kW
- Generator B: PB = 360 kW
- Voltage: V = 6300 V (maintained constant)

**Find:** Field current IfB

**Steps in GUI:**
1. Go to "Steady-State Analysis" tab
2. Set Load Power PL = 720 kW (use slider)
3. Set Load PF cos(φ) = 0.8 (use slider)
4. Set If_A = 20 A (use slider)
5. Set P_A = 360 kW (use slider)
6. Click "Calculate Part (a)"

**Expected Result:** IfB ≈ 15-17 A (exact value shown in results)

### Part (b): Calculate IfA

**Given:**
- Previous conditions from Part (a)
- Additional load: ΔP = 130 kW at cos φ = 1.0
- Generator B conditions kept constant (same IfB)

**Find:** New field current IfA

**Steps in GUI:**
1. First complete Part (a)
2. Set Additional ΔP = 130 kW (use slider)
3. Click "Calculate Part (b)"

**Expected Result:** IfA increases from 20 A to ≈ 21-23 A

## GUI Features

### Main Menu Tab
- Overview of capabilities
- Quick navigation buttons

### Steady-State Analysis Tab

**Left Panel (Controls):**
- Generator parameters (Pn, Ifn, xs)
- Operating conditions (sliders for real-time adjustment)
- Calculation buttons for Part (a) and Part (b)

**Right Panel (Results):**
- Detailed calculation results
- Power balance verification
- Generator operating points

### Dynamic Simulation Tab

**Top Panel (Controls):**
- Mechanical power (Pm) - use slider
- Terminal voltage (V) - use slider
- Internal EMF (E) - use slider
- Initial rotor angle (δ₀) - use slider
- Simulation time - enter value
- Method selection - choose RK45 or Euler
- Start/Stop/Reset buttons

**Main Area (6 Plots):**
1. **Rotor Angle vs Time** - Shows oscillations
2. **Rotor Speed vs Time** - Frequency variations
3. **Frequency Deviation** - Deviation from 60 Hz
4. **Power vs Time** - Pe and Pm comparison
5. **Phase Plane** - Trajectory in speed-angle space
6. **Power-Angle Curve** - Operating point on P-δ curve

### Phasor Diagrams Tab

**Controls:**
- Select Generator A or B
- Click "Draw Phasor Diagram"

**Display:**
- Vector diagram showing V, I, E, jXs·I
- Power angle (δ)
- Power factor angle (φ)
- Magnitude values

## Tips for Use

### Steady-State Analysis

1. **Understanding Results:**
   - Positive Q means lagging (consuming reactive power)
   - Negative Q means leading (supplying reactive power)
   - Power balance should always check: ΣP = PL and ΣQ = QL

2. **Parameter Adjustment:**
   - Use sliders for quick exploration
   - Observe how field current affects reactive power
   - Higher If → Higher E → More reactive power supplied

3. **Physical Interpretation:**
   - Generator with higher If operates at higher excitation
   - Reactive power flows from high to low excitation
   - Both generators must supply total active power

### Dynamic Simulation

1. **Stable Operation:**
   - Pm ≈ Pe at equilibrium
   - Small initial angle (< 45°) usually stable
   - Oscillations should decay with damping

2. **Observing Instability:**
   - Increase Pm significantly above Pe max
   - Large initial angle (> 90°)
   - Watch for growing oscillations

3. **Method Selection:**
   - **RK45**: More accurate, slightly slower
   - **Euler**: Faster, may need smaller time step

4. **Simulation Time:**
   - 2-5 seconds: See initial transient
   - 5-10 seconds: Observe damping
   - Longer: See steady-state settling

### Phasor Diagrams

1. **Understanding the Diagram:**
   - V is reference (along real axis)
   - I lags V for lagging power factor
   - E leads V by power angle δ
   - jXs·I is perpendicular to I

2. **Physical Meaning:**
   - δ (power angle): Mechanical angle between rotor and stator field
   - φ (power factor angle): Electrical angle between V and I
   - Larger δ → More active power
   - Larger |E-V| → More reactive power

## Troubleshooting

### Import Errors
```bash
# Install missing packages
pip3 install numpy matplotlib scipy
```

### Tkinter Not Available
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# macOS/Windows: Usually pre-installed
```

### Window Not Appearing
- Ensure X11 display is available
- For remote: Enable X11 forwarding
- Try: `export DISPLAY=:0`

### Calculation Errors
- Check that all parameters are positive
- Ensure power factors are between 0 and 1
- Verify generator ratings are realistic

### Simulation Not Running
- Click "Reset" first
- Check simulation time > 0
- Ensure parameters are valid (E, V, X > 0)

## Understanding the Math

### Key Equations

**EMF Equation:**
```
E = V + jXs·I
```

**Power Equations:**
```
P = (E·V/Xs)·sin(δ)     [Active power]
Q = (E·V/Xs)·cos(δ) - V²/Xs   [Reactive power]
```

**Swing Equation:**
```
(2H/ωs)·d²δ/dt² = Pm - Pe - D·Δω
```

### Per-Unit System

All impedances, voltages, and currents can be expressed in per-unit:
```
Zbase = Vbase²/Sbase
Vbase = Vnominal/√3 (phase)
Sbase = Pnominal/cos(φn)
```

## Example Workflow

### Complete Analysis Workflow:

1. **Start Application**
   ```bash
   python3 synchronous_generator_analyzer.py
   ```

2. **Configure Parameters**
   - Check generator parameters match problem
   - Adjust if needed

3. **Solve Part (a)**
   - Set all operating conditions
   - Click "Calculate Part (a)"
   - Review results
   - Check power balance

4. **Solve Part (b)**
   - Set additional load
   - Click "Calculate Part (b)"
   - Compare with Part (a)
   - Note change in field current

5. **Visualize Operation**
   - Go to Phasor Diagrams tab
   - Select Generator A
   - Draw phasor diagram
   - Repeat for Generator B
   - Compare power angles

6. **Simulate Dynamics**
   - Go to Dynamic Simulation tab
   - Set parameters based on steady-state results
   - Choose RK45 method
   - Click Start
   - Observe transient response

7. **Export Results**
   - Take screenshots of plots
   - Copy text results from results panel

## Advanced Usage

### Custom Studies

**Voltage Regulation Study:**
1. Fix PL and cos φL
2. Vary IfA and IfB
3. Observe voltage changes
4. Find optimal field current distribution

**Reactive Power Sharing:**
1. Set equal active power
2. Vary field currents
3. Observe reactive power distribution
4. Understand over/under-excited operation

**Stability Analysis:**
1. Find steady-state operating point
2. Apply disturbance in simulation
3. Observe response
4. Determine stability margin

### Parameter Studies

**Effect of Synchronous Reactance:**
- Change xs values
- Observe impact on field currents
- Higher xs → Higher field current needed

**Effect of Power Factor:**
- Vary load power factor
- Observe reactive power requirements
- Unity pf → Minimum current

**Effect of Inertia (in simulation):**
- Modify H in code
- Re-run simulation
- Higher H → Slower oscillations

## Getting Help

### Documentation
- See `README_GENERATOR_ANALYZER.md` for detailed documentation
- Code comments explain each function
- Mathematical formulas are documented

### Common Questions

**Q: Why is IfB different from IfA?**
A: Different generators have different parameters (Pn, xs), and they may operate at different excitation levels to maintain voltage.

**Q: Can reactive power be negative?**
A: Yes! Negative Q means the generator is over-excited and supplying reactive power to the system.

**Q: What if power balance doesn't check?**
A: Small errors (< 0.1 kW) are numerical. Larger errors indicate calculation issues.

**Q: Why do oscillations grow in simulation?**
A: The system is unstable for those parameters. Reduce Pm or initial angle.

**Q: How to export plots?**
A: Take screenshots or modify code to add `plt.savefig()` calls.

## Next Steps

After mastering the basics:

1. **Modify the code** to add new features
2. **Study different scenarios** (faults, load changes)
3. **Add governor models** for frequency control
4. **Include network impedance** for realistic systems
5. **Implement optimization** for optimal operation

Happy analyzing! 🔌⚡
