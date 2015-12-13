import kdapi
import praw
import OAuth2Util
import os
import argparse
import operator
import json
import time
import numpy as np
from datetime import datetime
from collections import defaultdict, OrderedDict

def getReposts(url):
  """Given a reddit url, use kdapi to get any reposts.
  Returns a list of repostDict's
  """

  repostList = []
  reposts = kdapi.check(url)
  reposts.sort(key=operator.attrgetter('score'), reverse=True)
  for item in reposts:
    repostDict = {}
    repostDict['link'] = item.link
    repostDict['score'] = item.score
    repostDict['similarity'] = item.similarity
    if item.subreddit:
      repostDict['subreddit'] = item.subreddit[3:]
    else:
      repostDict['subreddit'] = None
      
    repostList.append(repostDict)
  
  return repostList

def pickRepost(r, reposts, similarityTolerance, subredditStats):
  """r:reddit object
  reposts: list from getReposts
  similarityTolerance: The minumum repost similarity percent usable from karma decay
  subredditStats: stats returned by getSubredditsTopStats
  Used to pick a repost that will be used to try and find a comment.
  This logic has been removed so people are not running the same bot. Want to know more? We can chat about it!
  """
  return None, False

def getTopLevelComments(r, link):
  """returns a list of top level comments from a reddit link"""
  #Changes link to https, not http. Per reddits new oauth rules
  if link[4] != 's':
    link = 'https' + link[4:]
  
  comments = []
  submission = r.get_submission(link)
  topLevelComments = submission.comments
  for comment in topLevelComments:
    try:
      commentInfo = (comment.score, comment.gilded, comment.body)
      comments.append(commentInfo)
    except:
      pass
    
  return comments

def pickRepostComment(repostComments):
  """Given a list of repost comments, pick the comment to repost based on certain criteria
  This logic has been removed so people are not running the same bot. Want to know more? We can chat about it!
  """ 
  return None
  
def getPostsByType(sub, postType):
  """Given a sub reddit, and post type. Return 1 page of posts"""
  if postType == 'hot':
    return sub.get_hot()
  elif postType == 'top':
    return sub.get_top()
  elif postType == 'new':
    return sub.get_new()
  elif postType == 'rising':
    return sub.get_rising()
  else:
    return "You know that doesnt exist, now deal with this unexpect return" #Bad code should come back but probably wont

def getSubredditsTopStats(r, subreddits):
  """For each subreddit in subreddits, calculate some statistics about the top all time posts
  These statistics are used in picking comments
  returns a dictionary of dicts. Keyed on subreddit name
  """

  subredditStats = defaultdict(dict)
  
  for subreddit in subreddits:
    scores = []
    sub = r.get_subreddit(subreddit)
    for submission in sub.get_top_from_all(limit=300):
      scores.append(submission.score)
    
    subredditStats[subreddit]['mean'] = np.nanmean(scores)
    subredditStats[subreddit]['std'] = np.nanstd(scores)
    subredditStats[subreddit]['min'] = np.nanmin(scores)
    subredditStats[subreddit]['max'] = np.nanmax(scores)
    subredditStats[subreddit]['updated'] = str(datetime.now())

  return subredditStats

def crawlPosts(r, postType, subreddits):
  """Crawls the posts in a giving postType. Finding reposts, skiping ones already looked at (decayed).
  If a suitable repost, and comment are found. Post the old comment onto the new repost.
  Printing out info about every repost found, and the Totals after all the posts are crawled.
  If it has posted a certain amount of posts in a given time, it will wait two minutes.
  """
  print 'Crawling posts...'
  
  print len(subreddits), ' total subreddits'

  print 'Loading decayed.json...'
  decayed = []
  if os.path.exists(r'./decayed.json'):
    with open('./decayed.json', 'r') as decayFile:
      decayed = json.load(decayFile)
  print len(decayed), 'posts decayed'
  
  print 'Loading subreddit stats'
  subredditStats = defaultdict(dict)
  if os.path.exists(r'./subredditStats.json'):
    with open('./subredditStats.json', 'r') as subredditStatsFile:
      subredditStats = json.load(subredditStatsFile)
  print len(subredditStats.keys()), 'subreddit stats loaded'
    
  print 'Starting subreddit loop...'
  
  for subreddit in subreddits:
    print 'Starting', subreddit, postType
    sub = r.get_subreddit(subreddit)
    postCounter = 0
    postLimitCounter = 0
    newPostTotal = 0
    repostTotal = 0
    decayedPostTotal = 0
    for submission in getPostsByType(sub, postType):
      if submission.id in decayed:
        print 'Decayed post found'
        decayedPostTotal += 1
        next
      else:
        reposts = getReposts(submission.url)
        repost, useRepost = pickRepost(r, reposts, 95, subredditStats)
        if repost:
          repostTotal += 1
          print '!'*100
          print 'REPOST FOUND'
          print 'Repost link:', repost['link']
          print 'Repost score:', repost['score']
          print 'Repost similarity:', repost['similarity']
          print 'Repost subreddit:', repost['subreddit']
          print 'Repost submission url:', submission.url
          if useRepost:
            repostComments = getTopLevelComments(r, repost['link'])
            topRepostComment = pickRepostComment(repostComments)
            if topRepostComment:
              if topRepostComment.lower() != '[deleted]':
                print 'Top comment:', topRepostComment
                print 'Adding top comment found...'
                submission.upvote()
                submission.add_comment(topRepostComment)
                postCounter += 1
                postLimitCounter += 1
              if postCounter > 2:
                print datetime.now(), 'Waiting two minutes...'
                time.sleep(120)
                postLimitCounter = 0
          print '!'*100
        else:
          print 'New post found'
          newPostTotal += 1
        
        decayed.append(submission.id)
        
        with open('./decayed.json', 'w') as decayFile:
          decayFile.write(json.dumps(decayed))
    print '~'*100
    print 'Finsihed', subreddit,postType
    print 'Total comments posted:', postCounter
    print 'Total reposts found:', repostTotal
    print 'Total new posts found:', newPostTotal
    print 'Total decayed posts found:', decayedPostTotal
    print '~'*100
  
  print 'Finished subreddit loop'

def main ():

  parser = argparse.ArgumentParser(description='Start the bot')
  parser.add_argument('--username', required=True, help='Bot username')
  parser.add_argument('--password', required=True, help='Bot password')
  parser.add_argument('--subreddits', default=r'./subreddits.json', help='filePath to json file containing list of subreddits to crawl')

  args = parser.parse_args()
  username = args.username
  password = args.password
  subredditJsonPath = args.subreddits
  subreddits = []

  print 'Getting list of subreddits from json'
  if not os.path.exists(subredditJsonPath):
    print 'Subreddit list json not found'
    return -1
  else:
    with open(subredditJsonPath, 'r') as subredditJson:
      subreddits = json.load(subredditJson)
    
  print 'Logging in...'
  user_agent = ("CHANGE ME")
  r = praw.Reddit(user_agent = user_agent)
  o = OAuth2Util.OAuth2Util(r)
  o.refresh(force=True)
    
  startTime = datetime.now()
  print 'Starting at', startTime

  print 'Starting rising...'
  crawlPosts(r, 'rising', subreddits)
  print 'Finished rising'
  print 'Starting new...'
  crawlPosts(r, 'new', subreddits)
  print 'Finished new'
  print 'Starting hot...'
  crawlPosts(r, 'hot', subreddits)
  print 'Finished hot'
  
  print 'Finish time:', datetime.now()
  print 'Run time:', (datetime.now() - startTime)

if __name__ == '__main__':
    main()