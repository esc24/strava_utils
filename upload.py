#!/usr/bin/env python

# Copyright 2012, Ed Campbell
# All rights reserved.

# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:

# Redistributions of source code must retain the above copyright notice, this 
# list of conditions and the following disclaimer.

# Redistributions in binary form must reproduce the above copyright notice, 
# this list of conditions and the following disclaimer in the documentation 
# and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# TODO - units on output, order gpx by creation date, .strava file

import getpass
import glob
import hashlib
import os
import random

import gnomekeyring
import readline
import requests

def get_credentials():

    try:
        keyrings = gnomekeyring.find_items_sync(gnomekeyring.ITEM_GENERIC_SECRET, 
                                                {'signon_realm': 'https://www.strava.com/'})
    except gnomekeyring.NoMatchError:
        # no stored cred
        email = None
        password = None
    else:
        if len(keyrings) == 1:
            email = keyrings[0].attributes['username_value']
            password = keyrings[0].secret
            resp = raw_input('Are you {}? (Y/n): '.format(email))
            if resp != '' and resp.lower() != 'y':
                email = None
                password = None
        else:
            print('Multiple logins found...')
            for i, keyring in enumerate(keyrings, 1):
                print('{}) {}'.format(i, keyring.attributes['username_value']))
            id_num = int(raw_input('Enter number of account' \
                                      '(0 to enter alternative): '))
            if id_num > 0 and id_num <= len(keyrings):
                email = keyrings[id_num - 1].attributes['username_value']
                password = keyrings[id_num -1].secret
            elif id_num != 0:
                print('Invalid response.')

    # Fallback is to ask
    if email is None: 
        print('Enter strava login...')
        email = raw_input('Email: ')
        password = getpass.getpass()

    return email, password

def encrypy_password(raw_password):
    salt = hashlib.sha384(str(random.random())).hexdigest()
    hsh = hashlib.sha512('{}{}'.format(salt, raw_password)).hexdigest()
    enc_password = '{}${}'.format(salt, hsh)
    return enc_password

def check_password(raw_password, enc_password):
    salt, hsh = enc_password.split('$')
    return hsh == hashlib.sha512('{}{}'.format(salt, raw_password)).hexdigest()

def login(email, password):
    # Authentication
    r = requests.post('https://www.strava.com/api/v2/authentication/login', 
                      data={'email': email, 'password': password})
    if not r.ok:
        raise ValueError('Authentication failed ({}): {}'.format(r.status_code, r.text))

    return r.json['token'], r.json['athlete']['id']

def get_athlete_data(token):
    # Get athlete info
    r = requests.get('https://www.strava.com/api/v2/athletes/{}'.format(athlete_id), 
             params={'token':token})
    if not r.ok:
        raise ValueError('Operation failed ({}): {}'.format(r.status_code, r.text))

    return r.json

def get_ride_data(ride_id):
    # Get ride info
    r = requests.get('https://www.strava.com/api/v2/rides/{}'.format(ride_id))
    if not r.ok:
        raise ValueError('Operation failed ({}): {}'.format(r.status_code, r.text))

    return r.json['ride']

def upload_gpx(token, filename, activity='ride'):
    if activity not in ['ride', 'run']:
        raise ValueError("Unknown activity type '{}'".format(activity))

    with open(filename, 'rt') as gpx_file:
        gpx_data = gpx_file.read()

    r = requests.post('http://www.strava.com/api/v2/upload', data={'token': token, 
                                                                   'data': gpx_data, 
                                                                   'type': 'gpx', 
                                                                   'activity': activity})
    if not r.ok:
        raise ValueError('Operation failed ({}): {}'.format(r.status_code, r.text))

    return r.json['id'], r.json['upload_id']

if __name__ == '__main__':
    # Log in
    email, password = get_credentials()
    try:
        token, athlete_id = login(email, password)
    except RuntimeError:
        print('Login failed. Exiting...')
    print('Login successful.\n')
    
    # Upload
    garmin_path = '/media/GARMIN/Garmin/GPX'
    if os.path.isdir(garmin_path):
        track_num = 0
        print('Looking for tracks...')
        filenames = glob.glob(os.path.join(garmin_path,'Track_*.gpx'))
        # Sort by modification time
        filenames.sort(key=lambda f: os.path.getmtime(f))
        if filenames:
            for i, filename in enumerate(filenames ,1):
                print('{}) {}'.format(i, os.path.basename(filename).replace('Track_', '')))
            track_num = int(raw_input('Enter number to upload ' \
                                      '(0 to skip upload): '))
            if track_num == 0:
                print('Skipping upload.') 
            elif track_num > 0 and track_num <= len(filenames):
                upload_gpx(token, filenames[track_num - 1])
                print("Upload successful. Visit http://app.strava.com/athlete/training to edit.")
            else:
                print('Invalid response. Skipping upload.')
        else:
            print('No tracks found.\n')

    # Query rides
    exit_flag = False
    while exit_flag is False:
        ride_id = raw_input('Enter ride id to query (0 to exit): ')
        if int(ride_id) == 0:
            exit_flag = True
            print('Exiting...')
        else:
            try:
                ride = get_ride_data(ride_id)
            except ValueError as e:
                print(e.message)
            else:
                for key, val in ride.iteritems():
                    print('{!s}: {}'.format(key, val))

