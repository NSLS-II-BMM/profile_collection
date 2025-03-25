
import redis, configparser, os, requests, json, random, pprint
from redis_json_dict import RedisJSONDict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

startup_dir = os.path.dirname(os.path.dirname(__file__))
profile_configuration = configparser.ConfigParser(interpolation=None)
profile_configuration.read_file(open(os.path.join(startup_dir, "BMM_configuration.ini")))
bmmbot_secret = profile_configuration.get('slack', 'bmmbot_secret')

redis_client = redis.Redis(host=profile_configuration.get('services', 'nsls2_redis'))

pass_api = profile_configuration.get('services', 'pass_api') + "/{pass_id}/slack-channels"


class BMMbot():
    '''Simple class to manage conversations via the facility-provided
    Slack BMM Bot.

    usage
    =====

    instantiate client:
      from BMM_common import bmmbot
      bmmbot = BMMbot()

    post a text message:
      bmmbot.post('This is a text message')

    post an image file:
      bmmbot.image('/path/to/image/file')

    after changing users by running NSLS2's sync_experiment():
      bmmbot.refresh_channel()

    '''
    def __init__(self):
        def slurp(fname):
            'Slurp a text file into a string.'
            with open(fname, 'r') as myfile:
                text=myfile.read()
            return text
        self._post_allowed = True
        self.refresh_channel()
        self._auth = slurp(bmmbot_secret)
        self.client = WebClient(token=self._auth)
        
    def post(self, text):
        '''Post a text message to the proposal-tla channel.

        To generate a slightly randomized message (perhaps for
        debugging purposes), put ":flag:" in the text.  That string
        will be replaced by a random country flag emoji,
        e.g. ":flag-tv:".

        '''
        if self._post_allowed is False:
            print('Cannot post message. No proposal Slack channel exists.')
            return
        try:
            self.client.chat_postMessage(text=text.replace(':flag:', self.random_flag()), channel=self.non_chat_channel)
        except SlackApiError as e:
            print('Slack message post failed for reason: ' + e.response["error"])

    def image(self, fname, title=None):
        '''Post an image (or other file) to the proposal-tla channel'''
        if self._post_allowed is False:
            print('Cannot post image file. No proposal Slack channel exists.')
            return
        try:
            self.client.files_upload_v2(file=fname, title=title, channel=self.non_chat_channel)
        except SlackApiError as e:
            print('Slack image upload failed for reason: ' + e.response["error"])
            self.post(f'failed to post image: {fname}')

    def describe(self):
        '''Debugging message printed to screen.'''
        print('Channel data from NSLS-II API:')
        pprint.pprint(self.channel_data)
        print()
        print(f'_post_allowed = {self._post_allowed}')
        print(f'pass_id = {self.pass_id}')
        print(f'api_url = {self.api_url}')
        print(f'non_chat_channel = {self.non_chat_channel}')
        print(f'random flag emoji = {self.random_flag()}')
        
    def refresh_channel(self):
        '''Refresh the ID of the proposal-bmm channel when changing users.

        Also flag that posting is not allowed if the Slack channels do not exist
        for this proposal.

        '''
        facility_dict = RedisJSONDict(redis_client=redis_client, prefix='xas-')
        data_session = facility_dict['data_session']
        self.pass_id = data_session.replace('pass-','')
        self.api_url = pass_api.format(pass_id=self.pass_id)  # see line 14
        response=requests.get(self.api_url)
        self.channel_data = json.loads(response.text)
        self.non_chat_channel = '---'
        for c in self.channel_data:
            if c['channel_name'] == data_session + '-bmm':
                self.non_chat_channel = c['channel_id']
                self._post_allowed = True
        if self.non_chat_channel == '---':
            self._post_allowed = False
        
    def random_flag(self):
        '''Return a random flag emoji, which is sometimes useful for debugging.'''
        countries = ('ad', 'ae', 'af', 'ag', 'ai', 'al', 'am', 'ao', 'aq', 'ar', 'as', 'at', 'au', 'aw',
                     'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bl', 'bm', 'bn',
                     'bo', 'bq', 'br', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cc', 'cd', 'cf', 'cg',
                     'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'cr', 'cu', 'cv', 'cw', 'cx', 'cy', 'cz',
                     'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'ee', 'eg', 'eh', 'er', 'es', 'et', 'fi',
                     'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 'gh', 'gi', 'gl',
                     'gm', 'gn', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr',
                     'ht', 'hu', 'id', 'ie', 'il', 'im', 'in', 'io', 'iq', 'ir', 'is', 'it', 'je', 'jm',
                     'jo', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz', 'la',
                     'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me',
                     'mf', 'mg', 'mh', 'mk', 'ml', 'mm', 'mn', 'mo', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu',
                     'mv', 'mw', 'mx', 'my', 'mz', 'na', 'nc', 'ne', 'nf', 'ng', 'ni', 'nl', 'no', 'np',
                     'nr', 'nu', 'nz', 'om', 'pa', 'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr',
                     'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd',
                     'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'ss', 'st', 'sv',
                     'sx', 'sy', 'sz', 'tc', 'td', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to',
                     'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'um', 'us', 'uy', 'uz', 'va', 'vc', 've',
                     'vg', 'vi', 'vn', 'vu', 'wf', 'ws', 'ye', 'yt', 'za', 'zm', 'zw')
        return(f':flag-{random.choice(countries)}:')
