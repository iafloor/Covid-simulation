from Network import *
from Read_data import *
from Classes import *
from Parameters import *


def update(fatality, population, status_changes):
    """This function updates the status and increments the number
    of days that a person has been infected.
    For a new infection, days[i]=1.  For uninfected persons, days[i]=0.
    Input: infection fatality rate and age of persons i
    """
    new_status_changes = status_changes
    people = population.people
    for person in people:
        id = person.person_id
        if person.daysSinceInfection > 0 :
            if person.daysSinceInfection == 1 :
                new_status_changes["currently infected"] += 1
                new_status_changes["total infected"] += 1
                population.people[id].susceptible = 0
            population.people[id].daysSinceInfection += 1

        # on the day symptoms should be noticable we check if someone goes into quarantine
        # if someone does not go in quarantine because they don't want to, they don't know
        # that they have COVID or for other reasons, they stay in their household.
        # for this it doesn't matter if they have or do not have symptoms
        if person.daysSinceInfection == DAY_SYMPTOMS :
            if rd.random() < P_QUARANTINE:
                # i gets symptoms and quarantines
                population.people[id].quarantined = 1
                new_status_changes["quarantined"] += 1
            else:
                # i gets symptoms but does not quarantine
                houseID = population.people[id].household
                population.houseDict[houseID].infected += 1
                population.people[id].infectious += 1

        # on the recovery day of a person we check if they recover or if they get admitted to the hospital
        # when they are hospitalised we change their status based on if they had been quarantined.
        if person.daysSinceInfection == DAY_RECOVERY :
            if rd.random() < RATIO_HF * fatality[person.age]:
                population.people[id].hospitalised = 1
                if person.quarantined != 1 :
                    population.people[id].infectious -= 1
                    houseId = person.household
                    population.houseDict[houseId].infected -= 1
                    schoolId = person.schoolClass
                    if schoolId > -1 :
                        population.otherGroups[schoolId].infected -= 1
                else :
                    population.people[id].quarantined -= 1
                population.people[id].hospitalised += 1
                new_status_changes["hospitalized"] += 1
                new_status_changes["quarantined"] -= 1
            else:
                population.people[id].infectious = 0
                population.people[id].quarantined = 0
                population.people[id].daysSinceInfection = 0
                population.people[id].daysSinceRecovery = 1
                population.people[id].recovered = 1
                new_status_changes["recovered"] += 1
                new_status_changes["currently infected"] -= 1

        # on the day of release of someone who has been hospitalised, they have a chance of dying
        if person.daysSinceInfection == DAY_RELEASE:
            new_status_changes["hospitalized"] -= 1
            population.people[id].hospitalised = 0
            if rd.random() < 1 / RATIO_HF:
                population.people[id].infectious = 0
                population.people[id].quarantined = 0
                population.people[id].daysSinceInfection = 0
                population.people[id].deceased = 1
                new_status_changes["deceased"] += 1
                new_status_changes["currently infected"] -= 1
            else:
                population.people[id].infectious = 0
                population.people[id].quarantined = 0
                population.people[id].daysSinceInfection = 0
                population.people[id].recovered += 1
                population.people[id].daysSinceRecovery = 1
                new_status_changes["recovered"] += 1
                new_status_changes["currently infected"] += -1
        if person.daysSinceRecovery > 0 :
            if person.daysSinceRecovery == protectionInfection :
                population.people[id].susceptible = 1
                population.people[id].daysSinceRecovery = 0
            else :
                population.people[id].daysSinceRecovery += 1
    return population, new_status_changes


def refuseVaccination(population, dataframe):
    """This function handles creating vaccine refusers. When someone in a household
    refuses  a vaccine, the rest of the household has a higher change to refuse a
    vaccine too."""

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
        while(population.people[index].dontVaccme):
            index = random.choice(range(youngestRefuser, N - 1))
        age = population.people[index].age
        # find out if we can still let people of this age refuse
        list = [x for x in keys if x < age]
        try:
            if refusers[len(list) - 1] > 0:
                # lower list of refusers
                refusers[len(list) - 1] -= 1
                total -= 1
                population.people[index].dontVaccme = True
        except:
            pass

        # give the rest of the household a certain change to also refuse the vaccine
        id = population.people[index].household
        if(id > 0):
            # get all the ids of people in the household
            for i in population.houseDict[id].ids :
                if random.uniform(0,1) < chanceToRefuse:
                    # if they already refuse a vaccine nothing changes, if not they now refuse one
                    if(not population.people[i].dontVaccme):
                        # find out if we can still let people of this age refuse
                        list = [x for x in indices if x < age]
                        try:
                            if refusers[len(list) - 1] > 0:
                                population.people[i].dontVaccme = True
                                refusers[len(list) - 1] -= 1
                                total -=1
                        except:
                            pass
    return population


def reconstruct_vaccination(files, data, population):
    "This function will reconstruct the vaccination of people in the past 6 months"
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
    while (week < time):
        weeklyData = previouslyVaccinated[week]
        week += 1

        # now we vaccinate in proportion to the data
        for i in range(1,len(previouslyVaccinated.index)) :
            index, currentRange = getIndex(indices,i)
            # number of people we are going to vaccinate
            next = weeklyData[i] - alreadyVaccinated[i]
            number = int(next*(currentRange/N*1000))
            if number > 0:
                for j in range(number) :
                    # we keep trying to pick a new index until we found someone who
                    # has not been vaccinated yet and vaccinate that person
                    while(population.people[index].vaccinated != 0) :
                        index, x = getIndex(indices,i)
                    population.people[index].vaccinated = 1
                    gevaccineerd += 1
                    population.people[index].weekOfVaccination = week
        alreadyVaccinated = previouslyVaccinated[week-1]

    return population


def getIndex(indices, i):
    """This function takes a list of indices indicating the start of
    an age group, a start age and returns an index of someone within the range
    of people with a certain age."""
    if i == 1:
        begin = 0
    else:
        begin = indices[i - 1]
    if i == 16:
        end = N
    else:
        end = indices[i]
    index = random.choice(range(begin, end))
    return index, end-begin


def initialiseInfections(data, population, tracker):
    """This function reconstructs a week of infections. This is part
    of the preprocessing."""

    infections = [10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, ]

    for week in range(7):
        infected = 0
        status_changes = tracker.empty_changes()
        while (infections[week] > 0):
            index = random.choice(range(3000, N - 1))
            while (population.people[index].susceptible == 0):
                index = random.choice(range(3000, N - 1))
            population.people[index].daysSinceInfection = 1
            infections[week] -= 1
            infected += 1

        population, changes = update(data['IFR'], population, status_changes)

        # update the tracker
        tracker.update_statistics(changes)
    return population


def VaccinationEffectiveness():
    list = []
    weeks = int(time / 7) + 50
    for t in range(weeks):
        list.append(begin*(growFactor**t))
    print(list)
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
    return infectedPopulation, tracker, vaccEffectivenessList