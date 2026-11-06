from utils import energyLostToFriction, calcFluidVelocity, SECONDS_PER_DAY
from catalog import PIPE_OPTIONS, DUCTWORK_OPTIONS, DUCTWORK_FRICTION_FACTOR


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

        # If the pipe is coming from somewhere, then use its output flow
        if source is not None:
            match source:
                case "fermenter":
                    return 0
                case "filter":
                    return 1
                case "distiller":
                    return 2
                case "dehydrator":
                    return 3
                case _:
                    raise Exception("Unknown pipe source")
            
            flowRate = units[source].getOutputFlowRate()
            density = units[source].getOutputDensity()

        # Initial slurry pipe, so initial slurry flow
        else:
            flowRate = initialFlowRate
            density = initialDensity

        # Make a pipe obejct
        pipe = Pipe(
            length=length,
            diameter=diameter,
            tier=tier,
            flowRate=flowRate,
            density=density
        )

        pipes.append(pipe)

    return pipes