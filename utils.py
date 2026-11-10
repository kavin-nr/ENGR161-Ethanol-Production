import math

# Constants

DENSITY_SUGAR = 1599 # kg/m3
DENSITY_ETHANOL = 789.00 # kg/m3
DENSITY_FIBROUS = 1311 # kg/m3
DENSITY_WATER = 997 # kg/m3

DENSITY_CO2 = 1.80 # kg/m3 at room temperature

SECONDS_PER_DAY = 86400
M_PER_FT = 0.3048
GAL_PER_M3 = 264.172
LITTLE_G = 9.81 # m/s2

ETHANOL_ENERGY_DENSITY = 21160.18 # MJ/m3

TARGET_GALLONS = 100000 # gal of ethanol/day


# Retired. These are no longer constants.
# DAILY_FLOW_RATE = 0 # m3/day
# FLOW_RATE = DAILY_FLOW_RATE / SECONDS_PER_DAY # m3/s

# Initial slurry components
SLURRY_PERCENT_WEIGHT_SUGAR = 0.20
SLURRY_PERCENT_WEIGHT_ETHANOL = 0
SLURRY_PERCENT_WEIGHT_FIBROUS = 0.20
SLURRY_PERCENT_WEIGHT_WATER = 0.60

SLURRY_COMPONENTS = {

    DENSITY_SUGAR: SLURRY_PERCENT_WEIGHT_SUGAR, 
    DENSITY_ETHANOL: SLURRY_PERCENT_WEIGHT_ETHANOL,
    DENSITY_FIBROUS: SLURRY_PERCENT_WEIGHT_FIBROUS,
    DENSITY_WATER: SLURRY_PERCENT_WEIGHT_WATER    

    }



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

def suddenExpansionLoss(flowRate, area1, area2):
    
    velocity1 = flowRate / area1
    velocity2 = flowRate / area2
    
    headLoss = (velocity1 - velocity2)**2 / (2 * LITTLE_G)
    
    return headLoss

def suddenContractionLoss(flowRate, area1, area2, Cc):
    
    velocity2 = flowRate / area2
    
    Kc = (1 / Cc - 1)**2 # contraction loss coefficient
    
    headLoss = Kc * velocity2 ** 2 / (2 * LITTLE_G)
    
    return headLoss


def calcRequiredSlurryFlowRate(fermenterEfficiency):

    slurryDensity = calcDensityMixture(SLURRY_COMPONENTS)

    targetEthanolVolume = TARGET_GALLONS / GAL_PER_M3
    targetEthanolMass = targetEthanolVolume * DENSITY_ETHANOL

    # this is how many kg of ethanol is in per m3 of slurry
    ethanolMassPerM3 = (slurryDensity * SLURRY_PERCENT_WEIGHT_SUGAR * 0.51 * 
                        fermenterEfficiency)

    return targetEthanolMass / ethanolMassPerM3

def runProductionLine(initialMasses, units):

    state = initialMasses
    outputs = []

    # Units needs to be a list of tuples with each tuple consisting
    # of the class and a string representing the tier.
    for unitClass, tier in units:

        # We initialize an instance of unitClass, whether that's
        # Fermenter, Filter, Distiller, or Dehydrator

        # We treat the current mass flows of each "thing" as a state vector
        # The output of each machine is the input of the next one
        unit = unitClass(tier, *state)
        outputs.append(unit)
        state = unit.getOutputs()

    return outputs
