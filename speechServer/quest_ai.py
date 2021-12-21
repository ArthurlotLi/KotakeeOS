#
# quest_ai
#
# RoBERTa-powered Natural Language Processing introductory project. 
# Given a yes/no question, use various internet sources for context
# before using RoBERTa to derive a boolean response. 
#
# Designed to be utilized alongside KotakeeOS speechServer to allow
# users to ask their home assistant yes/no questions in conjunction
# with the Trigger Word Detection machine learning solution. Should
# be a pretty fun little project to introduce me to NLP. 
#
# Additonal enhancements TODO:
#  - Learn to tune the RoBERTa model yourself
#  - Implement automated dataset additions/separate personal dataset
#    source
#
# Base code from here:
# https://towardsdatascience.com/building-an-ai-8-ball-with-roberta-2bfbf6f5519b 
#

class QuestAi:

  # Given a question, process an answer!
  def generate_response(self, question_text):
    return True, 100.00