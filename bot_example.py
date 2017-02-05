import os
import time
from slackclient import SlackClient
import collections
from io import StringIO


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("SLACKBOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
CHANNEL_BUFFER = collections.defaultdict(lambda: collections.deque([], 5))
VIEW_BUFFER_COMMAND = 'show buffer'

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACKBOT_TOKEN'))


def handle_command(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    if user != BOT_ID:
        response = "Not sure what you mean. Use the *" + VIEW_BUFFER_COMMAND + \
                   "* command to view my buffer for this conversation"
        if command.startswith(VIEW_BUFFER_COMMAND):
            s = StringIO()
            this_channel_buffer = CHANNEL_BUFFER[channel]
            for user, message in this_channel_buffer:
                s.write("User {} said '{}'\n".format(user, message))
            response = s.getvalue()
        slack_client.api_call("chat.postMessage", channel=channel,
                              text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            # Update the buffer
            if output and 'type' in output and 'user' in output and output['type'] == 'message':
                ch_id = output['channel']
                user_id = output['user']
                text = output['text']
                if user_id != BOT_ID:
                    CHANNEL_BUFFER[ch_id].append((user_id, text))
                if AT_BOT in text:
                    # return text after the @ mention, whitespace removed
                    return text.split(AT_BOT)[1].strip().lower(), \
                           ch_id, user_id
    return None, None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            data = slack_client.rtm_read()
            print(slack_client.api_call(
                'channels.history',
                channel='C414EMFRQ'
            ))
            print(data)
            command, channel, user = parse_slack_output(data)
            if command and channel and user:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
