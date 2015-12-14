

# Reddit-Fake-User-Bot
This is a bot that looks at all the new posts, and checks to see if they are reposts using an api to http://karmadecay.com. I have a certain threshold to determine if the original posts were successful. If they were, I have another threshold to determine if the top comments were successful on the original posts. If both criteria were met, I copy/paste a successful comment and post it on the repost, effectively creating a "fake user". Some people recognize the reposted comments; others respond to them like they are organic. It is very satisfying to see comments being posted that are in the right context, and spur other conversations.

# What is reddit?
https://www.reddit.com/wiki/reddit_101
Basically users submit links to other websites and users can comment and vote on the links. The links are sorted by the votes, comments and time. Reposts happen a lot, and are just the same link being submitted more than once after a period of time.

# Disclaimer
Due to the nature of this bot some of the logic on how I pick the comments to repost has been removed in this repo. This is so people can't run the same bot at the same time.

#Requirements
praw
https://praw.readthedocs.org/en/stable/

praw-OAuth2Util
https://github.com/SmBe19/praw-OAuth2Util

kdapi
https://github.com/ethanhjennings/karmadecay-api/tree/master/kdapi