from Network import *
from Read_data import *
from Classes import *
from Parameters import *


def initialise_infection(people, tracker_changes):
    """ This function creates an array of n vertices (persons)
    and randomly initialises a fraction P0 of the persons
    as infected, denoted by status[i]=INFECTIOUS.
    Otherwise, status[i]=SUSCEPTIBLE.
    """

    # infect a fraction P0 of the population
    # todo dit kan sneller door willekeurig N*P0 elements uit range(0,N) te kiezen zonder terugleggen
    for person in people:
        if rd.random() < P0:
            person.infectious = 1
            tracker_changes["currently infected"] += 1
            tracker_changes["total infected"] += 1
        else:
            tracker_changes["susceptible"] += 1

    return tracker_changes


def vaccination_order_function(population, age_groups, type, start_age):
    # This is a function that creates a list of people to vaccinate to follow in the model
    if type == 1:  # Old to yound
        order = population.people[age_groups.iloc[start_age]:]
        order.reverse()
    if type == 2:  # Young to old
        order = population.people[age_groups.iloc[start_age]:]
    if type == 3:  # Danish way
        tail = population.people[age_groups.iloc[start_age]:age_groups.iloc[50]]
        start = population.people[age_groups.iloc[50]:]
        start.reverse()
        order = start + tail
    else :  # custom
        one = population.people[age_groups.iloc[40]:age_groups.iloc[60]]
        two = population.people[age_groups.iloc[60]:]
        two.reverse()
        three = population.people[age_groups.iloc[start_age]:age_groups.iloc[40]]
        order = one + two + three

    population.vaccOrder = order
    return population


def initialise_model(files, order_type, tracker_changes):
    # This initializes everything for the model to run

    # Read age distribution and add to dataframe
    print("Reading age distribution from: " + files['Population_dataset'])
    data = read_age_distribution(files["Population_dataset"])

    # Add fatality rate to dataframe
    print("Reading infection fatality rates from: " + files["Fatality_distribution_dataset"])
    data["IFR"] = read_fatality_distribution(files["Fatality_distribution_dataset"], len(data.index))

    # Add corresponding age groups to dataframe
    # These age groups are all ages in the range(start_group[i],start_group[i+1])
    print("Creating age group class objects.")
    data["Age group class object"] = make_age_groups(data, STARTGROUP, len(data.index))

    # Determine how many people of each age there are
    print("Determining age distribution for population of " + str(N) + "people.")
    data["Start of age group"] = determine_age_distribution(data)

    # Read the file containing data about contacts longer then 15 minutes
    print("Creating age group contact distribution.")
    contact_data = read_contact_data(data, files["Polymod_participants_dataset"], files["Polymod_contacts_dataset"], PERIOD)

    # create population
    print("Creating a population")
    currentPopulation = population()

    # adding people to the population
    print("Creating people.")
    currentPopulation = create_people(currentPopulation, N, data, Vacc_readiness)

    # create households
    print("Creating households")
    currentPopulation = make_households(currentPopulation, files["Household_makeup_dataset"],
                                     files["People_in_household_dataset"], files["Child_distribution_dataset"])

    # determine vaccination order
    print("Determining vaccination order")
    currentPopulation = vaccination_order_function(currentPopulation, data["Start of age group"], order_type, STARTAGE)

    # Create contact network
    print("Generating network.")
    contact_matrix = create_network(data, currentPopulation.people, contact_data)
    
    # Initialize infection
    #tracker_changes = initialise_infection(currentPopulation.people, tracker_changes)

    return data, contact_matrix, tracker_changes, currentPopulation

# infecting people

def infectChance(time, population, person) :
    """ This function calculates the chance that someone will get infect based
    on the infections in their innercircle. This chance is base on:
    - how many people in their household are infected
    - how many people in their classroom are infected
    and an overall difference if someone has been vaccinated or not
    and how long ago"""
    chance = 0

    # if cohab or classmate is sick, chance increases
    chance += cohabIsSick(population, person)
    chance += classmateIsSick(population, person)

    # if persen is vaccinated chance lowers but protection decreases over time
    if chance > 0:
        if person.vaccinated :
            chance *= prevVaccinated(time, person)
        else :
            chance = 10

    return chance


def cohabIsSick(population, person):
    # checks if there is someone sick in your household
    household = person.household
    if (population.houseDict[household].infected > 0) :
        chance = 20
    else :
        chance = 0
    return chance


def classmateIsSick(population, person):
    # checks if there is someone sick in your class
    id = person.schoolClass
    chance = 0
    if(id > -1) :   # a person has id -1 if they're not in a class
        if(population.schoolGroup[id].infected > 0):
            chance = 20
    return chance


def prevVaccinated(time, person):
    # this function calculates how long ago someone has been vaccinated
    # according to research the protection of a vaccine decreases over time
    vaccInWeek = person.weekOfVaccination
    timeSinceVacc = int(time/7) - vaccInWeek
    return 20 + 5*timeSinceVacc


def infect_standard(network, population):
    """This function performs one time step (day) of the infections
    a is the n by n adjacency matrix of the network
    status represents the health status of the persons.
    In this step, infectious persons infect their susceptible contacts
    with a certain probability.
    """

    people = population.people
    n = len(people)
    x = np.zeros((n + 1), dtype=int)
    y = np.zeros((n + 1), dtype=int)

    # determine list of infectious persons from status
    for person in people:
        if person.infectious == 1:
            x[person.person_id] = 1

    # propagate the infections
    for edge in network:
        i, j = edge
        y[i] += x[j]

    for person in people:
        # incorporate the daily probability of meeting a contact
        # taking into account the possibility of being infected twice

        if y[person.person_id] > 0:
            r = rd.random()
            if y[person.person_id] == 1:
                p = P_MEETING # probability of a meeting with 1 infected contact
            else:
                p = 1 - (1 - P_MEETING) ** y[person.person_id]  # probability with more than 1
            if r < p:
                if person.susceptible == 1:
                    person.daysSinceInfection = 1
        id = person.person_id
        population.people[id] = person

    return population

# update the data

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
                population.people[id].recovered = 1
                new_status_changes["recovered"] += 1
                new_status_changes["currently infected"] += -1

        # update the population
        # id = person.person_id
        # population.people[id] = person

    return population, new_status_changes

# functions to vaccinate people

def boosters(population, number, startage, week):
    """In this function we give a number of people a boostervaccine. The vaccines
    are distrubted from oldest to youngest and you can only get a boostervaccine
    if you have already been vaccinated before. We update the week of vaccination
    to the current week and use a parameter startage which keeps track of where
    we left vaccinating the previous day."""

    for i in range(number):
        # if the person has not been vaccinated, we skip them
        while population.people[startage].weekOfVaccination < 0 :
            startage -= 1
        population.people[startage].weekOfVaccination = week


def vaccinateKids(population, number, week):
    """In this function we vaccinate children under 12. We chose a
    random index and check if this kid has already been vaccinated,
    if so we chose another one."""

    for i in range(number):
        index = 1
        while(population.people[index].vaccinated != 0):
            index = 1
        population.people[index].vaccinated = 1
        population.people[index].weekOfVaccination = week


def vaccinate(population, status_changes):
    """This function performs one time step (day) of the vaccinations.
    status represents the health status of the persons.
    Only the susceptible or recovered (after a number of days) are vaccinated
    """

    new_status_changes = status_changes
    n = len(population.people)

    # today's number of vaccines
    vacc = math.floor((1 - BETA) * VACC * n)  # and for the old
    for i in range(min(vacc, len(population.vaccOrder))):
        person = population.vaccOrder.pop(0)
        if person.status == SUSCEPTIBLE:
            if person.vaccination_readiness == True:
                person.update_status(VACCINATED)
                new_status_changes["susceptible"] += -1
                new_status_changes["vaccinated"] += 1

        if person.status == RECOVERED and person.daysSinceInfection >= DAY_RECOVERY + NDAYS_VACC:
            person.update_status(VACCINATED)
            new_status_changes["vaccinated"] += 1

    return new_status_changes, population

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


def run_model(population, data, contact_matrix, tracker, timesteps, start_vaccination=0):
    """ This function simulates infections for a given number of days given by the input timesteps.
    The input for this function is the population containing information about all the people and
    their households, the contact matrix containing occasional meetings between people. A tracker
    that keeps track of the statistical changes and the number of timesteps."""
    for time in range(timesteps):
        sys.stdout.write('\r' + "Time step: " + str(time)) # printing the day we are currently simulating
        sys.stdout.flush()
        status_changes = tracker.empty_changes()
        # loop through all the people in the population, if they are not sick we calculate their change
        # of getting infected. If they get infected it is their first day since infection.
        for person in population.people:
            if person.susceptible == 1 :
                number = random.choice(range(100))
                if number < infectChance(time, population, person) :
                    id = person.person_id
                    population.people[id].daysSinceInfection = 1

        # we infect a number of people based on occasional meetings
        population = infect_standard(contact_matrix, population)

        # update the people in the population
        population, changes = update(data['IFR'], population, status_changes)

        # update the tracker
        tracker.update_statistics(changes)

    return tracker


def model(filenames, type, timesteps):
    # this initializes and runs the entire model for a certain number of timesteps.
    # It returns a pandas dataframe containing all data at time t
    tracker = track_statistics()

    tracker_changes = tracker.init_empty_changes()
    data, contact_matrix, tracker_changes, currentPopulation = initialise_model(filenames, type, tracker_changes)
    # update the dataframe
    tracker.update_statistics(tracker_changes)

    # preprocessing
    newPopulation, tracker = preprocessing(currentPopulation, filenames, data, tracker)

    # Run the model
    tracker = run_model(newPopulation, data, contact_matrix, tracker, timesteps - 1, 0)

    return tracker

