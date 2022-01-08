from Network import *
from Read_data import *
from Classes import *
from Parameters import *
from Model import update
# preprocessing functions
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
    #listOfNubers = []
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
        #listOfNubers.append(gevaccineerd/N*100)

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
        end = 100000
    else:
        end = indices[i]
    index = random.choice(range(begin, end))
    return index, end-begin


def initialiseInfections(data, population, tracker):
    """This function reconstructs 2 weeks of infections. This is part
    of the preprocessing."""

    infections = [10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, 10, 15, 20, 15, ]

    for week in range(len(infections)):
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


def preprocessing(population, files, data, tracker):
    """In this function we do the preprocessing that has to be done before we
    can start simulating. This consists of letting a percentage of the people
    refuse a vaccine, giving a percentage of the population a vaccine and
    reconstructing the infections that happened 14 timesteps prior to starting the
    simulation. """

    newpopulation = refuseVaccination(population, data)
    vaccinatedPopulation = reconstruct_vaccination(files, data, newpopulation)
    infectedPopulation = initialiseInfections(data, vaccinatedPopulation, tracker)
    return infectedPopulation, tracker