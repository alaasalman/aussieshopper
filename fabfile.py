#!/usr/bin/env python
import json
from os import path
from contextlib import contextmanager as _contextmanager

from fabric.api import (sudo, settings, require,
                        cd, env, task, local)
from fabric.colors import yellow, red, green
from fabric.context_managers import prefix
from fabric.utils import abort

# load config only once
env.config_loaded = False

# use ssh config attribs in $HOME
env.use_ssh_config = True
env.shell = "/bin/bash -l -i -c"


@_contextmanager
def _virtualenv():
    require('activate')

    with prefix(env.activate):
        yield


@task
def deploy():
    require('app_folder', 'deploy_user', 'hosts')
    deploy_user = env.deploy_user
    app_home = env.app_home

    print_with_attention("Uploading bundles")
    local(f'rsync --partial --progress --recursive web/static/ mylinode:~/{deploy_user}')

    with _virtualenv(), cd(env.app_folder), settings(sudo_user=env.deploy_user):
        print(green("Updating git repo"))
        sudo('git pull')
        
        print(green("Upgrading pip"))
        sudo('pip install pip --upgrade --no-cache-dir')

        print(green("Upgrading requirements"))
        sudo('pip install -r config/requirements.txt --upgrade --no-cache-dir')

        print(green("Running migrations"))
        sudo('./manage.py migrate')

        print(green("Collecting static files"))
        sudo('./manage.py collectstatic --noinput')

        # move bundles
        print(green("Moving bundles"))
        sudo(f'rsync -r /home/alaa/{deploy_user}/bundles {app_home}/static/')

    print_with_attention("Restarting app server and web server")
    # restart supervisor and nginx after all said and done
    sudo('supervisorctl restart aussieshopper: aussiecelery: aussiecelerybeat:')
    sudo('service nginx restart')


def loadconfig():
    """
    Load conf.json configuration file and replace environment values with ones defined in it.
    """
    if env.config_loaded:
        return

    print_with_attention("Loading configuration")

    require('config_key')  # need to know what environment we're working on

    config_file_path = 'conf.json'

    if not path.exists(config_file_path):
        print(red("Couldn\'t find config file at {0}".format(config_file_path)))
        return

    with open(config_file_path) as conf_file:
        json_config_object = json.load(conf_file)
        env_config_object = json_config_object.get(env.config_key)

        if env_config_object is None:
            abort("You need to specify what environment I am targeting first")

        print(green("Using this configuration:"))
        for k, v in env_config_object.items():
            env[k] = v
            print(green("{0} => {1}".format(k, v)))

    env.config_loaded = True


def print_with_attention(msg):
    """
    Print supplied message within ascii marks to bring the user's attention to it.
    :param msg: str to print and alert user of
    """
    print(yellow("=" * len(msg)))
    print(yellow(msg))
    print(yellow("=" * len(msg)))


@task
def mylinode():
    """Using default app name and user according to project"""
    env.config_key = 'default'

    loadconfig()

    print_with_attention("Deploying with user {0} and app {1}".format(env.deploy_user, env.app_name))

    env.app_home = '/home/%(deploy_user)s' % env
    env.app_folder_name = '%(app_name)s' % env
    env.app_folder = '%(app_home)s/src' % env

    env.activate = 'source %(app_home)s/venv/bin/activate' % env
