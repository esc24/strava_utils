#!/usr/bin/env python

import getpass
import requests

def login(email, password):
    # Authentication
    r = requests.post('https://www.strava.com/api/v2/authentication/login', 
                      data={'email': email, 'password': password})
    if not r.ok:
        raise ValueError('Authentication failed: status code = {}'.format(r.status_code))

    return r.json['token'], r.json['athlete']['id']

def athlete_data(token):
    # Get athlete info
    r = requests.get('https://www.strava.com/api/v2/athletes/{}'.format(athlete_id), 
             params={'token':token})
    if not r.ok:
        raise ValueError('Operation failed: status code = {}'.format(r.status_code))

    return r.json

def ride_data(ride_id):
    # Get ride info
    r = requests.get('https://www.strava.com/api/v2/rides/{}'.format(ride_id))
    if not r.ok:
        raise ValueError('Operation failed: status code = {}'.format(r.status_code))

    return r.json['ride']

if __name__ == '__main__':
    print('Enter strava login...')
    email = raw_input('Email: ')
    password = getpass.getpass()
    try:
        token, athlete_id = login(email, password)
    except RuntimeError:
        print('Login failed. Exiting...')
    print('Login successful.')
    
    print ''
    ride_id = raw_input('Enter ride id: ')
    ride = ride_data(ride_id)
    for key, val in ride.iteritems():
        print str(key) + ':', val

