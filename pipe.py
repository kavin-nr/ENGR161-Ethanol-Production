from utils import energyLostToFriction, calcFluidVelocity, SECONDS_PER_DAY
from catalog import PIPE_OPTIONS, DUCTWORK_OPTIONS, DUCTWORK_FRICTION_FACTOR
import sys

class Pipe:

    def __init__(self, length, diameter, tier, flowRate, density):

        self.length = length
        self.diameter = diameter
        self.flowRate = flowRate
        self.density = density

        # Found it much easier to grab stuff from the catalog directly here
        # Keep it all contained rather than putting it in main.py
        options = PIPE_OPTIONS[tier]

        self.frictionFactor = options["frictionFactor"] # Darcy-Weisbach
        self.costPerMeter = options["costs"][diameter] # $ / m

    def getCapitalCost(self):
        return self.costPerMeter * self.length

    def getVelocity(self):
        return calcFluidVelocity(self.flowRate, self.diameter)

    def getFluidMass(self):
        return self.density * self.flowRate * SECONDS_PER_DAY

    def getEnergyLoss(self):

        # If I haven't expressed my dislike for the 80 character limit before,
        # I do here.
        return energyLostToFriction(
            self.getFluidMass(),
            self.frictionFactor,
            self.length,
            self.diameter,
            self.flowRate
        )

# If you think about it, ducts are basically pipes with a few caveats
# Just made sense to just have it as a child class 

class Duct(Pipe):

    def __init__(self, length, diameter, flowRate, density):

        self.length = length
        self.diameter = diameter
        self.flowRate = flowRate
        self.density = density
        self.frictionFactor = DUCTWORK_FRICTION_FACTOR
        self.costPerMeter = DUCTWORK_OPTIONS[diameter]

    
    # IMPORTANT TO NOTE: Darcy-Weisbach deals with the flow of incompressible
    # fluids. CO2 (going through these ducts) is a gas, so it's compressible.
    # So we probably can neglect the energyLostToFriction in these ducts. 

    # Also, the validation model says it neglects waste pipe friction. I'm 
    # just going to go with that for now. 


def createPipes(configs, units, initialFlowRate, initialDensity):
    pipes = []
    for length, diameter, tier, source in configs:
        duct = False
        # If the pipe is coming from somewhere, then use its output flow
        if source is not None:
            match source:
                case "fermenter":
                    id = 0
                case "filter":
                    id = 1
                case "distiller":
                    id = 2
                case "dehydrator":
                    id = 3
                case "fermenter-waste":
                    id = 4
                    duct = True
                case "filter-waste":
                    id = 5
                case "distiller-waste":
                    id = 6
                case "dehydrator-waste":
                    id = 7
                case _:
                    raise Exception("Unknown pipe source")

            if 0 <= id <= 3:
                flowRate = units[id].getOutputFlowRate()
                density = units[id].getOutputDensity()

            else:                  
                flowRate = units[id - 4].getWasteFlowRate()
                density = units[id - 4].getWasteDensity()

        # Initial slurry pipe, so initial slurry flow
        else:
            flowRate = initialFlowRate
            density = initialDensity

        if not duct:
            # Make a pipe obejct
            pipe = Pipe(
                length=length,
                diameter=diameter,
                tier=tier,
                flowRate=flowRate,
                density=density
            )
        else:
            pipe = Duct(
                length=length,
                diameter=diameter,
                flowRate=flowRate,
                density=density
            )

        pipes.append(pipe)

    return pipes