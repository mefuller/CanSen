import cantera as ct
import sys

def equivalence_ratio(gas,eqRatio,fuel,oxidizer,completeProducts,additionalSpecies,):
    num_H_fuel = 0
    num_C_fuel = 0
    num_O_fuel = 0
    num_H_oxid = 0
    num_C_oxid = 0
    num_O_oxid = 0
    num_H_cprod = 0
    num_C_cprod = 0
    num_O_cprod = 0
    reactants = ''
    #fuel_tot = sum(fuel.values())
    for species, fuel_amt in fuel.items():
        num_H_fuel += gas.n_atoms(species,'H')*fuel_amt
        num_C_fuel += gas.n_atoms(species,'C')*fuel_amt
        num_O_fuel += gas.n_atoms(species,'O')*fuel_amt
    
    #oxid_tot = sum(oxidizer.values())
    for species, oxid_amt in oxidizer.items():
        num_H_oxid += gas.n_atoms(species,'H')*oxid_amt
        num_C_oxid += gas.n_atoms(species,'C')*oxid_amt
        num_O_oxid += gas.n_atoms(species,'O')*oxid_amt
        
    num_H_req = num_H_fuel + num_H_oxid
    num_C_req = num_C_fuel + num_C_oxid
    
    for species in completeProducts:
        num_H_cprod += gas.n_atoms(species,'H')
        num_C_cprod += gas.n_atoms(species,'C')
    
    if num_H_cprod > 0:    
        if num_H_req == 0:
            print('Error: All elements specified in the Complete Products must be in the Fuel or Oxidizer')
            sys.exit(1)
            
        H_multiplier = num_H_req/num_H_cprod
    else:
        H_multiplier = 0
    
    if num_C_cprod > 0:
        if num_C_req == 0:
            print('Error: All elements specified in the Complete Products must be in the Fuel or Oxidizer')
            sys.exit(1)
            
        C_multiplier = num_C_req/num_C_cprod
    else:
        C_multiplier = 0
    
    for species in completeProducts:
        num_C = gas.n_atoms(species,'C')
        num_H = gas.n_atoms(species,'H')
        num_O = gas.n_atoms(species,'O')
        if num_C > 0:
            num_O_cprod += num_O * C_multiplier
        elif num_H > 0:
            num_O_cprod += num_O * H_multiplier
    
    O_mult = (num_O_cprod - num_O_fuel)/num_O_oxid
    print(O_mult)
    
    totalOxidMoles = sum([O_mult * amt for amt in oxidizer.values()])
    totalFuelMoles = sum([eqRatio * amt for amt in fuel.values()])
    totalReactantMoles = totalOxidMoles + totalFuelMoles
    print(totalReactantMoles)
    
    if additionalSpecies:
        totalAdditionalSpecies = sum(additionalSpecies.values())
        if totalAdditionalSpecies >= 1:
            print('Error: Additional species must sum to less than 1')
        remain = 1 - totalAdditionalSpecies
        for species, molefrac in additionalSpecies.items():
            qwer = ':'.join([species,str(molefrac)])
            reactants = ','.join([reactants,qwer])
    else:
        remain = 1
    moles = []
    for species,ox_amt in oxidizer.items():
        molefrac = ox_amt * O_mult/totalReactantMoles * remain
        moles.append(molefrac)
        qwer = ':'.join([species,str(molefrac)])
        reactants = ','.join([reactants,qwer])
    
    for species, fuel_amt in fuel.items():
        molefrac = fuel_amt * eqRatio /totalReactantMoles * remain
        moles.append(molefrac)
        qwer = ':'.join([species,str(molefrac)])
        reactants = ','.join([reactants,qwer])
        
    print(reactants,sum(moles))
    sys.exit(0)


def constant_volume_reactor(mechFilename,saveFilename,keywords):
    gas = ct.Solution(mechFilename)
    initialTemp = keywords['temperature']
    initialPres = keywords['pressure']*ct.one_atm
    if 'eqRatio' in keywords:
        reactants = equivalence_ratio(gas,keywords['eqRatio'],keywords['fuel'],
                                      keywords['oxidizer'],
                                      keywords['completeProducts'],
                                      keywords['additionalSpecies'],
                                     )
    else:
        reactants = ','.join(keywords['reactants'])
    gas.TPX = initialTemp, initialPres, reactants
    reac = ct.Reactor(gas)
    netw = ct.ReactorNet([reac])
    if 'abstol' in keywords:
        netw.atol = keywords['abstol']
    if 'reltol' in keywords:
        netw.rtol = keywords['reltol']
    tend = keywords['endTime']
    time = 0
    if 'tempLimit' in keywords:
        tempLimit = keywords['tempLimit']
    else:
        tempLimit = keywords['tempThresh'] + keywords['temperature']
    while time < tend:
        time = netw.step(tend)
        #print(time,reac.T,reac.thermo.P)
        if reac.T > tempLimit:
            print(time,reac.T,reac.thermo.P)
            break
            
def constant_pressure_reactor(mechFilename,saveFilename,keywords):
    gas = ct.Solution(mechFilename)
    initialTemp = keywords['temperature']
    initialPres = keywords['pressure']*ct.one_atm
    reactants = ','.join(keywords['reactants'])
    gas.TPX = initialTemp, initialPres, reactants
    reac = ct.ConstPressureReactor(gas)
    netw = ct.ReactorNet([reac])
    tend = keywords['endTime']
    tempLimit = keywords['tempLimit'] + keywords['temperature']
    time = 0
    while time < tend:
        time = netw.step(tend)
        if reac.T > tempLimit:
            print(time,reac.T, reac.thermo.P)
            break
#gas = ct.Solution('mech.cti')
#gas.TPX = 1000,101325,'H2:2,O2:1,N2:3.76'
#reac = ct.Reactor(gas)
#netw = ct.ReactorNet([reac])
#tend = 10
#time = 0
#while time < tend:
#    time = netw.step(tend)
#    print(time,reac.T,reac.thermo.P)
#    if reac.T > 1400:
#        break

