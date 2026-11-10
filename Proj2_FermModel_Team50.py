import sys; args = sys.argv[1:] # Neat to grab command line args
from units import Fermenter, Filter, Distiller, Dehydrator
from utils import *
from pipe import Pipe, Duct, createPipes
from pump import Pump
from catalog import FERMENTER_OPTIONS

'''
DESIGN VARIABLES
'''

UNIT_TIERS = ["world-class", "premium", "average", "world-class"]
PUMP_TIER = "value"
PUMP_HEIGHT = 36 # effective pipe rating (m)

# Elevations of unit outlets relative to ground (feet, but we'll convert)
# Fermenter, filter, distiller, dehydrator
UNIT_ELEVATIONS = [40, 20, 0, 0]


# Expansion and contraction coefficients and calculations
CC = 0.6 # Coefficient of contraction, ASSUME sharp orifice
         # The smaller the coefficient, the higher the losses


# To calculate cross sectional areas where pipes flow in (ft^2)
# fermenter, fillter, distiller, dehydrator
UNIT_INLET_AREAS = [200, 400, 400, 200] 
UNIT_OUTLET_AREAS = [400, 400, 200, 200]



# Length in FEET but diameter in meters
# Tier is as per the parts catalog
# Source is None for initial slurry, 
# Fluid direction is either -1 (fluid goes down)
# 0 (fluid goes horizontally)
# 1 (fluid goes up)
# Bend is a list of angles
# Valves is a list of tiers (of valves)


# Again, lengths (1st param) are in feet

# Length, diameter, tier, source, fluidDirection, bends, valves

PIPE_CONFIGS = [
    (35, 0.10, "salvage", None, 1, [90], ["outstanding"]),           # INPUT
    (10, 0.10, "nice", "fermenter", -1, [], ["outstanding", "outstanding"]),# FERMENTER OUTPUT
    (10, 0.10, "nice", "filter", -1, [], ["outstanding", "outstanding"]),       # FILTER OUTPUT
    (10, 0.10, "better", "distiller", 0, [], ["outstanding", "outstanding"]),    # DISTILLER OUTPUT

    (10, 1.00, "DUCTSDONTHAVETIERS", "fermenter-waste", 1, [], []),    # CO2 
    (1, 0.10, "salvage", "filter-waste", 0, [], []),     # FILTER WASTE
    (1, 0.10, "salvage", "distiller-waste", 0, [], []),     # DISTILLER WASTE
    (1, 0.10, "salvage", "dehydrator-waste", 0, [], [])     # DEHYDRATOR WASTE

]


# 0.3048 meters per foot. Internal diameters are in meters, but lengths are in feet.
pipeConfigs = [(l*M_PER_FT, d, t, s, f, b, v) 
               for l, d, t, s, f,  b, v in PIPE_CONFIGS]
UNIT_ELEVATIONS = [h * M_PER_FT for h in UNIT_ELEVATIONS]

# Going from ft2 to m2 requires squaring conversion factor
UNIT_INLET_AREAS = [a * (M_PER_FT)**2 for a in UNIT_INLET_AREAS]
UNIT_OUTLET_AREAS = [a * (M_PER_FT)**2 for a in UNIT_OUTLET_AREAS]

'''
Costs
'''
BASE_COST = 1600000 * 1.1 # USD, this is Site 3, with 10% upfront tax
MOLD_COST = 18000 # USD, worst-case scenario - best-case was calculated to be $12000
SITE_COST = BASE_COST + MOLD_COST



def main():

    verbose = "-v" in args
    tiers = [arg for arg in args if arg != "-v"]

    if len(tiers) == 0:
        unitTiers = UNIT_TIERS

    elif len(tiers) == 4:
        unitTiers = tiers

    else:
        print("Try again! You need either 0 or 4 tiers.")
        sys.exit(0) 

    allowable = ["scrap", "average", "premium", "world-class"]
    for arg in tiers:
        if arg not in allowable:
            print("Invalid arguments!")
            sys.exit(0)
    
    fermenterTier, filterTier, distillerTier, dehydratorTier = unitTiers

    # This is now a dynamic quantity. We will minimize the slurry needed. 
    # Round up so we don't go under.
    DAILY_FLOW_RATE = math.ceil(
        calcRequiredSlurryFlowRate(FERMENTER_OPTIONS[fermenterTier][0])
        )

    FLOW_RATE = DAILY_FLOW_RATE / SECONDS_PER_DAY


    
    units = [
        (Fermenter, fermenterTier),
        (Filter, filterTier),
        (Distiller, distillerTier),
        (Dehydrator, dehydratorTier)
    ]

    fluidDensity = calcDensityMixture(SLURRY_COMPONENTS)

    # Just run it for 1 day 
    fluidMass = calcFluidMass(fluidDensity, DAILY_FLOW_RATE, 1)

    initialMasses = [
        fluidMass * SLURRY_PERCENT_WEIGHT_SUGAR,
        fluidMass * SLURRY_PERCENT_WEIGHT_ETHANOL,
        fluidMass * SLURRY_PERCENT_WEIGHT_FIBROUS,
        fluidMass * SLURRY_PERCENT_WEIGHT_WATER
    ]

    # Runs simulation of the units to get final masses
    units = runProductionLine(initialMasses, units)

    pipes = createPipes(pipeConfigs, units, FLOW_RATE, fluidDensity)

    wastePotentialEnergy = 0

    for i, pipe in enumerate(pipes[4:]):
        outletHeight = UNIT_ELEVATIONS[i] + pipe.heightChange
        wastePotentialEnergy += pipe.getGravitationalPEChange(outletHeight)

    # Only the kinetic energy flowing out of the system should count
    # This includes waste pipes/ducts and the final product output
    wasteKineticEnergy = sum(pipe.getKineticEnergy() for pipe in pipes[4:])

    outputKineticEnergy = 0 # Since we no longer have an output pipe, we 
                            # don't know discharge velocity

    outputPotentialEnergy = (units[-1].getTotalMassOutput() 
                             * LITTLE_G * UNIT_ELEVATIONS[-1])

    pipeCapitalCost = sum(pipe.getCapitalCost() for pipe in pipes)

    # IMPORTANT IMPORTANT IMPORTANT ASSUMPTION
    # We assume that main pump is providing energy for the whole system
    # Including pumping out waste
    pipeEnergyLoss = sum(pipe.getEnergyLoss() for pipe in pipes)


    transitionEnergyLoss = 0


    # i pretty much represents the index of the unit
    for i in range(4):
        # Expansion is when fluid goes from a pipe 
        # to a (much) larger unit operation tank
        inletPipe = pipes[i]
        inletArea = math.pi * (inletPipe.diameter/ 2)**2

        expansionHead = suddenExpansionLoss(
            inletPipe.flowRate, inletArea, UNIT_INLET_AREAS[i]
        )

        transitionEnergyLoss += (
            inletPipe.getFluidMass() * LITTLE_G * expansionHead
        )

        # Now we deal with the outgoing from units, contraction
        # Going from a large cross sectional area to a smaller pipe
        if i < 3:
            outletPipe = pipes[i + 1]
            outletArea = math.pi * (outletPipe.diameter / 2)**2
            contractionHead = suddenContractionLoss(
                outletPipe.flowRate, UNIT_OUTLET_AREAS[i], outletArea, CC
            )

            transitionEnergyLoss += (
                outletPipe.getFluidMass() * LITTLE_G * contractionHead
            )
    
    hydraulicEnergy = (
        pipeEnergyLoss + 
        transitionEnergyLoss +
        wastePotentialEnergy +
        wasteKineticEnergy + 
        outputPotentialEnergy + 
        outputKineticEnergy
        )

    pump = Pump(PUMP_TIER, PUMP_HEIGHT, FLOW_RATE)

    pumpEnergy = pump.getEnergyKWh(hydraulicEnergy)
    pumpCapitalCost = pump.getCapitalCost()

    # FINAL SYSTEM OUTPUTS

    finalUnit = units[-1]

    # Final product
    finalMass = finalUnit.getTotalMassOutput()
    finalPurity = finalUnit.getOutputPurity()
    ethanolMass = finalUnit.getEthanol()

    # Calculate final product volume
    finalDensity = calcDensityMixture({
        DENSITY_SUGAR: finalUnit.getSugar() / finalMass,
        DENSITY_ETHANOL: finalUnit.getEthanol() / finalMass,
        DENSITY_FIBROUS: finalUnit.getFibrous() / finalMass,
        DENSITY_WATER: finalUnit.getWater() / finalMass
    })

    finalVolume = finalMass / finalDensity
    finalGallons = finalVolume * GAL_PER_M3

    # Capital costs (unit operations only)
    unitCapitalCost = sum(unit.getCapitalCost() for unit in units)

    # Total costs
    totalCost = unitCapitalCost + pipeCapitalCost + pumpCapitalCost + SITE_COST

    # Electrical energy used by unit operations
    totalEnergy = sum(unit.getEnergy() for unit in units) + pumpEnergy

    # Ethanol energy output (MJ/day)
    ethanolVolume = ethanolMass / DENSITY_ETHANOL
    ethanolGallons = ethanolVolume * GAL_PER_M3
    
    energyOutput = ethanolVolume * ETHANOL_ENERGY_DENSITY

    # Energy ROI (kWh->MJ is a factor of 3.6)
    energyROI = energyOutput / (totalEnergy * 3.6)

    if verbose:
        # Final summary
        print("=" * 50)
        print("ETHANOL PRODUCTION FACILITY - SYSTEM SUMMARY")
        print("=" * 50)
        print()

        print("PRODUCTION")
        print(f"Initial Slurry: {DAILY_FLOW_RATE:,.2f} m3/day")
        print(f"Final Product: {finalGallons:,.2f} gal/day")
        print(f"Ethanol Produced: {ethanolMass:,.2f} kg/day")
        print(f"Ethanol Purity: {finalPurity:.2%}")
        print()

        print("ENERGY")
        print(f"Pipe Losses: {pipeEnergyLoss/1000:,.2f} kJ/day")
        print(f"Waste GPE: {wastePotentialEnergy/1000:,.2f} kJ/day")
        print(f"Waste KE: {wasteKineticEnergy/1000:,.2f} kJ/day")
        print(f"Output GPE: {outputPotentialEnergy/1000:,.2f} kJ/day")
        print(f"Output KE: {outputKineticEnergy/1000:,.2f} kJ/day")
        print(f"Pump Electricity: {pumpEnergy:,.2f} kWh/day")

        print(f"Expansion/Contraction Loss: {transitionEnergyLoss/1000:,.2f} kJ/day")

        print(f"Electrical Input: {totalEnergy:,.2f} kWh/day")
        print(f"Ethanol Energy: {energyOutput:,.2f} MJ/day")
        print(f"Energy ROI: {energyROI:.2f}")
        print()

        print("CAPITAL COSTS")
        print(f"Unit Operations: ${unitCapitalCost:,.2f}")
        print(f"Pipe and Duct Costs: ${pipeCapitalCost:,.2f}")
        print(f"Pump: ${pumpCapitalCost:,.2f}")
        print()

        print("TOTAL COST")
        print(f"${totalCost:,.2f}")
        print()

        print("REQUIREMENTS")
        print(f"Production Target: 100000 gal/day")
        print(f"Purity Target: 98%")
        print(f"Production Met: {finalGallons >= 100000}")
        print(f"Purity Met: {finalPurity >= 0.98}")
        print()
    else:
        print()
        print("Use 'python main.py -v' to get more detailed results!")
        print()
        print(f"Pure Ethanol: {ethanolGallons:,.2f} gal/day")
        print(f"Ethanol Purity: {finalPurity:.2%}")
        print(f"Energy ROI: {energyROI:.2f}")
        print(f"Total Capital Cost: ${totalCost:,.2f}")
        print(f"Required Slurry: {DAILY_FLOW_RATE:,.2f} m3/day")
        print()

        productionMet = ethanolGallons >= TARGET_GALLONS
        purityMet = finalPurity >= 0.98

        print(f"Production Met: {productionMet}")
        print(f"Purity Met: {purityMet}")
        print()









if __name__ == "__main__":
    main()
    
