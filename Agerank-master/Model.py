from initialize import *
from infecting import *
from preprocessing import *
from vaccination import *

# update the data

def run_model(population, data, contact_matrix, tracker, timesteps, start_vaccination, vaccEffectiveness):
    """ This function simulates infections for a given number of days given by the input timesteps.
    The input for this function is the population containing information about all the people and
    their households, the contact matrix containing occasional meetings between people. A tracker
    that keeps track of the statistical changes and the number of timesteps."""
    thuis = 0
    startage = int(N-1) # index of oldest person in the list
    for time in range(timesteps):
        sys.stdout.write('\r' + "Time step: " + str(time)) # printing the day we are currently simulating
        sys.stdout.flush()
        status_changes = tracker.empty_changes()
        # loop through all the people in the population, if they are not sick we calculate their change
        # of getting infected. If they get infected it is their first day since infection.
        for person in population.people:
            if person.susceptible == 1 :
                number = random.choice(range(100))
                infectC = infectChance(population, person)
                if number < infectC:
                    number = random.uniform(0,1)
                    if number < prevVaccinated(time, person, vaccEffectiveness):
                        id = person.person_id
                        population.people[id].daysSinceInfection = 1
                        thuis += 1

        # we infect a number of people based on occasional meetings
        population = infect_standard(contact_matrix, population)

        # update the people in the population
        population, changes = update(data['IFR'], population, status_changes)

        # booster people
        population, startage = boosters(population, startage, int(time/7))

        # update the tracker
        tracker.update_statistics(changes)

    return tracker, thuis

def create_model(filenames, type, timesteps):
    # this initializes and runs the entire model for a certain number of timesteps.
    # It returns a pandas dataframe containing all data at time t
    tracker = track_statistics()

    tracker_changes = tracker.init_empty_changes()
    data, contact_matrix, tracker_changes, currentPopulation = initialise_model(filenames, type, tracker_changes)
    # update the dataframe
    tracker.update_statistics(tracker_changes)

    # preprocessing
    newPopulation, tracker, vaccEffectiveness = preprocessing(currentPopulation, filenames, data, tracker)

    # Run the model
    tracker, thuis = run_model(newPopulation, data, contact_matrix, tracker, timesteps - 1, 0, vaccEffectiveness)
    print(thuis)
    return tracker

