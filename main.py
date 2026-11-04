import math
from units import Fermenter, Filter, Distiller, Dehydrator



# DESIGN VARIABLES (assumed)

DAILY_FLOW_RATE = 3161.58 # m3/day
NUM_VALVES = 8
NUM_BENDS = 4 # 90 degrees

PUMP_EFFICIENCY = 0.8

FERMENTER_EFFICIENCY = 0.5
FILTER_EFFICIENCY = 0.5
DISTILLER_EFFICIENCY = 0.81
DEHYDRATOR_EFFICIENCY = 0.5

FERMENTER_ENERGY = 46600 # kWh/day
DISTILLER_ENERGY = 47004 # kWh/day
FILTER_ENERGY = 48800 # kWh/day
DEHYDRATOR_ENERGY = 48800 # kWh/day

'''
Placeholder
'''
SITE_COST = 0 
OTHER_COSTS = 0



# CONSTANTS

ETHANOL_ENERGY_DENSITY = 21160.18 # MJ/m3
SUGAR_TO_CO2_RATIO = 0.49
DENSITY_SUGAR = 1599 # kg/m3
DENSITY_ETHANOL = 789.00 # kg/m3
DENSITY_FIBROUS = 1311 # kg/m3
DENSITY_WATER = 997 # kg/m3

SLURRY_PERCENT_WEIGHT_SUGAR = 0.20
SLURRY_PERCENT_WEIGHT_ETHANOL = 0
SLURRY_PERCENT_WEIGHT_FIBROUS = 0.20
SLURRY_PERCENT_WEIGHT_WATER = 0.60


# Uses a weighted average with mass percents as weights
# Unconventional, since volume ratios are typically used for weighted avg
# I'm using these ONLY because it aligns with the model validation provided
# And using a more "proper" way deviates from validation data
def calcDensityMixture(components: dict):
    return sum(rho * m_p for rho,m_p in components.items())


def calcFluidMass(fluidDensity, volumetricFlowRate, timeElapsed):
    return fluidDensity * volumetricFlowRate * timeElapsed

def calcFluidVelocity(volumetricFlowRate, pipe_Diameter):
    return volumetricFlowRate / (math.pi * (pipe_Diameter/2)**2)

def energyLostToPump(energyInput):
    return (1 - PUMP_EFFICIENCY) * energyInput

# For a given pipe
def energyLostToFriction(fluidMass, frictionFactor, pipeLength, 
        pipeDiameter, volumetricFlowRate):

    # Had to split things up to ensure line isn't 80+ chars long
    top = fluidMass * frictionFactor * (8 * volumetricFlowRate**2 * pipeLength)
    bottom = ((math.pi)**2 * (pipeDiameter)**5)
    return top / bottom

# Per bend
def energyLostToBend(fluidMass, pipeBendFactor, fluidVelocity):
    return 1/2 * fluidMass * pipeBendFactor * fluidVelocity**2

# Per valve
def energyLostToValve(fluidMass, lossCoefficient, fluidVelocity):
    return 1/2 * fluidMass * lossCoefficient * fluidVelocity**2


def runProductionLine(initialMasses, units):

    state = initialMasses
    outputs = []

    # Units needs to be a list of tuples with each tuple consisting
    # of the unit's class, its efficiency, and its energy input
    for unitClass, efficiency, energy in units:

        # We initialize an instance of unitClass, whether that's
        # Fermenter, Filter, Distiller, or Dehydrator

        # We treat the current mass flows of each "thing" as a state vector
        # The output of each machine is the input of the next one
        unit = unitClass(efficiency, energy, *state)
        outputs.append(unit)
        state = unit.getOutputs()

    return outputs

def main():
    units = [
        (Fermenter, FERMENTER_EFFICIENCY, FERMENTER_ENERGY),
        (Filter, FILTER_EFFICIENCY, FILTER_ENERGY),
        (Distiller, DISTILLER_EFFICIENCY, DISTILLER_ENERGY),
        (Dehydrator, DEHYDRATOR_EFFICIENCY, DEHYDRATOR_ENERGY)
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

        print()
        print()







if __name__ == "__main__":
    main()
    