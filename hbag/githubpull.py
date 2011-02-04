'''Pull from GitHub upon a Web Hook callback.'''
# tornado
import tornado.web
# stdlib
import os.path
import subprocess
import logging
import re
import json

class GitHubPullHandler(tornado.web.RequestHandler):
    def initialize(self, **options):
        self.options = options

    def post(self):
        # translate the json payload sent by github
        payload = json.loads(self.get_argument('payload'))
        # get the repository info
        repo = payload['repository']
        # construct the read-only url
        url = repo['url'].replace('https', 'git')+'.git'
        # get the name of the project
        name = repo['name']
        
        path = self.options['projects_path']
        git = self.options['git_cmd']
        if not os.path.exists(os.path.join(path, repo['name'])):
            # we only clone if it is one of ours
            m = re.search(self.options['required_url_regex'], url)
            if not m or m.start() != 0:
                logging.warning('git clone rejected: %s', url)
                return
            
            r = subprocess.call([git, 'clone', url], cwd=path)
            if r:
                logging.warning('git clone failed: %s')
            else:
                logging.info('git clone complete: %s', url)
        else:
            d = os.path.join(path, name)
            m = re.search(self.options['required_url_regex'], url)
            if not m or m.start() != 0:
                # we'll pull even if it isn't ours if we've already cloned
                info = subprocess.Popen([git, 'remote', '-v'], 
                                        stdout=subprocess.PIPE,
                                        cwd=d).communicate()[0]
                if url not in info:
                    logging.warning('git pull rejected: %s', url)
                    return
            segs = payload['ref'].split('/')
            branch = segs[-1]
            r = subprocess.call([git, 'pull', 'origin', branch], cwd=d)
            if r:
                logging.warning('git pull failed: %s', url)
            else:
                logging.info('git pull complete: %s', url)

def get_handler_map(app, webroot, options):
    return [(webroot+'githubpull.*', GitHubPullHandler, options)]

def get_default_options(app):
    return {
        'git_cmd' : '/usr/bin/git', 
        'projects_path' : os.path.join(app.dataPath, 'githubpull'),
        'required_url_regex' : 'git://github.com/parente/'
    }
