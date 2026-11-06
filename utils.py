import math

# Constants

DENSITY_SUGAR = 1599
DENSITY_ETHANOL = 789.00
DENSITY_FIBROUS = 1311
DENSITY_WATER = 997

SECONDS_PER_DAY = 86400

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

def energyLostToPump(energyInput, pumpEfficiency):
    return (1 - pumpEfficiency) * energyInput

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
    for unitClass, efficiency, energy, costPerM3PerSec in units:

        # We initialize an instance of unitClass, whether that's
        # Fermenter, Filter, Distiller, or Dehydrator

        # We treat the current mass flows of each "thing" as a state vector
        # The output of each machine is the input of the next one
        unit = unitClass(efficiency, energy, costPerM3PerSec, *state)
        outputs.append(unit)
        state = unit.getOutputs()

    return outputs
