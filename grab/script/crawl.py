import logging
import os

from grab.util.config import build_spider_config, build_global_config
from grab.util.module import load_spider_class
from grab.tools.logs import default_logging

logger = logging.getLogger('grab.script.crawl')

def setup_arg_parser(parser):
    parser.add_argument('-t', '--thread-number', help='Number of network threads',
                        default=None, type=int)
    parser.add_argument('--slave', action='store_true', default=False)
    parser.add_argument('--force-url', type=str)
    parser.add_argument('spider_name', type=str)


def main(spider_name, thread_number=None, slave=False, force_url=None,
         settings='settings', *args, **kwargs):
    default_logging()
    config = build_global_config(settings)
    spider_class = load_spider_class(config, spider_name)
    spider_config = build_spider_config(spider_name, config)

    if thread_number is None:
        thread_number = spider_config.getint('THREAD_NUMBER')

    bot = spider_class(
        thread_number=thread_number,
        slave=slave,
        config=spider_config,
        network_try_limit=spider_config.getint('NETWORK_TRY_LIMIT'),
        task_try_limit=spider_config.getint('TASK_TRY_LIMIT'),
    )
    if spider_config.get('QUEUE'):
        bot.setup_queue(**spider_config['QUEUE'])
    if spider_config.get('CACHE'):
        bot.setup_cache(**spider_config['CACHE'])
    if spider_config.get('PROXY_LIST'):
        bot.load_proxylist(**spider_config['PROXY_LIST'])
    try:
        bot.run()
    except KeyboardInterrupt:
        pass

    stats = bot.render_stats()
    logger.debug(stats)

    pid = os.getpid()
    logger.debug('Spider pid is %d' % pid)

    if config.get('SAVE_FATAL_ERRORS'):
        bot.save_list('fatal', 'var/fatal-%d.txt' % pid)

    if config.get('SAVE_TASK_ADD_ERRORS'):
        bot.save_list('task-could-not-be-added', 'var/task-add-error-%d.txt' % pid)

    if config.get('SAVE_FINAL_STATS'):
        open('var/stats-%d.txt' % pid, 'wb').write(stats)
