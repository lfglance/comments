from os import getenv


# allows web moderation
ADMIN_TOKEN = getenv('ADMIN_TOKEN', 'abcdef')
# if new comments are denied by default
AUTO_APPROVE = getenv('AUTO_APPROVE', True)
# domains which are allowed to post comments
ACCEPT_DOMAINS = ['127.0.0.1']