import logging
from datetime import datetime

from tweetscrape.tweets_scrape import TweetScrapper

logger = logging.getLogger(__name__)


class TweetScrapperSearch(TweetScrapper):
    """
    Search syntax for query, each filter is white space separated
    eg: Election India NDA "BJP" 2019 OR 2018 -Asia #India OR #BJP from:narendramodi to:NITIAayog @NDTV since:2017-08-01 until:2019-06-15

    1) All of these words: each white space separated
    2) This exact phrase: `""` term in quotation marks
    3) Any of these words: `OR` operator separated, each operator separated
    4) None of these words: `-` operator as prefix to the term, each white space separated
    5) These hash-tags: `#` operator as prefix to the term, each `OR` separated
    6) From these accounts: `from:` as prefix to the term, each `OR` separated
    7) To these accounts: `to:` as prefix to the term, each `OR` separated
    8) Mentioning these accounts: `@` as prefix to the term, each `OR` separated
    9) Near this place: `near:` as prefix to the term and `""` term in quotation marks
                        and `within:` as range with `mi` as suffix miles
    10) From this date: `since:` as prefix to from date and `until:` as prefix to till date. Date format as `YYYY-MM-DD`

    Can specify language. Use language codes. eg. English - `en`

    """

    search_term = None
    search_type = None
    pages = None

    __twitter_search_url__ = None
    __twitter_search_header__ = None
    __twitter_search_params__ = None

    def __init__(self,
                 search_all="", search_exact="", search_any="", search_excludes="", search_hashtags="",
                 search_from_accounts="", search_to_accounts="", search_mentions="",
                 search_near_place="", search_near_distance="",
                 search_from_date="", search_till_date="",
                 pages=2, language=''):

        self.search_type = "typd"
        self.pages = pages

        constructed_search_query = self.construct_query(search_all, search_exact, search_any,
                                                        search_excludes, search_hashtags,
                                                        search_from_accounts, search_to_accounts, search_mentions,
                                                        search_near_place, search_near_distance,
                                                        search_from_date, search_till_date)

        self.search_term = constructed_search_query
        # self.search_term = parse.quote(constructed_search_query)

        # if search_all.startswith("#"):
        #     self.search_type = "hash"
        # else:
        #     self.search_type = "typd"

        # if pages > 25:
        #     self.pages = 25
        # else:
        #     self.pages = pages

        self.__twitter_search_url__ = 'https://twitter.com/i/search/timeline'

        self.__twitter_search_params__ = {
            'vertical': 'default',
            'src': self.search_type,
            'q': self.search_term,
            'l': language,
            'include_available_features': 1,
            'include_entities': 1,
            'include_new_items_bar': 'true'
        }

        self.__twitter_search_header__ = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.8',
            'referer': 'https://twitter.com/search?q={search_term}&src={search_type}'
                .format(search_term=self.search_term, search_type=self.search_type),
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/60.0.3112.78 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'x-twitter-active-user': 'yes'
        }

        super().__init__(twitter_request_url=self.__twitter_search_url__,
                         twitter_request_header=self.__twitter_search_header__,
                         twitter_request_params=self.__twitter_search_params__)

    def get_search_tweets(self, save_output=False):
        output_file_name = '/' + self.search_term + '_search'
        return self.execute_twitter_request(search_term=self.search_term, pages=self.pages,
                                            log_output=save_output, output_file=output_file_name)

    @staticmethod
    def construct_query(search_all, search_exact, search_any, search_excludes, search_hashtags,
                        search_from_accounts, search_to_accounts, search_mentions, search_near_place,
                        search_near_distance, search_from_date, search_till_date):

        search_query_filters = []

        if search_all is not None and search_all != "":
            search_query_filters.append(search_all)

        if search_exact is not None and search_exact != "":
            search_exact = "\"" + search_exact + "\""
            search_query_filters.append(search_exact)

        if search_any is not None and search_any != "" and " " in search_any:
            search_any = " OR ".join(search_any.split())
            search_query_filters.append(search_any)

        if search_excludes is not None and search_excludes != "":
            search_excludes = " -".join(search_excludes.split())
            search_excludes = " -" + search_excludes
            search_query_filters.append(search_excludes)

        if search_hashtags is not None and search_hashtags != "":
            search_hashtags = prefix_operator(search_hashtags, "#")
            search_query_filters.append(search_hashtags)

        if search_from_accounts is not None and search_from_accounts != "":
            search_from_accounts = prefix_operator(search_from_accounts, "from:")
            search_query_filters.append(search_from_accounts)

        if search_to_accounts is not None and search_to_accounts != "":
            search_to_accounts = prefix_operator(search_to_accounts, "to:")
            search_query_filters.append(search_to_accounts)

        if search_mentions is not None and search_mentions != "":
            search_mentions = prefix_operator(search_mentions, "@")
            search_query_filters.append(search_mentions)

        if search_near_place is not None and search_near_place != "":
            search_near_place = "near:" + search_near_place

            if search_near_distance is not None and search_near_distance != "":
                search_near_distance = "within:" + search_near_distance
            else:
                search_near_distance = "within:15mi"

            search_query_filters.append(search_near_place)
            search_query_filters.append(search_near_distance)

        if search_from_date is not None and search_from_date != "" and valid_date_format(search_from_date):
            search_from_date = "since:" + search_from_date

            if search_till_date is not None and search_till_date != "" and valid_date_format(search_from_date):
                search_till_date = "untill:" + search_till_date
            else:
                search_till_date = datetime.strftime(datetime.now(), "%Y-%m-%d")

            search_query_filters.append(search_from_date)
            search_query_filters.append(search_till_date)

        search_query = ' '.join(search_query_filters)

        logger.info("Search:|{0}|".format(search_query))

        return search_query


def prefix_operator(query_str, prefix_op):
    query_list = query_str.split()
    for i, tag in enumerate(query_list):
        if tag[0] != prefix_op:
            query_list[i] = prefix_op + tag

    return " OR ".join(query_list.split())


def valid_date_format(date_str, date_format='%Y-%m-%d'):
    try:
        datetime.strptime(date_str, date_format)
    except ValueError:
        logger.warning("Incorrect data format, should be YYYY-MM-DD")
        return False
    return True


if __name__ == '__main__':

    # avengers%20infinity%20war%20%22avengers%22%20-asia%20%23avengers%20from%3Amarvel%20since%3A2019-06-01
    # avengers infinity war "avengers" -asia #avengers from:marvel since:2019-06-01

    logging.basicConfig(level=logging.DEBUG)

    ts = TweetScrapperSearch(search_all="avengers infinity war")
    # ts = TweetScrapperSearch(search_hashtags="FakeNews Trump", pages=1)
    #
    # # avengers endgame spiderman OR ironman -spoilers
    # ts = TweetScrapperSearch(search_all="avengers endgame",
    #                          search_any="spiderman ironman",
    #                          search_excludes="spoilers", pages=2)
    #
    # ts = TweetScrapperSearch(search_all="avengers marvel",
    #                          search_hashtags="avengers",
    #                          search_from_accounts="marvel ",
    #                          pages=2)
    #
    # ts = TweetScrapperSearch(search_all="raptors",
    #                          search_from_date="2019-03-01", search_till_date="2019-06-01",
    #                          pages=1)
    #
    # ts = TweetScrapperSearch(search_hashtags="raptors", search_near_place="toronto", pages=1)

    l_extracted_tweets = ts.get_search_tweets(True)
    for l_tweet in l_extracted_tweets:
        print(str(l_tweet))
    print(len(l_extracted_tweets))
