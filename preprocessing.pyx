from Network import *
from Read_data import *
from Classes import *
from Parameters import *
from vaccination import *
from customTypes cimport person, changes
from Model import simulation



cdef refuseVaccination(dataframe, sim):
    """This function handles creating vaccine refusers. When someone in a household
    refuses  a vaccine, the rest of the household has a higher change to refuse a
    vaccine too."""
    cdef person p
    # we start by decreasing the readiness for a vaccine for some people.
    ages = dataframe["Start of age group"].tolist()
    keys = [*vaccReadiness]
    youngestRefuser = ages[keys[0]]

    # create a list of the start indices
    indices = [ages[i] for i in keys]

    # get number of people, change the percentage to a number
    refusers = [int((100 - vaccReadiness[keys[i]]) * (N / 100)) for i in range((len(indices)))]
    total = int(sum(refusers))
    # as long as there are people that refuse the vaccine we do the following
    while(total > 0):
        index = random.choice(range(youngestRefuser, N - 1))
        p = sim.people[index]
        while(p.dontVaccme):
            index = random.choice(range(youngestRefuser, N - 1))
            p = sim.people[index]
        age = p.age
        # find out if we can still let people of this age refuse
        list = [x for x in keys if x < age]
        try:
            if refusers[len(list) - 1] > 0:
                # lower list of refusers
                refusers[len(list) - 1] -= 1
                total -= 1
                p.dontVaccme = True
                sim.people[index] = p
        except:
            pass

        # give the rest of the household a certain change to also refuse the vaccine
        id = p.household
        if(id > 0):
            # get all the ids of people in the household
            for i in sim.housedict[id].ids :
                if random.uniform(0,1) < chanceToRefuse:
                    # if they already refuse a vaccine nothing changes, 
                    # if not they now refuse one
                    if(not sim.people[i]["dontVaccme"]):
                        # find out if we can still let people of this age refuse
                        list = [x for x in indices if x < age]
                        try:
                            if refusers[len(list) - 1] > 0:
                                p = sim.people[i] 
                                p.dontVaccme = True
                                sim.people[i] = p
                                refusers[len(list) - 1] -= 1
                                total -=1
                        except:
                            pass
                            
    return sim


cdef reconstruct_vaccination(files, data, sim):
    "This function will reconstruct the vaccination of people in the past 6 months"
    cdef person p
    previouslyVaccinated = readVacciation(files["previouslyVaccinated"])
    ages = data["Start of age group"].tolist()

    # percentage of people of an age group that is already vaccinated
    alreadyVaccinated = [0 for i in range(len(previouslyVaccinated.index))]

    # list with all indices of the startages
    indices = []
    indices.append(ages[12])
    for i in range(1,16) :
        age = 2022 - int(previouslyVaccinated["age"][i][0:4])
        indices.append(ages[age])

    # we loop through all the weeks we have data off to see how many people
    # have gotten vaccinated in that week
    time = len(previouslyVaccinated.columns)
    week = 1
    gevaccineerd = 0
    #listOfNubers = []
    while (week < time):
        weeklyData = previouslyVaccinated[week]
        week += 1

        # now we vaccinate in proportion to the data
        for i in range(1,len(previouslyVaccinated.index)) :
            index, currentRange = getIndex(indices,i)
            # number of people we are going to vaccinate
            next = weeklyData[i] - alreadyVaccinated[i]
            number = int(next*0.01*(currentRange))
            if number > 0:
                for j in range(number) :
                    # we keep trying to pick a new index until we found someone who
                    # has not been vaccinated yet and vaccinate that person
                    p = sim.people[index]
                    while(p.vaccinated != 0) :
                        index, x = getIndex(indices,i)
                        p = sim.people[index]
                    p.vaccinated = 1
                    gevaccineerd += 1
                    p.weekOfVaccination = week
                    sim.people[index] = p
        alreadyVaccinated = previouslyVaccinated[week-1]
    print("procent gevaccineerd", gevaccineerd/N*100)
    return sim

cdef getIndex(list indices, int i):
    """This function takes a list of indices indicating the start of
    an age group, a start age and returns an index of someone within the range
    of people with a certain age."""
    if i == 1:
        begin = indices[0]
    else:
        begin = indices[i - 1]
    if i == 16:
        end = N
    else:
        end = indices[i]
    index = random.choice(range(begin, end))
    return index, end-begin
    
cdef initialiseProtection(sim) :
    """ this function gives a number of people protection for Covid per week based on the number 
    of people that are infected in the Netherlands on average in a week. This function is needed
    to prevent a peak in the beginning."""
    number = int(initProtect*N)
    for i in range(1,5) :
       for k in range(number) :
           index = random.choice(range(0,N-1))
           while sim.people[index]["daysSinceRecovery"] > 1 or \
                 sim.people[index]["susceptible"] == 0:
               index = random.choice(range(0,N-1))
           sim.people[index]["daysSinceRecovery"]  = i*7
           sim.people[index]["infectionProtected"] = 1
    return sim


cdef initialiseInfections(data, tracker, sim):
    """This function reconstructs 2 weeks of infections. This is part
    of the preprocessing."""
    
    # typing the variables
    cdef person p
    cdef int startage = N -1
    
    # initialize tracker
    infections = [10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, ]

    # loop through the weeks and infect a number of people 
    for week in range(14):
        infected = 0
        while infections[week] > 0:
            index = random.choice(range(3000, N - 1))
            p = sim.people[index]
            while p.susceptible == 0:
                index = random.choice(range(3000, N - 1))
                p = sim.people[index]
            p.daysSinceInfection = 1
            sim.people[index] = p
            infections[week] -= 1
            infected += 1
            
        sim.update(data['IFR'])
    return sim

def VaccinationEffectiveness():
    list = []
    weeks = int(time / 7) + 50
    for t in range(weeks):
        list.append(min(begin*(growFactor**t), 1))
    return list

def pmeetinglist():
    list = []
    for t in range(100):
        p = 1 - (1 - P_MEETING) ** t 
        list.append(p)
    return list
def preprocessing(files, data, sim):
    """In this function we do the preprocessing that has to be done before we
    can start simulating. This consists of letting a percentage of the people
    refuse a vaccine, giving a percentage of the population a vaccine and
    reconstructing the infections that happened 14 timesteps prior to starting the
    simulation. """

    sim = refuseVaccination(data, sim)
    sim = reconstruct_vaccination(files, data, sim)
    #sim = initialiseInfections(data, tracker, sim)
    sim = initialiseProtection(sim)

    return sim


    
