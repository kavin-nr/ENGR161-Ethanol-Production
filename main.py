from units import Fermenter, Filter, Distiller, Dehydrator
from utils import *

# CONSTANTS

ETHANOL_ENERGY_DENSITY = 21160.18 # MJ/m3
SUGAR_TO_CO2_RATIO = 0.49

SLURRY_PERCENT_WEIGHT_SUGAR = 0.20
SLURRY_PERCENT_WEIGHT_ETHANOL = 0
SLURRY_PERCENT_WEIGHT_FIBROUS = 0.20
SLURRY_PERCENT_WEIGHT_WATER = 0.60


# DESIGN VARIABLES (assumed)

DAILY_FLOW_RATE = 3161.58 # m3/day
FLOW_RATE = 3161.58 / SECONDS_PER_DAY # m3/s
NUM_VALVES = 8
NUM_BENDS = 4 # 90 degrees

PUMP_EFFICIENCY = 0.8

FERMENTER_EFFICIENCY = 0.5
FILTER_EFFICIENCY = 0.5
DISTILLER_EFFICIENCY = 0.81
DEHYDRATOR_EFFICIENCY = 0.5

FERMENTER_COST = 320000 # $ per m3/sec
FILTER_COST = 200000 # $ per m3/sec
DISTILLER_COST = 390000 # $ per m3/sec
DEHYDRATOR_COST = 200000 # $ per m3/sec

FERMENTER_ENERGY = 46600 # kWh/day
DISTILLER_ENERGY = 47004 # kWh/day
FILTER_ENERGY = 48800 # kWh/day
DEHYDRATOR_ENERGY = 48800 # kWh/day

'''
Placeholder
'''
SITE_COST = 0 
OTHER_COSTS = 0



def main():
    units = [
        (Fermenter, FERMENTER_EFFICIENCY, FERMENTER_ENERGY, FERMENTER_COST),
        (Filter, FILTER_EFFICIENCY, FILTER_ENERGY, FILTER_COST),
        (Distiller, DISTILLER_EFFICIENCY, DISTILLER_ENERGY, DISTILLER_COST),
        (Dehydrator, DEHYDRATOR_EFFICIENCY, DEHYDRATOR_ENERGY, DEHYDRATOR_COST)
    ]

    
    components = {

        DENSITY_SUGAR: SLURRY_PERCENT_WEIGHT_SUGAR, 
        DENSITY_ETHANOL: SLURRY_PERCENT_WEIGHT_ETHANOL,
        DENSITY_FIBROUS: SLURRY_PERCENT_WEIGHT_FIBROUS,
        DENSITY_WATER: SLURRY_PERCENT_WEIGHT_WATER
        
    }

    fluidDensity = calcDensityMixture(components)

    # Just run it for 1 day 
    fluidMass = calcFluidMass(fluidDensity, DAILY_FLOW_RATE, 1)

    initialMasses = [
        fluidMass * SLURRY_PERCENT_WEIGHT_SUGAR,
        fluidMass * SLURRY_PERCENT_WEIGHT_ETHANOL,
        fluidMass * SLURRY_PERCENT_WEIGHT_FIBROUS,
        fluidMass * SLURRY_PERCENT_WEIGHT_WATER
    ]

    units = runProductionLine(initialMasses, units)

    
    for unit in units:
        sugar, ethanol, fibrous, water = unit.getOutputs()

        # Just a lot of pretty formatting to make things pop
        print("=" * 45)
        print(type(unit).__name__.upper())
        print("=" * 45)
        print()

        print(f"Sugar Output: {sugar:,.2f} kg/day")
        print(f"Ethanol Output: {ethanol:,.2f} kg/day")
        print(f"Fibrous Output: {fibrous:,.2f} kg/day")
        print(f"Water Output: {water:,.2f} kg/day")
        print() 

        print(f"Total Mass Output: {unit.getTotalMassOutput():,.2f} kg/day")
        print(f"Ethanol Purity: {unit.getOutputPurity():.2%}")
        print(f"Energy Input: {unit.getEnergy():,.2f} kWh/day")


        print(f"Input Mass: {unit.getInputMass():,.2f} kg/day")
        print(f"Input Density: {unit.getInputDensity():,.2f} kg/m3")
        print(f"Input Flow Rate: {unit.getInputFlowRate():.6f} m3/s")
        print(f"Capital Cost: ${unit.getCapitalCost():,.2f}")

        print()
        print()







if __name__ == "__main__":
    main()
    