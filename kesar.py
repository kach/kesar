'''
KESAR: Kartik's Experiment Server for { Accelerating Research
                                      | Aggregating Responses
                                      | Asking Riddles
                                      | Analyzing Rationality
                                      }
'''

import os, sys, time, threading
import http.server, socketserver, uuid
from urllib.parse import urlparse, parse_qs
from functools import partial


class tag:
    def __init__(self, __name, **prop):
        self.name = __name
        self.prop = prop

    def __str__(self):
        return self()

    def __call__(self, *children):
        def render_kv(k, v):
            if v is True:
                return f'{k.strip("_")}'
            return f'{k.strip("_")}="{v}"'

        if len(children) == 0:
            return f'''<{self.name}{''.join([f' {render_kv(k, v)}' for k, v in self.prop.items() if v is not None and v is not False])}/>'''
        return f'''<{self.name}{''.join([f' {render_kv(k, v)}' for k, v in self.prop.items() if v is not None and v is not False])}>{' '.join(str(c) for c in children)}</{self.name}>'''


# Install 'tag' shortcuts globally, e.g. h1_() for <h1>
elements = ['<a>', '<abbr>', '<acronym>', '<address>', '<applet>', '<area>', '<article>', '<aside>', '<audio>', '<b>', '<base>', '<basefont>', '<bdi>', '<bdo>', '<bgsound>', '<big>', '<blink>', '<blockquote>', '<body>', '<br>', '<button>', '<canvas>', '<caption>', '<center>', '<cite>', '<code>', '<col>', '<colgroup>', '<content>', '<data>', '<datalist>', '<dd>', '<del>', '<details>', '<dfn>', '<dialog>', '<dir>', '<div>', '<dl>', '<dt>', '<em>', '<embed>', '<fieldset>', '<figcaption>', '<figure>', '<font>', '<footer>', '<form>', '<frame>', '<frameset>', '<h1>', '<h2>', '<h3>', '<h4>', '<h5>', '<h6>', '<head>', '<header>', '<hgroup>', '<hr>', '<html>', '<i>', '<iframe>', '<img>', '<input>', '<ins>', '<kbd>', '<keygen>', '<label>', '<legend>', '<li>', '<link>', '<main>', '<map>', '<mark>', '<marquee>', '<menu>', '<menuitem>', '<meta>', '<meter>', '<nav>', '<nobr>', '<noframes>', '<noscript>', '<object>', '<ol>', '<optgroup>', '<option>', '<output>', '<p>', '<param>', '<picture>', '<plaintext>', '<pre>', '<progress>', '<q>', '<rp>', '<rt>', '<rtc>', '<ruby>', '<s>', '<samp>', '<script>', '<section>', '<select>', '<shadow>', '<slot>', '<small>', '<source>', '<spacer>', '<span>', '<strike>', '<strong>', '<style>', '<sub>', '<summary>', '<sup>', '<table>', '<tbody>', '<td>', '<template>', '<textarea>', '<tfoot>', '<th>', '<thead>', '<time>', '<title>', '<tr>', '<track>', '<tt>', '<u>', '<ul>', '<var>', '<video>', '<wbr>', '<xmp>']
for e in elements:
    globals()[e[1:-1] + '_'] = partial(tag, e[1:-1])


def page(uid, *contents, **kwargs):
    if uid is None:
        return '<!DOCTYPE html>' + html_()(
            meta_(charset="utf-8"),
            meta_(name="viewport", content="width=device-width, initial-scale=1.0"),
            link_(rel='stylesheet', type_='text/css', href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css"),
            form_(action='', method='POST')(
                *contents
            )
        )

    return '<!DOCTYPE html>' + html_()(
        meta_(charset="utf-8"),
        meta_(name="viewport", content="width=device-width, initial-scale=1.0"),
        link_(rel='stylesheet', type_='text/css', href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css"),
        form_(action='', method='POST')(
            *contents,
            input_(type_='hidden', name='uid', value=uid),
            input_(id_='submit', type_='submit', value='Next', disabled="true" if 'disable_submit' in kwargs else None),
            p_()(em_()('Note: do not press the "back" button during this study.'))
        ),
        script_()('''
            var SUBMITTING = false;
            document.querySelector('form').addEventListener('submit', function() {
                SUBMITTING = true; 
            })
            window.addEventListener('beforeunload', function(e) {
                if (SUBMITTING) return;
                e.preventDefault();
                return e.returnValue = "Are you sure you want to exit? Doing so will invalidate your response to this study.";
            });

            // Sorry!
            history.pushState(null, null, document.URL);
            window.addEventListener('popstate', function () {
                history.pushState(null, null, document.URL);
            });
        ''')
    )

def text_input_(name='response', text='', required=True):
    return span_()(
        label_(for_=name)(text),
        input_(type_='text', id_=name, name=name, required=required)
    )

def check_input_(name, text, required=True):
    return span_()(
        label_(for_=name)(text),
        input_(type_='checkbox', id_=name, name=name, required=required)
    )


def kesar(script, port=8080, watch=True, logfile='log.db'):
    print(f'** Hello! I am Kesar and the time is {time.ctime()}.')
    sessions = {}

    class Experiment(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/':
                return super().do_GET()

            uid = uuid.uuid4().hex
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            sessions[uid] = script()
            next_form = page(uid, next(sessions[uid]))
            self.wfile.write(next_form.encode('utf-8'))

        def do_POST(self):
            length = int(self.headers['Content-length'])
            field_data = self.rfile.read(length)
            fields = parse_qs(urlparse(field_data).path.decode('utf-8'))
            uid = fields['uid'][0]

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                next_form = page(uid, sessions[uid].send(fields))
            except StopIteration as e:  # script completed
                if type(e.value) == tuple and len(e.value) == 2:
                    data, bye = e.value
                else:
                    data, bye = e.value, 'You have completed the experiment and can safely close this window.'
                next_form = page(None, bye)

                # Save data, thread-safe
                import fcntl, json
                with open(logfile, 'a') as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    f.write(json.dumps(data) + '\n')
                    f.flush()
                    fcntl.flock(f, fcntl.LOCK_UN)
            self.wfile.write(next_form.encode('utf-8'))


    def refresh_daemon():
        init_file = sys.argv[0]
        init_mtime = os.path.getmtime(init_file)
        print(f'** I am watching {init_file} for changes, and will reboot if it is changed.')
        print(f'   [warning: when I restart, I will cancel in-progress trials]')

        while True:
            time.sleep(1)
            current_mtime = os.path.getmtime(init_file)
            if current_mtime > init_mtime:
                print(f'''** I am refreshing the server by running $ python {' '.join(sys.argv)}.''')
                print()
                os.execvp('python', ['python'] + sys.argv)

    if watch:
        threading.Thread(target=refresh_daemon, daemon=True).start()

    import socket
    ip = socket.gethostbyname(socket.gethostname())
    print(f'** I am launching the server at http://{ip}:{port} - press CTRL-C to stop the server.')
    print(f'** I am logging responses to file {logfile}')
    with http.server.ThreadingHTTPServer(("", port), Experiment) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
