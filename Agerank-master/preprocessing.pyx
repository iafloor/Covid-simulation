from Network import *
from Read_data import *
from Classes import *
from Parameters import *
from vaccination import *
from customTypes cimport person, changes



def update(fatality, listOfPeople, houseDictList, otherGroupsList, nchanges):
    """This function updates the status and increments the number
    of days that a person has been infected.
    For a new infection, days[i]=1.  For uninfected persons, days[i]=0.
    Input: infection fatality rate and age of persons i
    """
    # typing the variables
    cdef person person
    cdef list people = listOfPeople, houseDict = houseDictList, otherGroups = otherGroupsList
    cdef int newinfections = 0, recovered = 0
    cdef int id
    nchanges["newInfections"] = 0
    cdef int vaccinated = 0, nonvaccinated = 0
    cdef int students = 0, youngadults = 0, parents = 0, old = 0
    
    for p in people:
        person = p
        id = person.person_id
        if person.daysSinceInfection > 0 :
            if person.daysSinceInfection == 1 :
                nchanges["newInfections"] += 1
                newinfections += 1
                vaccinated += person.vaccinated
                nonvaccinated += 1 - person.vaccinated 
                nchanges["totalInfected"] += 1
                person.susceptible = 0
                person.infectionProtected = 1
            person.daysSinceInfection += 1

        # on the day symptoms should be noticable we check if someone goes into quarantine
        # if someone does not go in quarantine because they don't want to, they don't know
        # that they have COVID or for other reasons, they stay in their household.
        # for this it doesn't matter if they have or do not have symptoms
        if person.daysSinceInfection == DAY_SYMPTOMS :
            if rd.random() < P_QUARANTINE:
	            # i gets symptoms and quarantines
                    person.quarantined = 1
            else:
	            # i gets symptoms but does not quarantine
                    houseID = person.household
                    houseDict[houseID].infected += 1
                    person.infectious = 1
                    schoolID = person.schoolClass
                    if schoolID > -1 :
                        otherGroups[schoolID].infected += 1
  
            # on the recovery day of a person we check if they recover or if they get admitted to the hospital
            # when they are hospitalised we change their status based on if they had been quarantined.
        elif person.daysSinceInfection == DAY_RECOVERY :
                if rd.random() < RATIO_HF * fatality[person.age]:
                    if person.vaccinated == 1 and rd.random() < 0.95 :
                        continue
                    person.hospitalised = 1
                    if person.quarantined != 1 :
                        person.infectious -= 1
                        houseId = person.household
                        houseDict[houseId].infected -= 1
                        schoolId = person.schoolClass
                        if schoolId > -1 :
                            otherGroups[schoolId].infected -= 1
                    else :
                        person.quarantined = 0
                    person.hospitalised = 1
                    nchanges["hospitalized"] += 1
                else:
                    if person.quarantined != 1 :
                        houseID = person.household
                        houseDict[houseID].infected -= 1
                        schoolId = person.schoolClass
                        if schoolId > -1:
                            otherGroupes[schoolId].infected -= 1
                    person.infectious = 0
                    person.quarantined = 0
                    person.daysSinceInfection = 0
                    person.recovered = 1
                    person.daysSinceRecovery = 1
                    recovered += 1

            # on the day of release of someone who has been hospitalised, they have a chance of dying
        elif person.daysSinceInfection == DAY_RELEASE:
                #nchanges["hospitalized"] -= 1
                person.hospitalised = 0
                if rd.random() < 1 / RATIO_HF:
                    person.infectious = 0
                    person.quarantined = 0
                    person.daysSinceInfection = 0
                    person.deceased = 1
                    nchanges["hospitalized"] -= 1
                    nchanges["deceased"] += 1
                    recovered += 1
                else:
                    person.infectious = 0
                    person.quarantined = 0
                    person.daysSinceInfection = 0
                    person.recovered = 1
                    person.daysSinceRecovery = 1
                    nchanges["hospitalized"] -= 1
                    recovered += 1
     
        if person.daysSinceRecovery > 0 :
            if person.daysSinceRecovery == 14 :
                person.susceptible = 1
            if person.daysSinceRecovery == protectionInfection :
                person.infectionProtected = 0 
                person.daysSinceRecovery = 0
            else : person.daysSinceRecovery += 1
        people[id] = person
    return people, houseDict, otherGroups, nchanges
    
    
def refuseVaccination(population, dataframe):
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
        p = population.people[index]
        while(p.dontVaccme):
            index = random.choice(range(youngestRefuser, N - 1))
            p = population.people[index]
        age = p.age
        # find out if we can still let people of this age refuse
        list = [x for x in keys if x < age]
        try:
            if refusers[len(list) - 1] > 0:
                # lower list of refusers
                refusers[len(list) - 1] -= 1
                total -= 1
                p.dontVaccme = True
                population.people[index] = p
        except:
            pass

        # give the rest of the household a certain change to also refuse the vaccine
        id = p.household
        if(id > 0):
            # get all the ids of people in the household
            for i in population.houseDict[id].ids :
                if random.uniform(0,1) < chanceToRefuse:
                    # if they already refuse a vaccine nothing changes, 
                    # if not they now refuse one
                    if(not population.people[i]["dontVaccme"]):
                        # find out if we can still let people of this age refuse
                        list = [x for x in indices if x < age]
                        try:
                            if refusers[len(list) - 1] > 0:
                                p = population.people[i] 
                                p.dontVaccme = True
                                population.people[i] = p
                                refusers[len(list) - 1] -= 1
                                total -=1
                        except:
                            pass
    return population


def reconstruct_vaccination(files, data, population):
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
                    p = population.people[index]
                    while(p.vaccinated != 0) :
                        index, x = getIndex(indices,i)
                        p = population.people[index]
                    p.vaccinated = 1
                    gevaccineerd += 1
                    p.weekOfVaccination = week
                    population.people[index] = p
        alreadyVaccinated = previouslyVaccinated[week-1]
    print("procent gevaccineerd", gevaccineerd/N*100)

    return population


def getIndex(indices, i):
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
    
def initialiseProtection(population) :
    """ this function gives a number of people protection for Covid per week based on the number 
    of people that are infected in the Netherlands on average in a week. This function is needed
    to prevent a peak in the beginning."""
    number = int(initProtect*N)
    for i in range(1,5) :
       for k in range(number) :
           index = random.randint(0,N-1)
           while population.people[index]["daysSinceRecovery"] == 0 and population.people[index]["susceptible"] == 1:
               index = random.randint(0,N-1)
           population.people[index]["daysSinceRecovery"]  = i*7
           population.people[index]["infectionProtected"] = 1
    return population


def initialiseInfections(data, population, tracker):
    """This function reconstructs 2 weeks of infections. This is part
    of the preprocessing."""
    
    # typing the variables
    cdef person p
    cdef changes newchanges
    cdef list people = population.people, houseDict = population.houseDict, otherGroups = population.otherGroups
    cdef int startage = N -1
    
    # initialize tracker
    newchanges.newInfections = 0
    newchanges.totalInfected = 0
    newchanges.hospitalized = 0
    newchanges.deceased = 0
    infections = [10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, ]

    # loop through the weeks and infect a number of people 
    for week in range(14):
        infected = 0
        status_changes = tracker.empty_changes()
        while infections[week] > 0:
            index = random.choice(range(3000, N - 1))
            p = people[index]
            while p.susceptible == 0:
                index = random.choice(range(3000, N - 1))
                p = people[index]
            p.daysSinceInfection = 1
            people[index] = p
            infections[week] -= 1
            infected += 1
            
        people, houseDict, otherGroups, changes = update(data['IFR'], people, houseDict, otherGroups, newchanges)
        
        
        # inpakken
        population.people = people
        population.houseDict = houseDict
        population.otherGroups = otherGroups

        # update the tracker
        tracker.update_statistics(changes)
    return population

def VaccinationEffectiveness():
    list = []
    weeks = int(time / 7) + 50
    for t in range(weeks):
        list.append(min(begin*(growFactor**t), 1))
    return list

def preprocessing(population, files, data, tracker):
    """In this function we do the preprocessing that has to be done before we
    can start simulating. This consists of letting a percentage of the people
    refuse a vaccine, giving a percentage of the population a vaccine and
    reconstructing the infections that happened 14 timesteps prior to starting the
    simulation. """

    newpopulation = refuseVaccination(population, data)
    vaccinatedPopulation = reconstruct_vaccination(files, data, newpopulation)
    infectedPopulation = initialiseInfections(data, vaccinatedPopulation, tracker)
    vaccEffectivenessList = VaccinationEffectiveness()
    protectedPopulation = initialiseProtection(infectedPopulation)
    return infectedPopulation, tracker, vaccEffectivenessList


    
