from aiohttp import web
import aiofiles
import datetime as dt
import asyncio


INTERVAL_SECS = 1
CHUNK_SIZE = 100
KILOBYTE = 1024
READ_SIZE = CHUNK_SIZE * KILOBYTE # 100 KB



async def uptime_handle(request):

    response = web.StreamResponse()

    response.headers['Content-Type'] = 'text/html'

    await response.prepare(request)

    while True:
        formatted_date = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f'{formatted_date}<br>'

        await response.write(message.encode('utf-8'))

        await asyncio.sleep(INTERVAL_SECS)

async def archivate(request):
    path = request.match_info['archive_hash']
    args = ['-r', '-', '.', '-i', '*']
    proc = await asyncio.create_subprocess_exec(
            'zip', *args, cwd=f'test_photos/{path}',
            stdout=asyncio.subprocess.PIPE
    )
    cursor = 0
    full_arch = b''
    while True:
        if not proc.stdout.at_eof():
            data = await proc.stdout.read(n=READ_SIZE)
        else:
            break
        full_arch += data
        data_length = len(data)

#    with open('smtharch.zip', 'w+b') as f1:
#        f1.seek(cursor)
#        f1.write(full_arch)
    response = web.StreamResponse()
#    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename="{path}.zip"'
    await response.prepare(request)
    await response.write(full_arch)

#    raise NotImplementedError


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
#        web.get('/', uptime_handle),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
