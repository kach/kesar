'''
 /)
(/_   _  _   _   __
/(___(/_/_)_(_(_/ (_

kesar: Kartik's Experiment Server for { Accelerating Research
                                      | Aggregating Responses
                                      | Asking Riddles
                                      | Analyzing Rationality
                                      | Accumulating Reward
                                      | Ascertaining Reality
                                      | Assisting RAs
                                      }
'''

import os, sys, time, threading, random, json
import http.server, socket, socketserver, uuid
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs
import functools, itertools

# https://dohliam.github.io/dropin-minimal-css/
CSS_FRAMEWORK_HREF = "https://cdn.jsdelivr.net/npm/water.css@2/out/water.css"
# CSS_FRAMEWORK_HREF = "https://cdn.jsdelivr.net/npm/holiday.css@0.11.2"

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
    globals()[e[1:-1] + '_'] = functools.partial(tag, e[1:-1])


def page(uid, *contents, **kwargs):
    if uid is None:
        return '<!DOCTYPE html>' + html_()(
            meta_(charset="utf-8"),
            meta_(name="viewport", content="width=device-width, initial-scale=1.0"),
            '<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌺</text></svg>">',
            link_(rel='stylesheet', type_='text/css', href=CSS_FRAMEWORK_HREF),
            form_(action='', method='POST', autocomplete="off")(
                *contents
            )
        )

    return '<!DOCTYPE html>' + html_()(
        meta_(charset="utf-8"),
        meta_(name="viewport", content="width=device-width, initial-scale=1.0"),
        '<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🌺</text></svg>">',
        link_(rel='stylesheet', type_='text/css', href=CSS_FRAMEWORK_HREF),
        form_(action='', method='POST', autocomplete="off")(
            *contents,
            input_(type_='hidden', name='uid', value=uid),
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

static_cache = {}
def static_(path):
    mtime = os.path.getmtime(path)
    if path not in static_cache or static_cache[path]['mtime'] != mtime:
        with open(path) as f:
            static_cache[path] = {
                'mtime': mtime,
                'value': f.read()
            }
    return static_cache[path]['value']

def submit_(**kwargs):
    return input_(id_='submit_button', type_='submit', value='Next', **kwargs)

def text_input_(name='response', text='', required=True):
    return span_()(
        label_(for_=name)(text),
        input_(type_='text', id_=name, name=name, required=required)
    )

def check_input_(name, text, required=True):
    return span_()(
        input_(type_='checkbox', id_=name, name=name, required=required),
        label_(for_=name)(text)
    )

def select_input_(name, options_dict, prompt="-- select one --", **kwargs):
    return select_(name=name, **kwargs)(
        option_(value="")(prompt),
        *[option_(value=k)(v) for k, v in options_dict.items()]
    )

def exit_survey_(*qs):
    return div_()(
        h1_()('You are almost done!'),
        p_()("Answer the following questions and press 'next' to finish the study!"),
        *[
            section_()(
                p_()(q),
                textarea_(name=f'Q{i + 1}', required=True)('')
            ) for i, q in enumerate(qs)
        ],
        submit_()
    )

class threadsafe_iterable_:
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return next(self.it)

def stratify_(*items):
    items = list(itertools.product(*items))
    def it():
        while True:
            random.shuffle(items)
            for item in items:
                yield item

    return threadsafe_iterable_(it())

def shuffled(x):
    x_ = list(x)[:]
    random.shuffle(x_)
    return x_

class pair_manager:
    def __init__(self, timeout=60):
        self.timeout = timeout
        self.lock = threading.Lock()
        self.unpaired = []
        self.partners = {}
        self.mailboxs = {}
        self.lastping = {}

    def get_partner(self, name):
        with self.lock:
            self.unpaired.append(name)
            self.lastping[name] = time.time()
            while len(self.unpaired) >= 2:
                a = self.unpaired.pop(0)
                b = self.unpaired.pop(0)
                self.partners[a] = b
                self.partners[b] = a

            if name in self.partners:
                return self.partners[name]
            return False

    def send(self, name, message):
        with self.lock:
            self.lastping[name] = time.time()
            partner = self.partners[name]
            self.mailboxs[partner] = message

    def recv(self, name):
        with self.lock:
            self.lastping[name] = time.time()
            if self.lastping[self.partners[name]] < time.time() - self.timeout:
                raise Exception(f'Partner of {name} has disconnected...')

            if name not in self.mailboxs:
                self.mailboxs[name] = False
            message = self.mailboxs[name]
            self.mailboxs[name] = False
            return message

def pause_(t=10):
    return script_()(f'''
        window.setTimeout(function() {{
            SUBMITTING = true;
            document.getElementsByTagName('form')[0].submit();
        }}, {t * 1000});
    ''')

def kesar(script, port=8080, watch=True, logfile='log.jsonl'):
    print(f'** Hello! I am Kesar and the time is {time.ctime()}.')
    print('   You can learn more about me here: https://github.com/kach/kesar')
    sessions = {}

    logfile_lock = threading.Lock()

    class Experiment(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/':
                # return super().do_GET()
                path = self.translate_path(self.path)
                if path.endswith("/"):
                    self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                    return
                try:
                    f = open(path, 'rb')
                except OSError:
                    self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                    return
                ctype = self.guess_type(path)
                fs = os.fstat(f.fileno())
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Length", str(fs[6]))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()
                return

            uid = uuid.uuid4().hex
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()

            sessions[uid] = script(uid)
            next_form = page(uid, next(sessions[uid]))
            self.wfile.write(next_form.encode('utf-8'))

        def do_POST(self):
            length = int(self.headers['Content-length'])
            field_data = self.rfile.read(length)
            fields = parse_qs(urlparse(field_data).path.decode('utf-8'))
            uid = fields['uid'][0]
            del fields['uid']
            fields['time_'] = time.time()
            print(fields, self.headers['User-Agent'])
            if uid not in sessions:
                print(f'-- Rebooting zombie session {uid}')
                return self.do_GET()

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Expires", "0")
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
                with logfile_lock:
                    with open(logfile, 'a') as f:
                        f.write(json.dumps(data) + '\n')
                        f.flush()
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
                with logfile_lock:
                    os.execvp('python', ['python'] + sys.argv)

    if watch:
        threading.Thread(target=refresh_daemon, daemon=True).start()

    ip = socket.gethostbyname(socket.gethostname())
    print(f'** I am launching the server at http://{ip}:{port} - press CTRL-C to stop me anytime.')
    print(f'** I am logging responses to file {logfile}')
    with http.server.ThreadingHTTPServer(("", port), Experiment) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()
