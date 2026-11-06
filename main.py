import sys; args = sys.argv[1:] # Neat to grab command line args
from units import Fermenter, Filter, Distiller, Dehydrator
from utils import *
from pipe import Pipe


# DESIGN VARIABLES (assumed)

DAILY_FLOW_RATE = 3161.58 # m3/day
FLOW_RATE = 3161.58 / SECONDS_PER_DAY # m3/s
NUM_VALVES = 8
NUM_BENDS = 4 # 90 degrees

PUMP_EFFICIENCY = 0.8

'''
Costs
'''
BASE_COST = 1600000 * 1.1 # USD, this is Site 3, with 10% upfront tax
MOLD_COST = 18000 # USD, worst-case scenario
SITE_COST = BASE_COST + MOLD_COST



def main():

    if len(args) != 4:
        print("Try again! You need 4 tiers.")
        sys.exit(0) 
    allowable = ["scrap", "average", "premium", "world-class"]
    for arg in args:
        if arg not in allowable:
            print("Invalid arguments!")
            sys.exit(0)
    
    fermenterTier, filterTier, distillerTier, dehydratorTier = args

    
    
    units = [
        (Fermenter, fermenterTier),
        (Filter, filterTier),
        (Distiller, distillerTier),
        (Dehydrator, dehydratorTier)
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
    finalGallons = finalVolume * 264.172

    # Capital costs (unit operations only)
    unitCapitalCost = sum(unit.getCapitalCost() for unit in units)

    # Total costs
    totalCost = unitCapitalCost + SITE_COST

    # Electrical energy used by unit operations
    totalEnergy = sum(unit.getEnergy() for unit in units)

    # Ethanol energy output (MJ/day)
    ethanolVolume = ethanolMass / DENSITY_ETHANOL
    energyOutput = ethanolVolume * ETHANOL_ENERGY_DENSITY

    # Energy ROI (excluding pump energy for now)
    energyROI = energyOutput / (totalEnergy * 3.6)

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
    print(f"Electrical Input: {totalEnergy:,.2f} kWh/day")
    print(f"Ethanol Energy: {energyOutput:,.2f} MJ/day")
    print(f"Energy ROI: {energyROI:.2f}")
    print()

    print("CAPITAL COSTS")
    print(f"Unit Operations: ${unitCapitalCost:,.2f}")
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








if __name__ == "__main__":
    main()
    