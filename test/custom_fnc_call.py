import sys
import os
sys.path.append(os.path.abspath(".."))

from helpers import _generate_jql_from_input

import time
import json

# Assuming this is defined somewhere
# from your_module import build_jql_constraints_from_input

# user_inputs = [
#     "Get all open tickets from UCB Italy and SLSP, sorted by priority, top 5 only",
#     "Show me 20 issues from UniCredit and CAF updated last month",
#     "I need all unresolved tasks in BAWAG, CSAS, and UniCredit, limit to 15",
#     "Give me top 10 tickets for UCB Italy that were closed in the last week",
#     "Fetch critical issues from SLSP and BAWAG, no more than 7 tickets",
#     "Find all tasks from CAF, up to 30",
#     "Tickets from CSAS and SLSP between Jan and now — only the top 3",
#     "Get me the 25 most recent tickets for UniCredit and CAF",
#     "UCB Italy and UniCredit — I want 12 tickets from the last 10 days",
#     "Requesting all priority tickets from BAWAG and CSAS, max 50"
# ]

# for input in user_inputs :
    

#     print("INPUT: ", input)

#     jql = generate_jql_from_input(
#         user_input=input,
#         allowed_projects=get_all_jira_projects(),
#         allowed_priorities=get_all_jira_priorities()
#     )

#     print ("JQL: ", jql)


print(_generate_jql_from_input(
        user_input="Oall open tickets for Bawag app support project"
    ))