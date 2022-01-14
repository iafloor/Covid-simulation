from Network import *
from Read_data import *
from Classes import *
from Parameters import *
from customTypes cimport person, changes

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
    currentPopulation = create_people(currentPopulation, N, data)

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

