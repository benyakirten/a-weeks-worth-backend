from functools import cmp_to_key

def compare(meal1, meal2):
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    times = ['B', 'L', 'D', 'O']
    if meal1['day'] == meal2['day']:
        if meal1['time'] == meal2['time']:
            return 0
        if meal1['time'] == 'B':
            return -1
        if meal1['time'] == 'L' and meal2['time'] not in times[:1]:
            return -1
        if meal1['time'] == 'D' and meal2['time'] not in times[:2]:
            return -1
        return 1
    if meal1['day'] == 'MON':
        return -1
    if meal1['day'] == 'TUE' and meal2['day'] not in days[:1]:
        return -1
    if meal1['day'] == 'WED' and meal2['day'] not in days[:2]:
        return -1
    if meal1['day'] == 'THU' and meal2['day'] not in days[:3]:
        return -1
    if meal1['day'] == 'FRI' and meal2['day'] not in days[:4]:
        return -1
    if meal1['day'] == 'SAT' and meal2['day'] not in days[:5]:
        return -1
    return 1

compare_as_key = cmp_to_key(compare)