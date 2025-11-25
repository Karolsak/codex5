#!/usr/bin/env python3
"""
Test script for synchronous generator calculations
Tests the mathematical models without GUI
"""

import sys
import numpy as np

# Import classes from the main module
try:
    from synchronous_generator_analyzer import (
        GeneratorParameters,
        SynchronousGeneratorModel,
        ParallelGeneratorAnalyzer,
        DynamicSimulator
    )
    print("✓ Successfully imported all classes")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_part_a():
    """Test Part (a) calculation"""
    print("\n" + "="*70)
    print("TEST: PART (a) - Calculate IfB")
    print("="*70)

    # Create generator parameters
    gen_a = GeneratorParameters(
        Pn=500, V1n=6300, Ifn=21.0, xs=1.5, cos_phi_n=0.85, name="Generator A"
    )
    gen_b = GeneratorParameters(
        Pn=350, V1n=6300, Ifn=16.0, xs=1.6, cos_phi_n=0.85, name="Generator B"
    )

    # Create analyzer
    analyzer = ParallelGeneratorAnalyzer(gen_a, gen_b)

    # Operating conditions
    PL = 720  # kW
    cos_phi_L = 0.8
    If_A = 20.0  # A
    P_A = 360  # kW
    P_B = 360  # kW
    V = 6300  # V

    print("\nInput Conditions:")
    print(f"  Load Power: PL = {PL} kW")
    print(f"  Load Power Factor: cos(φ_L) = {cos_phi_L} lagging")
    print(f"  Terminal Voltage: V = {V} V")
    print(f"  Generator A Field Current: If_A = {If_A} A")
    print(f"  Generator A Power: P_A = {P_A} kW")
    print(f"  Generator B Power: P_B = {P_B} kW")

    try:
        # Solve part (a)
        If_B, results = analyzer.solve_part_a(PL, cos_phi_L, If_A, P_A, P_B, V)

        print("\n✓ Calculation successful!")
        print(f"\nResult: If_B = {If_B:.2f} A")

        print("\nDetailed Results:")
        print(f"  Generator A:")
        print(f"    P_A = {results['P_A']:.2f} kW")
        print(f"    Q_A = {results['Q_A']:.2f} kVAr")
        print(f"    S_A = {results['S_A']:.2f} kVA")
        print(f"    cos(φ_A) = {results['cos_phi_A']:.3f}")

        print(f"\n  Generator B:")
        print(f"    P_B = {results['P_B']:.2f} kW")
        print(f"    Q_B = {results['Q_B']:.2f} kVAr")
        print(f"    S_B = {results['S_B']:.2f} kVA")
        print(f"    cos(φ_B) = {results['cos_phi_B']:.3f}")

        print(f"\n  Load:")
        print(f"    P_L = {PL:.2f} kW")
        print(f"    Q_L = {results['Q_L']:.2f} kVAr")

        # Verify power balance
        P_sum = results['P_A'] + results['P_B']
        Q_sum = results['Q_A'] + results['Q_B']
        P_error = abs(P_sum - PL)
        Q_error = abs(Q_sum - results['Q_L'])

        print(f"\n  Power Balance:")
        print(f"    ΣP = {P_sum:.2f} kW (error: {P_error:.2f} kW)")
        print(f"    ΣQ = {Q_sum:.2f} kVAr (error: {Q_error:.2f} kVAr)")

        if P_error < 0.1 and Q_error < 0.1:
            print("  ✓ Power balance verified!")
        else:
            print("  ⚠ Power balance error detected")

        return True, If_B, results

    except Exception as e:
        print(f"\n✗ Calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_part_b(If_B_from_a, results_a):
    """Test Part (b) calculation"""
    print("\n" + "="*70)
    print("TEST: PART (b) - Calculate IfA with additional load")
    print("="*70)

    # Create generator parameters
    gen_a = GeneratorParameters(
        Pn=500, V1n=6300, Ifn=21.0, xs=1.5, cos_phi_n=0.85, name="Generator A"
    )
    gen_b = GeneratorParameters(
        Pn=350, V1n=6300, Ifn=16.0, xs=1.6, cos_phi_n=0.85, name="Generator B"
    )

    # Create analyzer
    analyzer = ParallelGeneratorAnalyzer(gen_a, gen_b)

    # Operating conditions
    PL = 720  # kW
    cos_phi_L = 0.8
    delta_P = 130  # kW (additional load at unity pf)
    If_B = If_B_from_a  # A (from part a)
    P_A = 360 + delta_P / 2  # Assuming equal sharing
    P_B = 360 + delta_P / 2
    V = 6300  # V

    print("\nInput Conditions:")
    print(f"  Original Load: PL = {PL} kW at cos(φ) = {cos_phi_L}")
    print(f"  Additional Load: ΔP = {delta_P} kW at cos(φ) = 1.0")
    print(f"  New Total Load: P_total = {PL + delta_P} kW")
    print(f"  Terminal Voltage: V = {V} V")
    print(f"  Generator B Field Current: If_B = {If_B:.2f} A (kept constant)")
    print(f"  Generator A Power: P_A = {P_A} kW")
    print(f"  Generator B Power: P_B = {P_B} kW")

    try:
        # Solve part (b)
        If_A, results = analyzer.solve_part_b(PL, cos_phi_L, delta_P, If_B, P_A, P_B, V)

        print("\n✓ Calculation successful!")
        print(f"\nResult: If_A = {If_A:.2f} A")

        print("\nDetailed Results:")
        print(f"  Generator A:")
        print(f"    P_A = {results['P_A']:.2f} kW")
        print(f"    Q_A = {results['Q_A']:.2f} kVAr")
        print(f"    S_A = {results['S_A']:.2f} kVA")
        print(f"    cos(φ_A) = {results['cos_phi_A']:.3f}")

        print(f"\n  Generator B:")
        print(f"    P_B = {results['P_B']:.2f} kW")
        print(f"    Q_B = {results['Q_B']:.2f} kVAr")
        print(f"    S_B = {results['S_B']:.2f} kVA")
        print(f"    cos(φ_B) = {results['cos_phi_B']:.3f}")

        print(f"\n  Total Load:")
        print(f"    P_L = {results['P_L']:.2f} kW")
        print(f"    Q_L = {results['Q_L']:.2f} kVAr")

        # Verify power balance
        P_sum = results['P_A'] + results['P_B']
        Q_sum = results['Q_A'] + results['Q_B']
        P_error = abs(P_sum - results['P_L'])
        Q_error = abs(Q_sum - results['Q_L'])

        print(f"\n  Power Balance:")
        print(f"    ΣP = {P_sum:.2f} kW (error: {P_error:.2f} kW)")
        print(f"    ΣQ = {Q_sum:.2f} kVAr (error: {Q_error:.2f} kVAr)")

        if P_error < 0.1 and Q_error < 0.1:
            print("  ✓ Power balance verified!")
        else:
            print("  ⚠ Power balance error detected")

        return True, If_A, results

    except Exception as e:
        print(f"\n✗ Calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_dynamic_simulation():
    """Test dynamic simulation"""
    print("\n" + "="*70)
    print("TEST: Dynamic Simulation")
    print("="*70)

    # Create generator parameters
    gen_a = GeneratorParameters(
        Pn=500, V1n=6300, Ifn=21.0, xs=1.5, cos_phi_n=0.85, name="Generator A"
    )

    # Create simulator
    simulator = DynamicSimulator(gen_a)

    # Simulation parameters
    Pm = 0.8  # pu
    V = 1.0   # pu
    E = 1.5   # pu
    X = 1.5   # pu
    delta_0 = np.radians(30)  # rad
    t_span = (0, 2.0)  # 2 seconds

    print("\nSimulation Parameters:")
    print(f"  Mechanical Power: Pm = {Pm} pu")
    print(f"  Terminal Voltage: V = {V} pu")
    print(f"  Internal EMF: E = {E} pu")
    print(f"  Synchronous Reactance: X = {X} pu")
    print(f"  Initial Rotor Angle: δ₀ = {np.degrees(delta_0):.1f}°")
    print(f"  Simulation Time: {t_span[1]} seconds")

    try:
        # Run simulation with RK45
        print("\n  Running RK45 simulation...")
        results_rk45 = simulator.simulate_transient(Pm, V, E, X, t_span, delta_0, 'RK45')
        print("  ✓ RK45 simulation completed")
        print(f"    Time points: {len(results_rk45['t'])}")
        print(f"    Final rotor angle: {np.degrees(results_rk45['delta'][-1]):.2f}°")
        print(f"    Final frequency: {results_rk45['frequency'][-1]:.4f} Hz")

        # Run simulation with Euler
        print("\n  Running Euler simulation...")
        results_euler = simulator.simulate_transient(Pm, V, E, X, t_span, delta_0, 'Euler')
        print("  ✓ Euler simulation completed")
        print(f"    Time points: {len(results_euler['t'])}")
        print(f"    Final rotor angle: {np.degrees(results_euler['delta'][-1]):.2f}°")
        print(f"    Final frequency: {results_euler['frequency'][-1]:.4f} Hz")

        # Compare methods
        angle_diff = abs(np.degrees(results_rk45['delta'][-1]) - np.degrees(results_euler['delta'][-1]))
        print(f"\n  Difference between methods:")
        print(f"    Rotor angle: {angle_diff:.4f}°")

        return True

    except Exception as e:
        print(f"\n✗ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "SYNCHRONOUS GENERATOR ANALYZER TESTS" + " "*17 + "║")
    print("╚" + "="*68 + "╝")

    results = []

    # Test Part (a)
    success_a, If_B, results_a = test_part_a()
    results.append(("Part (a)", success_a))

    # Test Part (b) if Part (a) succeeded
    if success_a:
        success_b, If_A, results_b = test_part_b(If_B, results_a)
        results.append(("Part (b)", success_b))
    else:
        results.append(("Part (b)", False))
        print("\n⚠ Skipping Part (b) due to Part (a) failure")

    # Test dynamic simulation
    success_sim = test_dynamic_simulation()
    results.append(("Dynamic Simulation", success_sim))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    all_passed = True
    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {test_name:.<50} {status}")
        if not success:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n🎉 All tests passed successfully!")
        print("\nYou can now run the GUI application:")
        print("  python3 synchronous_generator_analyzer.py")
        return 0
    else:
        print("\n⚠ Some tests failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
