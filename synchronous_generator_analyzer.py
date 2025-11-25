#!/usr/bin/env python3
"""
Advanced Synchronous Generator Parallel Operation Analyzer
Comprehensive tool for electrical engineering analysis with dynamic simulation
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from scipy.integrate import solve_ivp, odeint
import math
from dataclasses import dataclass
from typing import Tuple, List
import threading
import time


@dataclass
class GeneratorParameters:
    """Parameters for a synchronous generator"""
    Pn: float          # Nominal power (kW)
    V1n: float         # Nominal voltage (V)
    Ifn: float         # Nominal field current (A)
    xs: float          # d-axis synchronous reactance (pu)
    cos_phi_n: float   # Nominal power factor
    name: str          # Generator identifier


class SynchronousGeneratorModel:
    """Mathematical model for synchronous generator analysis"""

    def __init__(self, gen_params: GeneratorParameters):
        self.params = gen_params
        self.Zbase = None
        self.Ibase = None
        self.calculate_base_values()

    def calculate_base_values(self):
        """Calculate base values for per-unit system"""
        # Base values for per-unit calculations
        Sbase = self.params.Pn / self.params.cos_phi_n  # Base apparent power (kVA)
        Vbase_line = self.params.V1n  # Base line voltage (V)
        Vbase_phase = Vbase_line / np.sqrt(3)  # Base phase voltage (V)
        self.Ibase = Sbase * 1000 / (np.sqrt(3) * Vbase_line)  # Base current (A)
        self.Zbase = Vbase_phase / self.Ibase  # Base impedance (Ohm)

    def calculate_emf(self, P: float, Q: float, V: float, If: float) -> complex:
        """Calculate internal EMF (E) of the generator

        Args:
            P: Active power (kW)
            Q: Reactive power (kVAr)
            V: Terminal voltage (V line-to-line)
            If: Field current (A)

        Returns:
            Complex EMF
        """
        # Convert to phase values
        V_phase = V / np.sqrt(3)

        # Calculate current magnitude and angle
        S = P + 1j * Q  # Complex power (kVA)
        I = np.conj(S * 1000 / (np.sqrt(3) * V))  # Phase current

        # Synchronous reactance in ohms
        Xs_ohm = self.params.xs * self.Zbase

        # Internal EMF: E = V + jXs*I
        V_complex = V_phase + 0j
        E = V_complex + 1j * Xs_ohm * I

        return E

    def calculate_field_current(self, P: float, Q: float, V: float,
                               If_ref: float = None) -> float:
        """Calculate required field current for given operating point

        Args:
            P: Active power (kW)
            Q: Reactive power (kVAr)
            V: Terminal voltage (V)
            If_ref: Reference field current for scaling

        Returns:
            Required field current (A)
        """
        if If_ref is None:
            If_ref = self.params.Ifn

        E = self.calculate_emf(P, Q, V, If_ref)
        E_mag = abs(E)

        # EMF is proportional to field current (unsaturated)
        # E/En = If/Ifn
        V_phase_n = self.params.V1n / np.sqrt(3)

        # At nominal conditions
        Sn = self.params.Pn / self.params.cos_phi_n
        phi_n = np.arccos(self.params.cos_phi_n)
        Qn = Sn * np.sin(phi_n)
        E_n = self.calculate_emf(self.params.Pn, Qn, self.params.V1n, self.params.Ifn)
        E_n_mag = abs(E_n)

        # Calculate required field current
        If_required = If_ref * (E_mag / E_n_mag) * (self.params.Ifn / If_ref)

        return If_required

    def calculate_reactive_power(self, P: float, V: float, If: float) -> float:
        """Calculate reactive power for given active power, voltage and field current

        This requires iterative solution
        """
        # Initial guess
        phi = np.arccos(self.params.cos_phi_n)
        Q = P * np.tan(phi)

        # Iterative solution
        for _ in range(50):
            E = self.calculate_emf(P, Q, V, If)
            E_mag = abs(E)

            # EMF equation: E = V + jXs*I
            # For given If, we can find the required Q
            V_phase = V / np.sqrt(3)
            Xs_ohm = self.params.xs * self.Zbase

            # From power: S = V*I*
            I_mag = (P**2 + Q**2)**0.5 * 1000 / (np.sqrt(3) * V)

            # From EMF equation magnitude:
            # E^2 = V^2 + (Xs*I)^2 + 2*V*Xs*I*sin(phi)
            # where phi is the power factor angle

            S = P + 1j * Q
            I = np.conj(S * 1000 / (np.sqrt(3) * V))
            E_calc = V_phase + 1j * Xs_ohm * I

            # Scale to match field current
            E_n = abs(self.calculate_emf(self.params.Pn,
                                         self.params.Pn * np.tan(np.arccos(self.params.cos_phi_n)),
                                         self.params.V1n, self.params.Ifn))
            E_target = E_n * If / self.params.Ifn

            # Adjust Q to match E_target
            error = abs(E_calc) - E_target
            if abs(error) < 0.1:
                break

            # Update Q
            Q_adjust = error * 10
            Q -= Q_adjust

        return Q


class ParallelGeneratorAnalyzer:
    """Analyzer for parallel operation of synchronous generators"""

    def __init__(self, gen_a: GeneratorParameters, gen_b: GeneratorParameters):
        self.gen_a = SynchronousGeneratorModel(gen_a)
        self.gen_b = SynchronousGeneratorModel(gen_b)

    def solve_part_a(self, PL: float, cos_phi_L: float, If_A: float,
                     P_A: float, P_B: float, V: float) -> Tuple[float, dict]:
        """Solve part (a): Find If_B for given conditions

        Args:
            PL: Total load power (kW)
            cos_phi_L: Load power factor
            If_A: Field current of generator A (A)
            P_A: Active power of generator A (kW)
            P_B: Active power of generator B (kW)
            V: Terminal voltage (V)

        Returns:
            Tuple of (If_B, results_dict)
        """
        # Load reactive power
        phi_L = np.arccos(cos_phi_L)
        QL = PL * np.tan(phi_L)

        # Calculate Q_A from generator A conditions
        Q_A = self.gen_a.calculate_reactive_power(P_A, V, If_A)

        # Q_B must supply the remaining reactive power
        Q_B = QL - Q_A

        # Calculate required If_B
        If_B = self.gen_b.calculate_field_current(P_B, Q_B, V)

        results = {
            'If_B': If_B,
            'P_A': P_A,
            'P_B': P_B,
            'Q_A': Q_A,
            'Q_B': Q_B,
            'Q_L': QL,
            'S_A': np.sqrt(P_A**2 + Q_A**2),
            'S_B': np.sqrt(P_B**2 + Q_B**2),
            'cos_phi_A': P_A / np.sqrt(P_A**2 + Q_A**2),
            'cos_phi_B': P_B / np.sqrt(P_B**2 + Q_B**2)
        }

        return If_B, results

    def solve_part_b(self, PL: float, cos_phi_L: float, delta_P: float,
                     If_B: float, P_A: float, P_B: float, V: float) -> Tuple[float, dict]:
        """Solve part (b): Find If_A when additional load is connected

        Args:
            PL: Original load power (kW)
            cos_phi_L: Original load power factor
            delta_P: Additional load power (kW) at unity power factor
            If_B: Field current of generator B (kept constant) (A)
            P_A: New active power of generator A (kW)
            P_B: Active power of generator B (kW)
            V: Terminal voltage (V)

        Returns:
            Tuple of (If_A, results_dict)
        """
        # New total load
        phi_L = np.arccos(cos_phi_L)
        QL_original = PL * np.tan(phi_L)

        PL_new = PL + delta_P
        QL_new = QL_original  # Additional load at unity pf doesn't add Q

        # Calculate Q_B (kept constant with If_B)
        Q_B = self.gen_b.calculate_reactive_power(P_B, V, If_B)

        # Calculate required Q_A
        Q_A = QL_new - Q_B

        # Calculate required If_A
        If_A = self.gen_a.calculate_field_current(P_A, Q_A, V)

        results = {
            'If_A': If_A,
            'P_A': P_A,
            'P_B': P_B,
            'Q_A': Q_A,
            'Q_B': Q_B,
            'Q_L': QL_new,
            'P_L': PL_new,
            'S_A': np.sqrt(P_A**2 + Q_A**2),
            'S_B': np.sqrt(P_B**2 + Q_B**2),
            'cos_phi_A': P_A / np.sqrt(P_A**2 + Q_A**2),
            'cos_phi_B': P_B / np.sqrt(P_B**2 + Q_B**2)
        }

        return If_A, results


class DynamicSimulator:
    """Dynamic simulation of synchronous generator using swing equation"""

    def __init__(self, gen_params: GeneratorParameters):
        self.params = gen_params
        self.H = 3.0  # Inertia constant (s) - typical value
        self.D = 2.0  # Damping coefficient
        self.omega_s = 2 * np.pi * 60  # Synchronous speed (rad/s) for 60 Hz
        self.running = False

    def swing_equation(self, t, y, Pm, Pe_func):
        """Swing equation: differential equations for rotor dynamics

        State variables:
        y[0] = delta (rotor angle in radians)
        y[1] = omega (rotor speed in rad/s)

        Args:
            t: time
            y: state vector [delta, omega]
            Pm: Mechanical power (pu)
            Pe_func: Function to calculate electrical power given delta

        Returns:
            dy/dt
        """
        delta, omega = y

        # Calculate electrical power
        Pe = Pe_func(delta)

        # Swing equations
        d_delta = omega - self.omega_s  # Rotor angle rate
        d_omega = (self.omega_s / (2 * self.H)) * (Pm - Pe - self.D * (omega - self.omega_s) / self.omega_s)

        return [d_delta, d_omega]

    def simulate_transient(self, Pm: float, V: float, E: float, X: float,
                          t_span: Tuple[float, float], delta_0: float = 0.1,
                          method: str = 'RK45') -> dict:
        """Simulate transient response

        Args:
            Pm: Mechanical power (pu)
            V: Terminal voltage (pu)
            E: Internal EMF (pu)
            X: Synchronous reactance (pu)
            t_span: Time span (t_start, t_end)
            delta_0: Initial rotor angle (rad)
            method: Integration method ('RK45' or 'Euler')

        Returns:
            Dictionary with simulation results
        """
        # Electrical power as function of delta
        def Pe_func(delta):
            return (E * V / X) * np.sin(delta)

        # Initial conditions
        y0 = [delta_0, self.omega_s]

        if method == 'RK45':
            # Use scipy's RK45 integrator
            sol = solve_ivp(
                lambda t, y: self.swing_equation(t, y, Pm, Pe_func),
                t_span,
                y0,
                method='RK45',
                dense_output=True,
                max_step=0.001
            )
            t = np.linspace(t_span[0], t_span[1], 1000)
            y = sol.sol(t)
            delta = y[0]
            omega = y[1]
        else:  # Euler method
            dt = 0.0001
            t = np.arange(t_span[0], t_span[1], dt)
            delta = np.zeros_like(t)
            omega = np.zeros_like(t)
            delta[0], omega[0] = y0

            for i in range(1, len(t)):
                dy = self.swing_equation(t[i-1], [delta[i-1], omega[i-1]], Pm, Pe_func)
                delta[i] = delta[i-1] + dy[0] * dt
                omega[i] = omega[i-1] + dy[1] * dt

        # Calculate electrical power
        Pe = (E * V / X) * np.sin(delta)

        # Calculate frequency deviation
        freq = omega / (2 * np.pi)

        results = {
            't': t,
            'delta': delta,
            'omega': omega,
            'frequency': freq,
            'Pe': Pe,
            'Pm': np.full_like(t, Pm)
        }

        return results


class AdvancedGeneratorGUI:
    """Advanced GUI for synchronous generator analysis"""

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Synchronous Generator Analyzer")
        self.root.geometry("1400x900")

        # Initialize default generator parameters
        self.gen_a_params = GeneratorParameters(
            Pn=500, V1n=6300, Ifn=21.0, xs=1.5, cos_phi_n=0.85, name="Generator A"
        )
        self.gen_b_params = GeneratorParameters(
            Pn=350, V1n=6300, Ifn=16.0, xs=1.6, cos_phi_n=0.85, name="Generator B"
        )

        self.analyzer = ParallelGeneratorAnalyzer(self.gen_a_params, self.gen_b_params)
        self.simulator = DynamicSimulator(self.gen_a_params)

        # Simulation control
        self.sim_running = False
        self.sim_thread = None

        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create main notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Create tabs
        self.create_main_menu_tab()
        self.create_steady_state_tab()
        self.create_dynamic_simulation_tab()
        self.create_phasor_diagram_tab()

        # Bind resize event
        self.root.bind('<Configure>', self.on_resize)

    def on_resize(self, event):
        """Handle window resize events"""
        # This will be called when window is resized
        # Matplotlib canvases will automatically adjust with pack/grid
        pass

    def create_main_menu_tab(self):
        """Create main menu and welcome screen"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Main Menu")

        # Configure grid
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = ttk.Label(main_frame, text="Advanced Synchronous Generator Analyzer",
                         font=('Arial', 24, 'bold'))
        title.grid(row=0, column=0, pady=20)

        # Description
        desc_frame = ttk.LabelFrame(main_frame, text="About", padding=20)
        desc_frame.grid(row=1, column=0, sticky='nsew', pady=10)
        desc_frame.grid_rowconfigure(0, weight=1)
        desc_frame.grid_columnconfigure(0, weight=1)

        desc_text = scrolledtext.ScrolledText(desc_frame, wrap=tk.WORD, height=15,
                                             font=('Arial', 11))
        desc_text.grid(row=0, column=0, sticky='nsew')

        description = """
        Welcome to the Advanced Synchronous Generator Analyzer!

        This comprehensive tool provides:

        🔧 Steady-State Analysis:
           • Parallel operation of synchronous generators
           • Field current calculations for voltage regulation
           • Power flow analysis
           • Reactive power distribution

        ⚡ Dynamic Simulation:
           • Transient stability analysis
           • Swing equation simulation
           • Real-time ODE solvers (RK45, Euler methods)
           • Frequency and power oscillation studies

        📊 Visualization:
           • Phasor diagrams
           • Time-domain waveforms
           • Power-angle curves
           • Interactive plots with auto-scaling

        🎛️ Features:
           • Intuitive parameter adjustment with sliders
           • Real-time calculations
           • Professional electrical engineering tool
           • Export-ready results

        Navigate through the tabs to access different analysis modules.
        """

        desc_text.insert('1.0', description)
        desc_text.config(state='disabled')

        # Quick start buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=20)

        ttk.Button(button_frame, text="Steady-State Analysis",
                  command=lambda: self.notebook.select(1),
                  width=25).grid(row=0, column=0, padx=10, pady=5)

        ttk.Button(button_frame, text="Dynamic Simulation",
                  command=lambda: self.notebook.select(2),
                  width=25).grid(row=0, column=1, padx=10, pady=5)

        ttk.Button(button_frame, text="Phasor Diagrams",
                  command=lambda: self.notebook.select(3),
                  width=25).grid(row=0, column=2, padx=10, pady=5)

    def create_steady_state_tab(self):
        """Create steady-state analysis tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚡ Steady-State Analysis")

        # Configure grid
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=0)
        tab.grid_columnconfigure(1, weight=1)

        # Left panel - Controls
        control_frame = ttk.Frame(tab, width=400)
        control_frame.grid(row=0, column=0, sticky='ns', padx=5, pady=5)
        control_frame.grid_propagate(False)

        # Generator parameters
        gen_frame = ttk.LabelFrame(control_frame, text="Generator Parameters", padding=10)
        gen_frame.pack(fill='x', padx=5, pady=5)

        # Generator A
        ttk.Label(gen_frame, text="Generator A", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=5)

        ttk.Label(gen_frame, text="Pn (kW):").grid(row=1, column=0, sticky='w')
        self.pn_a_var = tk.DoubleVar(value=500)
        ttk.Entry(gen_frame, textvariable=self.pn_a_var, width=15).grid(row=1, column=1)

        ttk.Label(gen_frame, text="Ifn (A):").grid(row=2, column=0, sticky='w')
        self.ifn_a_var = tk.DoubleVar(value=21.0)
        ttk.Entry(gen_frame, textvariable=self.ifn_a_var, width=15).grid(row=2, column=1)

        ttk.Label(gen_frame, text="xs (pu):").grid(row=3, column=0, sticky='w')
        self.xs_a_var = tk.DoubleVar(value=1.5)
        ttk.Entry(gen_frame, textvariable=self.xs_a_var, width=15).grid(row=3, column=1)

        ttk.Separator(gen_frame, orient='horizontal').grid(
            row=4, column=0, columnspan=2, sticky='ew', pady=10)

        # Generator B
        ttk.Label(gen_frame, text="Generator B", font=('Arial', 10, 'bold')).grid(
            row=5, column=0, columnspan=2, pady=5)

        ttk.Label(gen_frame, text="Pn (kW):").grid(row=6, column=0, sticky='w')
        self.pn_b_var = tk.DoubleVar(value=350)
        ttk.Entry(gen_frame, textvariable=self.pn_b_var, width=15).grid(row=6, column=1)

        ttk.Label(gen_frame, text="Ifn (A):").grid(row=7, column=0, sticky='w')
        self.ifn_b_var = tk.DoubleVar(value=16.0)
        ttk.Entry(gen_frame, textvariable=self.ifn_b_var, width=15).grid(row=7, column=1)

        ttk.Label(gen_frame, text="xs (pu):").grid(row=8, column=0, sticky='w')
        self.xs_b_var = tk.DoubleVar(value=1.6)
        ttk.Entry(gen_frame, textvariable=self.xs_b_var, width=15).grid(row=8, column=1)

        # Operating conditions for Part (a)
        part_a_frame = ttk.LabelFrame(control_frame, text="Part (a) - Conditions", padding=10)
        part_a_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(part_a_frame, text="Load Power PL (kW):").grid(row=0, column=0, sticky='w')
        self.pl_var = tk.DoubleVar(value=720)
        ttk.Scale(part_a_frame, from_=100, to=1000, variable=self.pl_var,
                 orient='horizontal', length=200).grid(row=0, column=1)
        ttk.Label(part_a_frame, textvariable=self.pl_var).grid(row=0, column=2)

        ttk.Label(part_a_frame, text="Load PF cos(φ):").grid(row=1, column=0, sticky='w')
        self.cos_phi_l_var = tk.DoubleVar(value=0.8)
        ttk.Scale(part_a_frame, from_=0.5, to=1.0, variable=self.cos_phi_l_var,
                 orient='horizontal', length=200).grid(row=1, column=1)
        ttk.Label(part_a_frame, textvariable=self.cos_phi_l_var).grid(row=1, column=2)

        ttk.Label(part_a_frame, text="If_A (A):").grid(row=2, column=0, sticky='w')
        self.if_a_var = tk.DoubleVar(value=20.0)
        ttk.Scale(part_a_frame, from_=10, to=30, variable=self.if_a_var,
                 orient='horizontal', length=200).grid(row=2, column=1)
        ttk.Label(part_a_frame, textvariable=self.if_a_var).grid(row=2, column=2)

        ttk.Label(part_a_frame, text="P_A (kW):").grid(row=3, column=0, sticky='w')
        self.pa_var = tk.DoubleVar(value=360)
        ttk.Scale(part_a_frame, from_=100, to=600, variable=self.pa_var,
                 orient='horizontal', length=200).grid(row=3, column=1)
        ttk.Label(part_a_frame, textvariable=self.pa_var).grid(row=3, column=2)

        ttk.Button(part_a_frame, text="Calculate Part (a)",
                  command=self.calculate_part_a).grid(row=4, column=0, columnspan=3, pady=10)

        # Operating conditions for Part (b)
        part_b_frame = ttk.LabelFrame(control_frame, text="Part (b) - Additional Load", padding=10)
        part_b_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(part_b_frame, text="Additional ΔP (kW):").grid(row=0, column=0, sticky='w')
        self.delta_p_var = tk.DoubleVar(value=130)
        ttk.Scale(part_b_frame, from_=0, to=300, variable=self.delta_p_var,
                 orient='horizontal', length=200).grid(row=0, column=1)
        ttk.Label(part_b_frame, textvariable=self.delta_p_var).grid(row=0, column=2)

        ttk.Button(part_b_frame, text="Calculate Part (b)",
                  command=self.calculate_part_b).grid(row=1, column=0, columnspan=3, pady=10)

        # Right panel - Results
        results_frame = ttk.Frame(tab)
        results_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD,
                                                     font=('Courier', 10))
        self.results_text.grid(row=0, column=0, sticky='nsew')

    def create_dynamic_simulation_tab(self):
        """Create dynamic simulation tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔄 Dynamic Simulation")

        # Configure grid
        tab.grid_rowconfigure(0, weight=0)
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Control panel
        control_frame = ttk.LabelFrame(tab, text="Simulation Controls", padding=10)
        control_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        # Parameters
        param_frame = ttk.Frame(control_frame)
        param_frame.pack(side='left', padx=10)

        ttk.Label(param_frame, text="Mechanical Power Pm (pu):").grid(row=0, column=0, sticky='w')
        self.pm_var = tk.DoubleVar(value=0.8)
        ttk.Scale(param_frame, from_=0.1, to=1.5, variable=self.pm_var,
                 orient='horizontal', length=200).grid(row=0, column=1, padx=5)
        ttk.Label(param_frame, textvariable=self.pm_var).grid(row=0, column=2)

        ttk.Label(param_frame, text="Terminal Voltage V (pu):").grid(row=1, column=0, sticky='w')
        self.v_pu_var = tk.DoubleVar(value=1.0)
        ttk.Scale(param_frame, from_=0.8, to=1.2, variable=self.v_pu_var,
                 orient='horizontal', length=200).grid(row=1, column=1, padx=5)
        ttk.Label(param_frame, textvariable=self.v_pu_var).grid(row=1, column=2)

        ttk.Label(param_frame, text="Internal EMF E (pu):").grid(row=2, column=0, sticky='w')
        self.e_pu_var = tk.DoubleVar(value=1.5)
        ttk.Scale(param_frame, from_=1.0, to=2.0, variable=self.e_pu_var,
                 orient='horizontal', length=200).grid(row=2, column=1, padx=5)
        ttk.Label(param_frame, textvariable=self.e_pu_var).grid(row=2, column=2)

        ttk.Label(param_frame, text="Initial Angle δ₀ (deg):").grid(row=3, column=0, sticky='w')
        self.delta_0_var = tk.DoubleVar(value=30)
        ttk.Scale(param_frame, from_=0, to=90, variable=self.delta_0_var,
                 orient='horizontal', length=200).grid(row=3, column=1, padx=5)
        ttk.Label(param_frame, textvariable=self.delta_0_var).grid(row=3, column=2)

        ttk.Label(param_frame, text="Simulation Time (s):").grid(row=4, column=0, sticky='w')
        self.sim_time_var = tk.DoubleVar(value=5.0)
        ttk.Entry(param_frame, textvariable=self.sim_time_var, width=10).grid(row=4, column=1, sticky='w', padx=5)

        ttk.Label(param_frame, text="Method:").grid(row=5, column=0, sticky='w')
        self.method_var = tk.StringVar(value='RK45')
        ttk.Radiobutton(param_frame, text='RK45', variable=self.method_var,
                       value='RK45').grid(row=5, column=1, sticky='w')
        ttk.Radiobutton(param_frame, text='Euler', variable=self.method_var,
                       value='Euler').grid(row=5, column=2, sticky='w')

        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side='right', padx=10)

        self.start_btn = ttk.Button(button_frame, text="▶ Start",
                                    command=self.start_simulation, width=12)
        self.start_btn.grid(row=0, column=0, padx=5, pady=2)

        self.stop_btn = ttk.Button(button_frame, text="⏸ Stop",
                                   command=self.stop_simulation, width=12, state='disabled')
        self.stop_btn.grid(row=1, column=0, padx=5, pady=2)

        self.reset_btn = ttk.Button(button_frame, text="🔄 Reset",
                                    command=self.reset_simulation, width=12)
        self.reset_btn.grid(row=2, column=0, padx=5, pady=2)

        # Plot area
        plot_frame = ttk.Frame(tab)
        plot_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        plot_frame.grid_rowconfigure(0, weight=1)
        plot_frame.grid_columnconfigure(0, weight=1)

        # Create matplotlib figure
        self.sim_fig = Figure(figsize=(12, 8))
        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, master=plot_frame)
        self.sim_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Create subplots
        self.ax_delta = self.sim_fig.add_subplot(3, 2, 1)
        self.ax_omega = self.sim_fig.add_subplot(3, 2, 2)
        self.ax_freq = self.sim_fig.add_subplot(3, 2, 3)
        self.ax_power = self.sim_fig.add_subplot(3, 2, 4)
        self.ax_phase = self.sim_fig.add_subplot(3, 2, 5)
        self.ax_power_angle = self.sim_fig.add_subplot(3, 2, 6)

        self.sim_fig.tight_layout()

    def create_phasor_diagram_tab(self):
        """Create phasor diagram visualization tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Phasor Diagrams")

        # Configure grid
        tab.grid_rowconfigure(0, weight=0)
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=1)

        # Control panel
        control_frame = ttk.LabelFrame(tab, text="Phasor Diagram Controls", padding=10)
        control_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

        ttk.Label(control_frame, text="Generator:").pack(side='left', padx=5)
        self.phasor_gen_var = tk.StringVar(value='A')
        ttk.Radiobutton(control_frame, text='Generator A', variable=self.phasor_gen_var,
                       value='A').pack(side='left', padx=5)
        ttk.Radiobutton(control_frame, text='Generator B', variable=self.phasor_gen_var,
                       value='B').pack(side='left', padx=5)

        ttk.Button(control_frame, text="Draw Phasor Diagram",
                  command=self.draw_phasor_diagram).pack(side='left', padx=20)

        # Plot area
        plot_frame = ttk.Frame(tab)
        plot_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        plot_frame.grid_rowconfigure(0, weight=1)
        plot_frame.grid_columnconfigure(0, weight=1)

        self.phasor_fig = Figure(figsize=(10, 8))
        self.phasor_canvas = FigureCanvasTkAgg(self.phasor_fig, master=plot_frame)
        self.phasor_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        self.ax_phasor = self.phasor_fig.add_subplot(111)
        self.phasor_fig.tight_layout()

    def calculate_part_a(self):
        """Calculate solution for part (a)"""
        try:
            # Update generator parameters
            self.gen_a_params.Pn = self.pn_a_var.get()
            self.gen_a_params.Ifn = self.ifn_a_var.get()
            self.gen_a_params.xs = self.xs_a_var.get()

            self.gen_b_params.Pn = self.pn_b_var.get()
            self.gen_b_params.Ifn = self.ifn_b_var.get()
            self.gen_b_params.xs = self.xs_b_var.get()

            # Recreate analyzer with updated parameters
            self.analyzer = ParallelGeneratorAnalyzer(self.gen_a_params, self.gen_b_params)

            # Get operating conditions
            PL = self.pl_var.get()
            cos_phi_L = self.cos_phi_l_var.get()
            If_A = self.if_a_var.get()
            P_A = self.pa_var.get()
            P_B = PL - P_A
            V = self.gen_a_params.V1n

            # Solve
            If_B, results = self.analyzer.solve_part_a(PL, cos_phi_L, If_A, P_A, P_B, V)

            # Display results
            output = "="*70 + "\n"
            output += "PART (a) - FIELD EXCITATION CURRENT CALCULATION\n"
            output += "="*70 + "\n\n"

            output += "Input Conditions:\n"
            output += "-" * 70 + "\n"
            output += f"  Load Power:              PL = {PL:.1f} kW\n"
            output += f"  Load Power Factor:       cos(φ_L) = {cos_phi_L:.2f} lagging\n"
            output += f"  Terminal Voltage:        V = {V:.0f} V\n"
            output += f"  Generator A Field Current: If_A = {If_A:.1f} A\n"
            output += f"  Generator A Power:       P_A = {P_A:.1f} kW\n"
            output += f"  Generator B Power:       P_B = {P_B:.1f} kW\n\n"

            output += "Results:\n"
            output += "-" * 70 + "\n"
            output += f"  Generator B Field Current: If_B = {If_B:.2f} A\n\n"

            output += "Detailed Analysis:\n"
            output += "-" * 70 + "\n"
            output += "Generator A:\n"
            output += f"  Active Power:    P_A = {results['P_A']:.2f} kW\n"
            output += f"  Reactive Power:  Q_A = {results['Q_A']:.2f} kVAr\n"
            output += f"  Apparent Power:  S_A = {results['S_A']:.2f} kVA\n"
            output += f"  Power Factor:    cos(φ_A) = {results['cos_phi_A']:.3f} {'lagging' if results['Q_A'] > 0 else 'leading'}\n\n"

            output += "Generator B:\n"
            output += f"  Active Power:    P_B = {results['P_B']:.2f} kW\n"
            output += f"  Reactive Power:  Q_B = {results['Q_B']:.2f} kVAr\n"
            output += f"  Apparent Power:  S_B = {results['S_B']:.2f} kVA\n"
            output += f"  Power Factor:    cos(φ_B) = {results['cos_phi_B']:.3f} {'lagging' if results['Q_B'] > 0 else 'leading'}\n\n"

            output += "Load:\n"
            output += f"  Total Active Power:    P_L = {PL:.2f} kW\n"
            output += f"  Total Reactive Power:  Q_L = {results['Q_L']:.2f} kVAr\n\n"

            output += "Power Balance Check:\n"
            output += f"  ΣP = P_A + P_B = {results['P_A'] + results['P_B']:.2f} kW (should equal {PL:.2f} kW)\n"
            output += f"  ΣQ = Q_A + Q_B = {results['Q_A'] + results['Q_B']:.2f} kVAr (should equal {results['Q_L']:.2f} kVAr)\n"

            output += "\n" + "="*70 + "\n"

            self.results_text.delete('1.0', tk.END)
            self.results_text.insert('1.0', output)

            # Store results for phasor diagram
            self.last_results_a = results

        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")

    def calculate_part_b(self):
        """Calculate solution for part (b)"""
        try:
            # First need results from part (a)
            if not hasattr(self, 'last_results_a'):
                messagebox.showwarning("Warning", "Please calculate Part (a) first!")
                return

            # Get operating conditions
            PL = self.pl_var.get()
            cos_phi_L = self.cos_phi_l_var.get()
            delta_P = self.delta_p_var.get()

            # If_B from part (a)
            If_B = self.last_results_a['If_B']

            # Assume equal power sharing of additional load
            P_A = self.pa_var.get() + delta_P / 2
            P_B = (PL - self.pa_var.get()) + delta_P / 2
            V = self.gen_a_params.V1n

            # Solve
            If_A, results = self.analyzer.solve_part_b(PL, cos_phi_L, delta_P, If_B, P_A, P_B, V)

            # Display results
            output = "="*70 + "\n"
            output += "PART (b) - ADDITIONAL LOAD CONNECTED\n"
            output += "="*70 + "\n\n"

            output += "Input Conditions:\n"
            output += "-" * 70 + "\n"
            output += f"  Original Load:           PL = {PL:.1f} kW at cos(φ) = {cos_phi_L:.2f}\n"
            output += f"  Additional Load:         ΔP = {delta_P:.1f} kW at cos(φ) = 1.0 (unity)\n"
            output += f"  New Total Load:          P_total = {results['P_L']:.1f} kW\n"
            output += f"  Terminal Voltage:        V = {V:.0f} V\n"
            output += f"  Generator B Field Current: If_B = {If_B:.2f} A (kept constant)\n"
            output += f"  Generator A Power:       P_A = {P_A:.1f} kW\n"
            output += f"  Generator B Power:       P_B = {P_B:.1f} kW\n\n"

            output += "Results:\n"
            output += "-" * 70 + "\n"
            output += f"  Generator A Field Current: If_A = {If_A:.2f} A\n\n"

            output += "Detailed Analysis:\n"
            output += "-" * 70 + "\n"
            output += "Generator A:\n"
            output += f"  Active Power:    P_A = {results['P_A']:.2f} kW\n"
            output += f"  Reactive Power:  Q_A = {results['Q_A']:.2f} kVAr\n"
            output += f"  Apparent Power:  S_A = {results['S_A']:.2f} kVA\n"
            output += f"  Power Factor:    cos(φ_A) = {results['cos_phi_A']:.3f} {'lagging' if results['Q_A'] > 0 else 'leading'}\n\n"

            output += "Generator B:\n"
            output += f"  Active Power:    P_B = {results['P_B']:.2f} kW\n"
            output += f"  Reactive Power:  Q_B = {results['Q_B']:.2f} kVAr\n"
            output += f"  Apparent Power:  S_B = {results['S_B']:.2f} kVA\n"
            output += f"  Power Factor:    cos(φ_B) = {results['cos_phi_B']:.3f} {'lagging' if results['Q_B'] > 0 else 'leading'}\n\n"

            output += "Load:\n"
            output += f"  Total Active Power:    P_L = {results['P_L']:.2f} kW\n"
            output += f"  Total Reactive Power:  Q_L = {results['Q_L']:.2f} kVAr\n\n"

            output += "Power Balance Check:\n"
            output += f"  ΣP = P_A + P_B = {results['P_A'] + results['P_B']:.2f} kW (should equal {results['P_L']:.2f} kW)\n"
            output += f"  ΣQ = Q_A + Q_B = {results['Q_A'] + results['Q_B']:.2f} kVAr (should equal {results['Q_L']:.2f} kVAr)\n"

            output += "\n" + "="*70 + "\n"

            self.results_text.delete('1.0', tk.END)
            self.results_text.insert('1.0', output)

            # Store results for phasor diagram
            self.last_results_b = results

        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")

    def start_simulation(self):
        """Start dynamic simulation"""
        if self.sim_running:
            return

        self.sim_running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        # Run simulation in thread
        self.sim_thread = threading.Thread(target=self.run_simulation)
        self.sim_thread.start()

    def stop_simulation(self):
        """Stop dynamic simulation"""
        self.sim_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def reset_simulation(self):
        """Reset simulation plots"""
        self.ax_delta.clear()
        self.ax_omega.clear()
        self.ax_freq.clear()
        self.ax_power.clear()
        self.ax_phase.clear()
        self.ax_power_angle.clear()
        self.sim_canvas.draw()

    def run_simulation(self):
        """Run the dynamic simulation"""
        try:
            # Get parameters
            Pm = self.pm_var.get()
            V = self.v_pu_var.get()
            E = self.e_pu_var.get()
            X = self.xs_a_var.get()
            delta_0 = np.radians(self.delta_0_var.get())
            t_end = self.sim_time_var.get()
            method = self.method_var.get()

            # Run simulation
            results = self.simulator.simulate_transient(
                Pm, V, E, X, (0, t_end), delta_0, method
            )

            # Plot results
            self.plot_simulation_results(results)

        except Exception as e:
            messagebox.showerror("Error", f"Simulation error: {str(e)}")
        finally:
            self.sim_running = False
            self.root.after(0, lambda: self.start_btn.config(state='normal'))
            self.root.after(0, lambda: self.stop_btn.config(state='disabled'))

    def plot_simulation_results(self, results):
        """Plot simulation results"""
        t = results['t']
        delta = results['delta']
        omega = results['omega']
        freq = results['frequency']
        Pe = results['Pe']
        Pm = results['Pm']

        # Clear previous plots
        self.ax_delta.clear()
        self.ax_omega.clear()
        self.ax_freq.clear()
        self.ax_power.clear()
        self.ax_phase.clear()
        self.ax_power_angle.clear()

        # Rotor angle
        self.ax_delta.plot(t, np.degrees(delta), 'b-', linewidth=2)
        self.ax_delta.set_xlabel('Time (s)')
        self.ax_delta.set_ylabel('Rotor Angle δ (degrees)')
        self.ax_delta.set_title('Rotor Angle vs Time')
        self.ax_delta.grid(True, alpha=0.3)

        # Rotor speed
        self.ax_omega.plot(t, omega / (2 * np.pi), 'r-', linewidth=2)
        self.ax_omega.axhline(y=60, color='k', linestyle='--', alpha=0.5, label='Synchronous speed')
        self.ax_omega.set_xlabel('Time (s)')
        self.ax_omega.set_ylabel('Rotor Speed (Hz)')
        self.ax_omega.set_title('Rotor Speed vs Time')
        self.ax_omega.legend()
        self.ax_omega.grid(True, alpha=0.3)

        # Frequency deviation
        self.ax_freq.plot(t, (freq - 60), 'g-', linewidth=2)
        self.ax_freq.axhline(y=0, color='k', linestyle='--', alpha=0.5)
        self.ax_freq.set_xlabel('Time (s)')
        self.ax_freq.set_ylabel('Frequency Deviation (Hz)')
        self.ax_freq.set_title('Frequency Deviation vs Time')
        self.ax_freq.grid(True, alpha=0.3)

        # Power
        self.ax_power.plot(t, Pe, 'b-', linewidth=2, label='Pe (Electrical)')
        self.ax_power.plot(t, Pm, 'r--', linewidth=2, label='Pm (Mechanical)')
        self.ax_power.set_xlabel('Time (s)')
        self.ax_power.set_ylabel('Power (pu)')
        self.ax_power.set_title('Power vs Time')
        self.ax_power.legend()
        self.ax_power.grid(True, alpha=0.3)

        # Phase plane (delta vs omega)
        self.ax_phase.plot(np.degrees(delta), omega / (2 * np.pi), 'b-', linewidth=2)
        self.ax_phase.plot(np.degrees(delta[0]), omega[0] / (2 * np.pi), 'go', markersize=10, label='Start')
        self.ax_phase.plot(np.degrees(delta[-1]), omega[-1] / (2 * np.pi), 'ro', markersize=10, label='End')
        self.ax_phase.set_xlabel('Rotor Angle δ (degrees)')
        self.ax_phase.set_ylabel('Rotor Speed (Hz)')
        self.ax_phase.set_title('Phase Plane Portrait')
        self.ax_phase.legend()
        self.ax_phase.grid(True, alpha=0.3)

        # Power-angle curve
        delta_range = np.linspace(-np.pi/2, np.pi/2, 100)
        E = self.e_pu_var.get()
        V = self.v_pu_var.get()
        X = self.xs_a_var.get()
        Pe_curve = (E * V / X) * np.sin(delta_range)

        self.ax_power_angle.plot(np.degrees(delta_range), Pe_curve, 'k-', linewidth=2, label='Pe-δ curve')
        self.ax_power_angle.plot(np.degrees(delta), Pe, 'b-', linewidth=1, alpha=0.5, label='Operating trajectory')
        self.ax_power_angle.axhline(y=self.pm_var.get(), color='r', linestyle='--', linewidth=2, label='Pm')
        self.ax_power_angle.set_xlabel('Rotor Angle δ (degrees)')
        self.ax_power_angle.set_ylabel('Power (pu)')
        self.ax_power_angle.set_title('Power-Angle Curve')
        self.ax_power_angle.legend()
        self.ax_power_angle.grid(True, alpha=0.3)
        self.ax_power_angle.set_xlim(-90, 90)

        self.sim_fig.tight_layout()
        self.sim_canvas.draw()

    def draw_phasor_diagram(self):
        """Draw phasor diagram for selected generator"""
        try:
            # Check if we have results
            if not hasattr(self, 'last_results_a'):
                messagebox.showwarning("Warning", "Please calculate Part (a) first!")
                return

            results = self.last_results_a
            gen_name = self.phasor_gen_var.get()

            if gen_name == 'A':
                gen = self.gen_a_params
                gen_model = self.analyzer.gen_a
                P = results['P_A']
                Q = results['Q_A']
                If = self.if_a_var.get()
            else:
                gen = self.gen_b_params
                gen_model = self.analyzer.gen_b
                P = results['P_B']
                Q = results['Q_B']
                If = results['If_B']

            V = gen.V1n

            # Calculate phasors
            V_phase = V / np.sqrt(3)
            S = (P + 1j * Q) * 1000  # VA
            I = np.conj(S / (np.sqrt(3) * V))  # Phase current

            # Synchronous reactance in ohms
            Xs_ohm = gen.xs * gen_model.Zbase

            # Internal EMF
            V_phasor = V_phase + 0j
            E_phasor = V_phasor + 1j * Xs_ohm * I

            # jXs*I drop
            jXsI = 1j * Xs_ohm * I

            # Clear and plot
            self.ax_phasor.clear()

            # Plot phasors
            # Reference: V along real axis
            self.ax_phasor.arrow(0, 0, V_phasor.real, V_phasor.imag,
                               head_width=50, head_length=100, fc='blue', ec='blue',
                               linewidth=2, label='V (Terminal Voltage)')

            # Current (scaled for visibility)
            I_scale = V_phase / abs(I) * 0.3  # Scale to 30% of voltage
            I_scaled = I * I_scale
            self.ax_phasor.arrow(0, 0, I_scaled.real, I_scaled.imag,
                               head_width=50, head_length=100, fc='red', ec='red',
                               linewidth=2, label='I (Current, scaled)')

            # jXs*I drop
            self.ax_phasor.arrow(V_phasor.real, V_phasor.imag,
                               jXsI.real, jXsI.imag,
                               head_width=50, head_length=100, fc='green', ec='green',
                               linewidth=2, label='jXs·I')

            # Internal EMF
            self.ax_phasor.arrow(0, 0, E_phasor.real, E_phasor.imag,
                               head_width=50, head_length=100, fc='purple', ec='purple',
                               linewidth=2, label='E (Internal EMF)')

            # Power angle
            delta = np.angle(E_phasor)
            arc_radius = V_phase * 0.2
            theta = np.linspace(0, delta, 50)
            self.ax_phasor.plot(arc_radius * np.cos(theta), arc_radius * np.sin(theta),
                              'k--', linewidth=1)
            self.ax_phasor.text(arc_radius * 1.3 * np.cos(delta/2),
                              arc_radius * 1.3 * np.sin(delta/2),
                              f'δ = {np.degrees(delta):.1f}°', fontsize=10)

            # Power factor angle
            phi = np.angle(I)
            if abs(phi) > 0.01:
                arc_radius2 = V_phase * 0.15
                theta2 = np.linspace(0, -phi, 50)
                self.ax_phasor.plot(arc_radius2 * np.cos(theta2), arc_radius2 * np.sin(theta2),
                                  'r--', linewidth=1)
                self.ax_phasor.text(arc_radius2 * 1.3 * np.cos(-phi/2),
                                  arc_radius2 * 1.3 * np.sin(-phi/2),
                                  f'φ = {np.degrees(-phi):.1f}°', fontsize=10)

            # Formatting
            max_val = max(abs(E_phasor), abs(V_phasor)) * 1.2
            self.ax_phasor.set_xlim(-max_val, max_val)
            self.ax_phasor.set_ylim(-max_val, max_val)
            self.ax_phasor.set_aspect('equal')
            self.ax_phasor.grid(True, alpha=0.3)
            self.ax_phasor.axhline(y=0, color='k', linewidth=0.5)
            self.ax_phasor.axvline(x=0, color='k', linewidth=0.5)
            self.ax_phasor.legend(loc='upper right')
            self.ax_phasor.set_xlabel('Real Axis')
            self.ax_phasor.set_ylabel('Imaginary Axis')
            self.ax_phasor.set_title(f'Phasor Diagram - Generator {gen_name}')

            # Add text with values
            text_str = f'Generator {gen_name}\n'
            text_str += f'P = {P:.1f} kW\n'
            text_str += f'Q = {Q:.1f} kVAr\n'
            text_str += f'S = {np.sqrt(P**2 + Q**2):.1f} kVA\n'
            text_str += f'|V| = {V_phase:.1f} V\n'
            text_str += f'|I| = {abs(I):.2f} A\n'
            text_str += f'|E| = {abs(E_phasor):.1f} V\n'
            text_str += f'If = {If:.2f} A\n'
            text_str += f'cos(φ) = {P/np.sqrt(P**2 + Q**2):.3f}'

            self.ax_phasor.text(0.02, 0.98, text_str,
                              transform=self.ax_phasor.transAxes,
                              verticalalignment='top',
                              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                              fontsize=9, family='monospace')

            self.phasor_fig.tight_layout()
            self.phasor_canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", f"Phasor diagram error: {str(e)}")


def main():
    """Main function to run the application"""
    root = tk.Tk()
    app = AdvancedGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
