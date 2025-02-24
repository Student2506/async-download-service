import argparse
import asyncio
import logging
import os
from pathlib import Path

import aiofiles
from aiohttp import web

INTERVAL_SECS = 1
CHUNK_SIZE = 100
KILOBYTE = 1024
READ_SIZE = CHUNK_SIZE * KILOBYTE  # 100 KB

format = '%(asctime)s, %(levelname)s, %(message)s, %(name)s'

log_levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
        '': logging.NOTSET
}

parser = argparse.ArgumentParser(
        description='Serve files from folders as zip archive'
)
parser.add_argument(
        '--loglevel', default='', choices=log_levels, type=str.lower
)
parser.add_argument('--delay', default=1, type=int)
parser.add_argument('--path', default='test_photos')
main_args = parser.parse_args()
logging.basicConfig(level=log_levels[main_args.loglevel], format=format)
log = logging.getLogger(__name__)


async def archivate(request):
    archive_name = request.match_info['archive_hash']
    path = request.app.storage / archive_name
    if '.' in str(path):
        raise web.HTTPNotFound(body='Using dot "." is not allowed')
    if not os.path.exists(path):
        raise web.HTTPNotFound(body='File is deleted or never existed')
    args = ['-r', '-', '.', '-i', '*']
    zip_process = await asyncio.create_subprocess_exec(
            'zip', *args, cwd=path,
            stdout=asyncio.subprocess.PIPE
    )
    response = web.StreamResponse()
    response.headers['Content-Disposition'] = (
            f'attachment; filename="{archive_name}.zip"'
    )
    response.headers['Transfer-Encoding'] = 'deflate; chunked'
    response.headers['Connection'] = 'keep-alive'
    await response.prepare(request)

    try:
        while not zip_process.stdout.at_eof():
            data = await zip_process.stdout.read(n=READ_SIZE)
            await asyncio.sleep(request.app.delay)
            await response.write(data)
            log.info('Sending archive chunk ...')
    except asyncio.CancelledError:
        log.info('User canceled download')
        raise
    except Exception as e:
        log.info('Download was interrupted')
        log.error(str(e))
        raise
    except BaseException as e:
        log.error(str(e))
    finally:
        try:
            zip_process.kill()
            outs, errs = await zip_process.communicate()
        except ProcessLookupError:
            pass
        log.info('Sending End of file')
        try:
            await response.write_eof()
        except ConnectionResetError:
            pass


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.storage = Path(main_args.path)
    app.delay = main_args.delay
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
