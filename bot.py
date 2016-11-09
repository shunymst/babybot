import json
import os
from logging import DEBUG, StreamHandler, getLogger

import requests

import doco.client
import falcon

# logger
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)

# ENDPOINT_URI = 'https://trialbot-api.line.me/v1/events'
ENDPOINT_URI = 'https://api.line.me/v2/bot/message/reply'
DOCOMO_API_KEY = os.environ.get('DOCOMO_API_KEY', '')


class CallbackResource(object):
    # line
    header = {
        'Content-Type': 'application/json; charset=UTF-8',
#        'X-Line-ChannelID': os.environ['LINE_CHANNEL_ID'],
#        'X-Line-ChannelSecret': os.environ['LINE_CHANNEL_SECRET'],
#        'X-Line-Trusted-User-With-ACL': os.environ['LINE_CHANNEL_MID'],
        'Authorization': 'Bearer {}'.format(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
    }

    # docomo baby
    user = {'t': 30}
    docomo_client = doco.client.Client(apikey=DOCOMO_API_KEY, user=user)


def on_post(self, req, resp):
    body = req.stream.read()
    if not body:
        raise falcon.HTTPBadRequest('Empty request body',
                                    'A valid JSON document is required.')

    receive_params = json.loads(body.decode('utf-8'))
    logger.debug('receive_params: {}'.format(receive_params))

    for event in receive_params['events']:

        logger.debug('event: {}'.format(event))

        if event['type'] == 'message':
            try:
                user_utt = event['message']['text']
                docomo_res = self.docomo_client.send(
                    utt=user_utt, apiname='Dialogue')

            except Exception:
                raise falcon.HTTPError(falcon.HTTP_503,
                                       'Docomo API Error. ',
                                       'Could not invoke docomo api.')

            logger.debug('docomo_res: {}'.format(docomo_res))
            sys_utt = docomo_res['utt']

            send_content = {
                'replyToken': event['replyToken'],
                'messages': [
                    {
                        'type': 'text',
                        'text': sys_utt
                    }

                ]
            }
            send_content = json.dumps(send_content)
            logger.debug('send_content: {}'.format(send_content))

            res = requests.post(ENDPOINT_URI, data=send_content, headers=self.header)
            logger.debug('res: {} {}'.format(res.status_code, res.reason))

            resp.body = json.dumps('OK')

api = falcon.API()
api.add_route('/callback', CallbackResource())
