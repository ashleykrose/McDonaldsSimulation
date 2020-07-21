"""
Project 1 Scenario 2
Ashley Roselius
Mateen Rizki
CS 6830
"""
import random
import simpy

random_seed = 132141
run_time = 7200.0  # Total time of simulation (2 hours)
number_order_stations = 2  # Number of order stations (2)
number_pickup_window = 1  # Number of pickup windows (1)
maximum_pickup_line = 6  # Max number in pickup line (6)
maximum_individual_order_line = 5  # Max number in each order line (5)
maximum_order_line = 10  # Max number in total order line (10)
mean_order_time = 90.0  # Mean time of 1.5 minutes for customer to order
mean_food_prep_time = 300.0  # Mean time of 5 minutes for food prep
mean_pickup_time = 60.0  # Mean time of 1 minutes for payment
mean_payment_time = 120.0  # Mean time of 2 minutes for payment
mean_interarrival_time = 120.0  # Mean time of 1 minutes between customer arrivals
number_of_customers = 0  # Number of people who come to the restaurant
order_station_number = 0  # Which line the customer got in
number_left = 0  # Number of people who left
number_fed = 0  # Number of people who got food


def customer_generator(env, run_time, order_station_1, order_station_1_waiting, order_station_2, order_station_2_waiting, pickup_window, number_of_customers, order_station_number):
    """Source generates customers randomly for set time"""
    number_of_customers += 1
    c = customer(env, 'Customer%02d' % number_of_customers, order_station_1, order_station_1_waiting, order_station_2, order_station_2_waiting, pickup_window, order_station_number)
    env.process(c)
    interarrival_time = random.expovariate(1.0 / mean_interarrival_time)
    yield env.timeout(interarrival_time)
    # schedule the customer arrival
    env.process(customer_generator(env, run_time, order_station_1, order_station_1_waiting, order_station_2, order_station_2_waiting, pickup_window, number_of_customers, order_station_number))


def customer(env, name, order_station_1, order_station_1_waiting, order_station_2, order_station_2_waiting, pickup_window, order_station_number):
    """Customer arrives, is served and leaves."""
    print('%s: Here I am' % name)
    order_station_1_count = order_station_1.count
    order_station_2_count = order_station_2.count
    order_line_1_count = len(order_station_1.queue) + order_station_1_waiting.count + len(order_station_1_waiting.queue)
    order_line_2_count = len(order_station_2.queue) + order_station_2_waiting.count + len(order_station_1_waiting.queue)
    order_line_count = order_line_1_count + order_line_2_count
    # request an order station
    if order_line_count < maximum_order_line:
        if (order_line_1_count + order_station_1_count) <= (order_line_2_count + order_station_2_count):
            req_order_station = order_station_1.request()
            order_station_number = 1
        else:
            req_order_station = order_station_2.request()
            order_station_number = 2
        yield req_order_station
        # We got an order station
        order_time = random.expovariate(1.0 / mean_order_time)
        yield env.timeout(order_time)
        # wait for food to prep
        prep_time_start = env.now
        food_prep_time = random.expovariate(1.0 / mean_food_prep_time)
        # Pay at order station
        payment_time = random.expovariate(1.0 / mean_payment_time)
        yield env.timeout(payment_time)
        # send to the waiting queue so next person can order
        if order_station_number == 1:
            req_order_station_waiting = order_station_1_waiting.request()
        elif order_station_number == 2:
            req_order_station_waiting = order_station_2_waiting.request()
        else:
            print('ERROR: somehow order station didnt get set correctly')
        # release the order station
        if order_station_number == 1:
            order_station_1.release(req_order_station)
        elif order_station_number == 2:
            order_station_2.release(req_order_station)
        else:
            print('ERROR: somehow order station didnt get set correctly')
        yield req_order_station_waiting
        # wait for pickup queue to be less than 6
        while len(pickup_window.queue) >= maximum_pickup_line:
            yield env.timeout(10.0)
        # request the pickup window
        req_pickup_window = pickup_window.request()
        # release the waiting queue
        if order_station_number == 1:
            order_station_1_waiting.release(req_order_station_waiting)
        elif order_station_number == 2:
            order_station_2_waiting.release(req_order_station_waiting)
        else:
            print('ERROR: somehow order station didnt get set correctly')
        yield req_pickup_window
        # We got the pickup window
        left_food_prep_time = food_prep_time - (env.now - prep_time_start)
        pickup_time = random.expovariate(1.0 / mean_pickup_time)
        if left_food_prep_time > 0:
            wait_time = left_food_prep_time + pickup_time
            yield env.timeout(wait_time)
        else:
            yield env.timeout(pickup_time)
        # release the pickup window
        pickup_window.release(req_pickup_window)
        print('%s: Finished and got food' % name)
        global number_fed
        number_fed += 1
    else:
        print('%s: Did not get in line' % name)
        global number_left
        number_left += 1


# Setup and start the simulation
print('Project 1')
random.seed(random_seed)
env = simpy.Environment()

# Start processes and run
order_station_1 = simpy.Resource(env, capacity=(number_order_stations/2))
order_station_1_waiting = simpy.Resource(env, capacity=(number_order_stations/2))
order_station_2 = simpy.Resource(env, capacity=(number_order_stations/2))
order_station_2_waiting = simpy.Resource(env, capacity=(number_order_stations/2))
pickup_window = simpy.Resource(env, capacity=number_pickup_window)
env.process(customer_generator(env, run_time, order_station_1, order_station_1_waiting, order_station_2, order_station_2_waiting, pickup_window, number_of_customers, order_station_number))
env.run(until=run_time)
print('Number of people who got food: %02d' % number_fed)
print('Number of people who left: %02d' % number_left)
