from initialize import *
from infecting import *
from vaccination import *
from preprocessing import *

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

    return population, new_status_changes

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

def create_model(filenames, type, timesteps):
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

