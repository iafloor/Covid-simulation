from Network import *
from Read_data import *
from Classes import *
from Parameters import *


def initialise_infection(parameters, people, tracker_changes):
    """ This function creates an array of n vertices (persons)
    and randomly initialises a fraction P0 of the persons
    as infected, denoted by status[i]=INFECTIOUS.
    Otherwise, status[i]=SUSCEPTIBLE.
    """

    # infect a fraction P0 of the population
    # todo dit kan sneller door willekeurig N*P0 elements uit range(0,N) te kiezen zonder terugleggen
    for person in people:
        if rd.random() < parameters["P0"]:
            person.infectious = 1
            tracker_changes["currently infected"] += 1
            tracker_changes["total infected"] += 1
        else:
            tracker_changes["susceptible"] += 1

    return tracker_changes


def reconstruct_vaccination(parameters, order, tracker_changes, files, dataframe, population):
    "This function will reconstruct the vaccination of people in the past 6 months"
    new_status_changes = tracker_changes
    previouslyVaccinated = readVacciation(files["previouslyVaccinated"])
    ages = dataframe["Start of age group"].tolist()

    # percentage of people of an age group that is already vaccinated
    alreadyVaccinated = [0 for i in range(len(previouslyVaccinated.index))]

    # list with all indices of the startages
    indices = []
    indices.append(ages[12])
    for i in range(1,16) :
        age = 2022 - int(previouslyVaccinated["age"][i][0:4])
        indices.append(ages[age])

    # we loop through all the weeks we have data off
    time = len(previouslyVaccinated.columns)
    week = 1
    gevaccineerd = 0
    listOfNubers = []
    while (week < time):
        weeklyData = previouslyVaccinated[week]
        week += 1

        # now we vaccinate a percentage of alll
        for i in range(1,len(previouslyVaccinated.index)) :
            index, currentRange = getIndex(indices,i)
            # number of people we are going to vaccinate
            next = weeklyData[i] - alreadyVaccinated[i]
            number = int(next*(currentRange/N*1000))
            if number > 0:
                for j in range(number) :
                    while(population.people[index].vaccinated != 0) :
                        index, x = getIndex(indices,i)
                    population.people[index].vaccinated = 1
                    gevaccineerd += 1
                    population.people[index].weekOfVaccination = week
                    person = population.people[index]
        alreadyVaccinated = previouslyVaccinated[week-1]
        listOfNubers.append(gevaccineerd/N*100)

    p = population.people[67382]
    return new_status_changes, order


def getIndex(indices, i):
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


def initialise_model(parameters, files, order_type, tracker_changes):
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
    data["Age group class object"] = make_age_groups(data, parameters["STARTGROUP"], len(data.index))

    # Determine how many people of each age there are
    print("Determining age distribution for population of " + str(parameters["N"]) + "people.")
    data["Start of age group"] = determine_age_distribution(parameters, data)

    # Read the file containing data about contacts longer then 15 minutes
    print("Creating age group contact distribution.")
    contact_data = read_contact_data(data, files["Polymod_participants_dataset"], files["Polymod_contacts_dataset"], parameters["PERIOD"])

    # create population
    print("Creating a population")
    currentPopulation = population()

    # adding people to the population
    print("Creating people.")
    currentPopulation = create_people(currentPopulation, parameters["N"], data, parameters["Vacc_readiness"])

    # create households
    print("Creating households")
    currentPopulation = make_households(currentPopulation, files["Household_makeup_dataset"],
                                     files["People_in_household_dataset"], files["Child_distribution_dataset"])

    # determine vaccination order
    print("Determining vaccination order")
    currentPopulation = vaccination_order_function(currentPopulation, data["Start of age group"], order_type, parameters["STARTAGE"])

    # Create contact network
    print("Generating network.")
    contact_matrix = create_network(data, currentPopulation.people, contact_data)
    
    # Initialize infection
    tracker_changes = initialise_infection(parameters, currentPopulation.people, tracker_changes)

    # Initialize vaccination
    tracker_changes, currentPopulation.vaccOrder = reconstruct_vaccination(parameters, currentPopulation.vaccOrder, tracker_changes, files, data, currentPopulation)

    return data, contact_matrix, tracker_changes, currentPopulation


def infectChance(time, population, person) :
    """ This function calculates the chance that someone will get infect.
     This is based on a couple factors:
    CHEKC if there is someone infected in their household or schoolclass
     - their age --> beta variant doesn't matter about age
     CHECK if they are vaccinated (and how long ago)
     - if they have been infected before
     - the random chance to get COVID by the polymod"""
    chance = 0

    # if cohab or classmate is sick, chance increases
    chance += cohabIsSick(population, person)
    chance += classmateIsSick(population, person)

    # if person has not been vaccinated chance increases
    # if persen is vaccinated, protection decreases over time
    if person.vaccinated :
        chance += prevVaccinated(time, person)
    else :
        chance += 10

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
    vaccInWeek = person.weekOfVaccination
    timeSinceVacc = int(time/7) - vaccInWeek
    return 20 + 5*timeSinceVacc


def infect_cohabitants(parameters,population, tracker_changes):
    # Method of infection for people in the same house.

    infected = []

    for j in population.people:
        if j.household != 0:
            if j.status == parameters["INFECTIOUS"] or j.status == parameters["SYMPTOMATIC"]:
                infected.append(j)
            elif j.status == parameters["TRANSMITTER"] and rd.random() < parameters["P_TRANSMIT0"]:
                infected.append(j)

    for j in infected:
        members = population.houseDict[j.household].members
        cohabitants = [members[i] for i in range(len(members)) if members[i] != j]
        for cohab in cohabitants:
            if rd.random() < parameters["P_COHAB"]:
                if j.status == parameters["SUSCEPTIBLE"]:
                    j.update_status(parameters["INFECTIOUS"])
                    tracker_changes["currently infected"] += 1
                    tracker_changes["total infected"] += 1
                    tracker_changes["susceptible"] -= 1
                elif j.status == parameters["VACCINATED"]:
                    if rd.random() < parameters["P_TRANSMIT1"]:
                        j.update_status(parameters["TRANSMITTER"])
                        tracker_changes['currently infected'] += 1
                        tracker_changes['total infected'] += 1
                        tracker_changes["transmitter"] += 1

    return tracker_changes


def infect_perturbation(parameters, p, tracker_changes):
    # this infects a fraction of the poplulation proportional to the the amount of infections
    people = population.people
    n = len(people)
    x = np.zeros((n + 1), dtype=int)

    for person in people:
        if person.status == parameters["INFECTIOUS"] or person.status == parameters["SYMPTOMATIC"]:
            x[person.person_id] = 1
        elif person.status == parameters["TRANSMITTER"] and rd.random() < parameters["P_TRANSMIT0"]:
            x[person.person_id] = 1

    total_infected = sum(x)
    prob = 1 - (1 - parameters["P_ENCOUNTER"] * (total_infected / (parameters["N"] - 1))) ** (parameters["ENCOUNTERS"])
    to_infect = [i for i in range(n) if rd.random() < prob]

    for id in to_infect:
        person = people[id]
        if person.status == parameters["SUSCEPTIBLE"]:
            person.update_status(parameters["INFECTIOUS"])
            tracker_changes["currently infected"] += 1
            tracker_changes["total infected"] += 1
            tracker_changes["susceptible"] -= 1
        elif person.status == parameters["VACCINATED"]:
            person.update_status(parameters["TRANSMITTER"])
            tracker_changes['currently infected'] += 1
            tracker_changes['total infected'] += 1
            tracker_changes["transmitter"] += 1

    return tracker_changes


def infect_standard(parameters, network, population):
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
        #elif person.status == parameters["TRANSMITTER"] and rd.random() < parameters["P_TRANSMIT0"]:
        #    x[person.person_id] = 1

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
                p = parameters["P_MEETING"]  # probability of a meeting with 1 infected contact
            else:
                p = 1 - (1 - parameters["P_MEETING"]) ** y[person.person_id]  # probability with more than 1
            if r < p:
                if person.status == parameters["SUSCEPTIBLE"]:
                    person.daysSinceInfection = 1
        id = person.person_id
        population.people[id] = person

    return population


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


def run_model(population, parameters, data, contact_matrix, tracker, timesteps, start_vaccination=0):
    # Function for running the model. It wraps the vaccinate, infection and update functions
    for time in range(timesteps):
        sys.stdout.write('\r' + "Tijdstap: " + str(time))
        sys.stdout.flush()
        status_changes = tracker.empty_changes()
        for person in population.people:
            if person.susceptible == 1 :
                number = random.choice(range(100))
                if number < infectChance(time, population, person) :
                    id = person.person_id
                    population.people[id].daysSinceInfection = 1
        population = infect_standard(parameters, contact_matrix, population)

        # update the population
        population, changes = update(data['IFR'], population, status_changes)
        tracker.update_statistics(changes)

    return tracker


def model(parameters, filenames, type, timesteps):
    # this initializes and runs the entire model for a certain number of timesteps.
    # It returns a pandas dataframe containing all data at time t
    tracker = track_statistics()

    tracker_changes = tracker.init_empty_changes()
    data, contact_matrix, tracker_changes, currentPopulation = initialise_model(parameters, filenames, type, tracker_changes)
    # update the dataframe
    tracker.update_statistics(tracker_changes)

    # Run the model
    tracker = run_model(currentPopulation, parameters, data, contact_matrix, tracker, timesteps - 1, 0)

    return tracker

