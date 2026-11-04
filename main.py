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



'''
Outputs:
Capital Cost:   ~ $ 1,867,000   ( including estimated $12,000 cost for remediating mold ) 
Energy ROI:   ~ 5. 55
Volume of Ethanol Out : ~ 68.70 * 10^3 gal/day   (too low)
Purity   of Ethanol   Out:   87 %   (not good enough   per requirements, need 9 8 %+ )
'''

def calcDensityMixture(components: dict):
    sum = 0
    for density, mass_percent in components.items():
        sum += mass_percent / density
    return 1 / sum

def calcFluidMass(fluidDensity, volumetricFlowRate, timeElapsed):
    return fluidDensity * volumetricFlowRate * timeElapsed

def calcFluidVelocity(volumetricFlowRate, pipe_Diameter):
    return volumetricFlowRate / (math.pi * (pipe_Diameter/2)**2)

def energyLostToPump(energyInput):
    return (1 - PUMP_EFFICIENCY) * energyInput

# For a given pipe
def energyLostToFriction(fluidMass, frictionFactor, pipeLength, pipeDiameter, volumetricFlowRate):
    return fluidMass * frictionFactor * (8 * volumetricFlowRate**2 * pipeLength) / ((math.pi)**2 * (pipeDiameter)**5)

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

    fluidMass = calcFluidMass(fluidDensity, DAILY_FLOW_RATE, 1) # Just run it for 1 day 

    initialMasses = [
        fluidMass * SLURRY_PERCENT_WEIGHT_SUGAR,
        fluidMass * SLURRY_PERCENT_WEIGHT_ETHANOL,
        fluidMass * SLURRY_PERCENT_WEIGHT_FIBROUS,
        fluidMass * SLURRY_PERCENT_WEIGHT_WATER
    ]

    units = runProductionLine(initialMasses, units)

    for unit in units:
        print(type(unit).__name__)
        print("Output masses:", unit.getOutputs())
        print("Total mass:", unit.getTotalMassOutput())
        print("Purity:", unit.getOutputPurity())
        print()






if __name__ == "__main__":
    main()
    