from dateutil import parser
import datetime
import ACI_Analytics

analytics_on = [7,14,30,60,90,'all']

analytics_start_date = '2020-02-27'
analytics_end_date = datetime.datetime.today().strftime("%Y-%m-%d")
analytics_end_datetime = datetime.datetime.today()

for delta in analytics_on:
    if delta == 'all':
        ACI_Analytics.main(analytics_start_date,analytics_end_date,force_overwrite=True)
    else:
        analytics_start_date = (analytics_end_datetime - datetime.timedelta(days=delta-1)).strftime("%Y-%m-%d")
        ACI_Analytics.main(analytics_start_date,analytics_end_date,force_overwrite=True)
        